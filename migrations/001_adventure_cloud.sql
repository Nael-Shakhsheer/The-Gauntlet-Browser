-- Run in your own Supabase SQL editor. No credentials or private saves here.
-- Only the authoritative Python server may call these RPCs.
begin;
create table if not exists public.gauntlet_worlds (
 id uuid primary key, owner_id uuid not null references auth.users(id),
 creator_character uuid not null, revision bigint not null default 1,
 record jsonb not null, saved_at timestamptz not null default now()
);
create table if not exists public.gauntlet_members (
 world_id uuid references public.gauntlet_worlds(id), user_id uuid references auth.users(id),
 character_id uuid not null, primary key(world_id,user_id), unique(world_id,character_id)
);
create table if not exists public.gauntlet_save_receipts (
 world_id uuid references public.gauntlet_worlds(id), request_key text,
 revision bigint not null, saved_at timestamptz not null, primary key(world_id,request_key)
);
alter table public.gauntlet_worlds enable row level security;
alter table public.gauntlet_members enable row level security;
alter table public.gauntlet_save_receipts enable row level security;
revoke all on public.gauntlet_worlds,public.gauntlet_members,public.gauntlet_save_receipts from anon,authenticated;

create or replace function public.gauntlet_claim_world(p_world uuid,p_actor uuid,p_character uuid,p_creator uuid,p_record jsonb)
returns jsonb language plpgsql security definer set search_path=public as $$
declare w gauntlet_worlds; c uuid;
begin
 -- Serialize initial ownership and concurrent guest claims.
 perform pg_advisory_xact_lock(hashtextextended(p_world::text,0));
 select * into w from gauntlet_worlds where id=p_world for update;
 if not found then
   if p_character<>p_creator then raise exception 'CREATOR_REQUIRED'; end if;
   if p_record->>'worldId'<>p_world::text or p_record->>'creatorCharacter'<>p_creator::text then raise exception 'INVALID_IDENTITY'; end if;
   insert into gauntlet_worlds(id,owner_id,creator_character,record) values(p_world,p_actor,p_creator,p_record) returning * into w;
 end if;
 if w.creator_character<>p_creator or not (w.record->'characterIds' @> jsonb_build_array(p_character::text)) then raise exception 'INVALID_CHARACTER'; end if;
 select character_id into c from gauntlet_members where world_id=p_world and user_id=p_actor;
 if found and c<>p_character then raise exception 'ACCOUNT_ALREADY_HAS_CHARACTER'; end if;
 if p_character=w.creator_character and p_actor<>w.owner_id then raise exception 'OWNER_MISMATCH'; end if;
 insert into gauntlet_members values(p_world,p_actor,p_character) on conflict(world_id,user_id) do nothing;
 return jsonb_build_object('revision',w.revision,'savedAt',w.saved_at,'owner',w.owner_id=p_actor);
end $$;

create or replace function public.gauntlet_save_world(p_world uuid,p_actor uuid,p_character uuid,p_expected bigint,p_request text,p_record jsonb)
returns jsonb language plpgsql security definer set search_path=public as $$
declare w gauntlet_worlds; r gauntlet_save_receipts;
begin
 select * into w from gauntlet_worlds where id=p_world for update;
 if not found or not exists(select 1 from gauntlet_members where world_id=p_world and user_id=p_actor and character_id=p_character) then raise exception 'MEMBERSHIP_REQUIRED'; end if;
 select * into r from gauntlet_save_receipts where world_id=p_world and request_key=p_request;
 if found then return jsonb_build_object('revision',r.revision,'savedAt',r.saved_at); end if;
 if w.revision<>p_expected then raise exception 'REVISION_CONFLICT'; end if;
 if p_record->>'worldId'<>p_world::text or p_record->>'creatorCharacter'<>w.creator_character::text or p_record->'characterIds'<>w.record->'characterIds' then raise exception 'IMMUTABLE_IDENTITY'; end if;
 update gauntlet_worlds set record=p_record,revision=revision+1,saved_at=now() where id=p_world returning * into w;
 insert into gauntlet_save_receipts values(p_world,p_request,w.revision,w.saved_at);
 return jsonb_build_object('revision',w.revision,'savedAt',w.saved_at);
end $$;

create or replace function public.gauntlet_list_worlds(p_actor uuid) returns jsonb
language sql security definer set search_path=public as $$
 select coalesce(jsonb_agg(jsonb_build_object('worldId',w.id,'name',w.record->'backup'->>'name',
 'savedAt',w.saved_at,'revision',w.revision,'owner',w.owner_id=p_actor,
 'hero',c.progress->>'class','items',jsonb_array_length(c.progress->'inventory'),
 'training',coalesce((select sum(value::int) from jsonb_each_text(c.progress->'skillRanks')),0),
 'runes',w.record->'backup'->'progress'->'runes',
 'completed',(select count(*) from jsonb_each_text(w.record->'backup'->'progress'->'world'->'quests') where value='complete'),
 'locations',jsonb_array_length(w.record->'backup'->'progress'->'world'->'visited'),
 'recovery',case when w.record->'backup'->'progress'->'world'->'checkpoint'->>'bed' is null then 'Oakvale gate' else 'Upstairs inn bed' end)), '[]'::jsonb)
 from gauntlet_worlds w join gauntlet_members m on m.world_id=w.id
 cross join lateral (
   select value progress from jsonb_array_elements(w.record->'backup'->'progress'->'characters') with ordinality
   where w.record->'characterIds'->>((ordinality-1)::int)=m.character_id::text
 ) c where m.user_id=p_actor;
$$;

create or replace function public.gauntlet_load_world(p_actor uuid,p_world uuid) returns jsonb
language plpgsql security definer set search_path=public as $$
declare w gauntlet_worlds; c uuid;
begin
 select character_id into c from gauntlet_members where user_id=p_actor and world_id=p_world;
 if not found then raise exception 'MEMBERSHIP_REQUIRED'; end if;
 select * into w from gauntlet_worlds where id=p_world;
 return jsonb_build_object('record',w.record,'character',c,'revision',w.revision,'savedAt',w.saved_at);
end $$;
revoke all on function public.gauntlet_claim_world(uuid,uuid,uuid,uuid,jsonb), public.gauntlet_save_world(uuid,uuid,uuid,bigint,text,jsonb), public.gauntlet_list_worlds(uuid), public.gauntlet_load_world(uuid,uuid) from public,anon,authenticated;
grant execute on function public.gauntlet_claim_world(uuid,uuid,uuid,uuid,jsonb), public.gauntlet_save_world(uuid,uuid,uuid,bigint,text,jsonb), public.gauntlet_list_worlds(uuid), public.gauntlet_load_world(uuid,uuid) to service_role;
commit;

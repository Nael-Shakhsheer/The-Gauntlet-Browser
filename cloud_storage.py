"""Optional Supabase replica behind local RunStorage. No network on the tick lock.

Auth tokens are verified by Supabase, never decoded and trusted locally. RPCs
are service-role-only transactions; local saves continue on network failure.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import secrets
import threading
import time
import urllib.error
import urllib.request
import uuid
import base64
from urllib.parse import urlsplit


def public_key(value):
    if value.startswith('sb_publishable_'):return True
    try:return json.loads(base64.urlsafe_b64decode(value.split('.')[1]+'==='))['role']=='anon'
    except (ValueError,KeyError,IndexError,TypeError):return False


class Supabase:
    def __init__(self,directory):
        self.url=os.getenv('GAUNTLET_SUPABASE_URL','').rstrip('/')
        self.public=os.getenv('GAUNTLET_SUPABASE_ANON_KEY','')
        self.secret=os.getenv('GAUNTLET_SUPABASE_SERVICE_ROLE_KEY','')
        url=urlsplit(self.url)
        self.configured=bool(url.scheme=='https' and url.hostname and not url.username and not url.password and not url.query and not url.fragment and
            public_key(self.public) and self.secret and self.public!=self.secret)
        self.directory=Path(directory)/'cloud-sync';self.bindings={};self.pending={};self.retries={};self.states={};self.blocked=set()
        self.lock=threading.Lock();self.wake=threading.Event()
        if self.configured:
            for path in self.directory.glob('*.json'):
                try:
                    data=json.loads(path.read_text());uuid.UUID(path.stem);self.bindings[path.stem]=data
                except (OSError,ValueError,TypeError):pass
            for path in self.directory.glob('*.pending.json'):
                try:
                    wid=str(uuid.UUID(path.name.removesuffix('.pending.json')))
                    if wid in self.bindings:self.retries[wid]=json.loads(path.read_text())
                except (OSError,ValueError,TypeError):pass
            threading.Thread(target=self.worker,daemon=True,name='adventure-cloud-sync').start()
            self.wake.set()

    def public_config(self):return dict(configured=self.configured,url=self.url if self.configured else '',anonKey=self.public if self.configured else '')

    def request(self,path,payload=None,token=None):
        if not self.configured:raise ValueError('Cloud storage is not configured. Local saves and portable backups work.')
        headers={'apikey':self.public if token else self.secret,'Content-Type':'application/json'}
        if token or self.secret.startswith('eyJ'):headers['Authorization']='Bearer '+(token or self.secret)
        req=urllib.request.Request(self.url+path,data=json.dumps(payload).encode() if payload is not None else None,headers=headers)
        try:
            with urllib.request.urlopen(req,timeout=8) as response:return json.load(response)
        except urllib.error.HTTPError as e:
            detail=e.read(4096).decode(errors='replace')
            if 'REVISION_CONFLICT' in detail:raise ValueError('Cloud revision conflict. Remote progress was preserved. Export local progress, then reload cloud or import a separate world.') from None
            raise ValueError('Cloud request rejected. Check sign-in, membership and server configuration.') from None
        except (OSError,ValueError):raise ValueError('Cloud unavailable. Local progress remains saved; retry later.') from None

    def actor(self,token):
        if not token or len(token)>8192:raise ValueError('Sign in to cloud storage first.')
        user=self.request('/auth/v1/user',token=token)
        try:return str(uuid.UUID(user['id']))
        except (KeyError,ValueError):raise ValueError('Invalid cloud account.') from None

    def rpc(self,name,**args):return self.request('/rest/v1/rpc/'+name,args)

    def envelope(self,record):
        import save_portability
        room=record['room'];a=room['world']
        return dict(backup=save_portability.project(record),worldId=a['worldId'],creatorCharacter=a['creatorCharacter'],
                    characterIds=[p['characterId'] for p in room['players'].values()])

    def persist_binding(self,wid,row):
        self.directory.mkdir(parents=True,exist_ok=True)
        path=self.directory/(str(uuid.UUID(wid))+'.json');tmp=path.with_suffix('.tmp')
        with tmp.open('w',encoding='utf-8') as out:
            json.dump(row,out);out.flush();os.fsync(out.fileno())
        os.replace(tmp,path)

    def claim(self,world,payload,token):
        actor=self.actor(token)
        with world.lock:
            room,p=world.adventure_access(payload.get('room',''),payload.get('player',''))
            if not __import__('adventure_recovery').proof_matches(payload.get('recovery'),p.get('recoveryProof')):raise ValueError('A private existing-session recovery proof is required; a room code cannot claim a character. Legacy sessions can export and import a new world first.')
            import adventure,save_portability
            a=save_portability.identity(room);wid=a['worldId'];character=p['characterId'];creator=a['creatorCharacter']
            record=self.envelope(adventure.snapshot(room))
        result=self.rpc('gauntlet_claim_world',p_world=wid,p_actor=actor,p_character=character,p_creator=creator,p_record=record)
        row=dict(actor=actor,character=character,revision=result['revision'],savedAt=result.get('savedAt'))
        with self.lock:
            if wid not in self.bindings:
                self.persist_binding(wid,row);self.bindings[wid]=row
        return dict(linked=True,worldId=wid,owner=result['owner'],savedAt=result.get('savedAt'))

    def queue(self,record):
        wid=record['room']['world']['worldId']
        with self.lock:
            if wid not in self.bindings or wid in self.blocked:return
            self.pending[wid]=copy.deepcopy(record);self.states[wid]=dict(pending=True)
        self.wake.set()

    def sync(self,wid,record):
        row=copy.deepcopy(self.bindings[wid]);envelope=self.envelope(record)
        digest=hashlib.sha256(json.dumps(envelope,sort_keys=True).encode()).hexdigest()
        # Keep the exact request body through lost acknowledgements/restarts.
        pending=self.directory/(wid+'.pending.json');pending.parent.mkdir(parents=True,exist_ok=True)
        tmp=pending.with_suffix('.tmp')
        with tmp.open('w',encoding='utf-8') as stream:
            json.dump(record,stream);stream.flush();os.fsync(stream.fileno())
        os.replace(tmp,pending)
        result=self.rpc('gauntlet_save_world',p_world=wid,p_actor=row['actor'],p_character=row['character'],p_expected=row['revision'],p_request=digest,p_record=envelope)
        row.update(revision=result['revision'],savedAt=result['savedAt'])
        with self.lock:
            self.persist_binding(wid,row);self.bindings[wid]=row;self.states[wid]=dict(pending=wid in self.pending)
        pending.unlink(missing_ok=True)

    def worker(self):
        while True:
            self.wake.wait(30);self.wake.clear()
            with self.lock:
                # Retry the exact failed transaction before any newer snapshot.
                jobs=self.retries;self.retries={}
                for wid,record in list(self.pending.items()):
                    if wid not in jobs:jobs[wid]=record;del self.pending[wid]
            for wid,record in jobs.items():
                try:self.sync(wid,record)
                except (ValueError,OSError) as exc:
                    message=str(exc) if isinstance(exc,ValueError) else 'Cloud metadata could not be saved; local backup is intact.'
                    with self.lock:self.states[wid]=dict(error=message,pending=False)
                    # Never retry a CAS conflict with a freshly fetched revision.
                    # A network retry uses identical request/content and expected revision.
                    if 'conflict' not in message.lower():
                        with self.lock:self.retries[wid]=record
                    else:
                        with self.lock:self.blocked.add(wid);self.pending.pop(wid,None)

    def status(self,wid):
        with self.lock:
            row=self.bindings.get(wid,{});state=copy.deepcopy(self.states.get(wid,{}))
        return dict(type='local',label='Local server disk',cloudConfigured=self.configured,cloudLinked=bool(row),
                    cloudSavedAt=row.get('savedAt'),cloudRevision=row.get('revision'),cloud=state)

    def worlds(self,token):return self.rpc('gauntlet_list_worlds',p_actor=self.actor(token))

    def load(self,recovery,token,wid,as_copy=False):
        actor=self.actor(token);wid=str(uuid.UUID(str(wid)))
        result=self.rpc('gauntlet_load_world',p_actor=actor,p_world=wid)
        envelope=result['record'];document,_=__import__('save_portability').validate(envelope['backup'])
        with recovery.world.lock:
            if as_copy:
                return recovery.install(document,envelope['characterIds'].index(result['character']))
            room=next((r for r in recovery.world.rooms.values() if (r.get('adventure') or {}).get('worldId')==wid),None)
            if room:
                p=next((p for p in room['players'].values() if p['characterId']==result['character']),None)
                if not p:raise ValueError('Cloud character unavailable in the active world. Export local progress before recovery.')
                return recovery.session(room['code'],p['id'])
            local_path=recovery.world.storage.adventure_paths.get(wid,recovery.world.storage.directory/'adventures'/(wid+'.json'))
            if local_path.exists():raise ValueError('An existing local record could not be loaded and is preserved. Restore the cloud snapshot as a separate copy.')
            slot=envelope['characterIds'].index(result['character'])
            session=recovery.install(document,slot,cloud=envelope)
            row=dict(actor=actor,character=result['character'],revision=result['revision'],savedAt=result.get('savedAt'))
            with self.lock:self.persist_binding(wid,row);self.bindings[wid]=row
            return session

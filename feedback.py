"""Bounded, ephemeral presentation events. No combat clocks or rules live here."""
import secrets
import time

LIMIT = 128
TTL = 3.0


def scene(room):
    dungeon = room.get('dungeon') or (room.get('adventure') or {}).get('dungeon') or {}
    if not isinstance(dungeon, dict): dungeon = {'id': dungeon}
    return '|'.join(str(v) for v in (room.get('mode', 'gauntlet'),
        (room.get('adventure') or {}).get('current', ''), dungeon.get('id', ''),
        dungeon.get('floor', room.get('dungeonFloor', '')), room.get('stage', 0)))


def stream(room):
    key = scene(room)
    state = room.get('_feedback')
    if not state or state['scene'] != key:
        state = room['_feedback'] = dict(scene=key, epoch=secrets.token_hex(8),
                                         cursor=0, events=[], actors={}, enemies={}, phase=None, wave=None)
    return state


def emit(room, kind, *, actor=None, x=None, y=None, **data):
    state = stream(room)
    now = time.monotonic()
    state['cursor'] += 1
    if actor:
        data.setdefault('ownerId', actor.get('id'))
        data.setdefault('heroClass', actor.get('class', ''))
        if actor.get('magicRunes', {}).get('ascended'): data.setdefault('ascended', True)
        x = actor.get('x') if x is None else x
        y = actor.get('y') if y is None else y
    event = dict(data, id=state['cursor'], kind=kind, at=now, x=x, y=y)
    state['events'] = [e for e in state['events'] if now-e['at'] < TTL][-LIMIT+1:] + [event]
    return event


def sample(room):
    """Observe fixed 20Hz state for windup/recovery and restorative transitions."""
    state = stream(room)
    now = time.monotonic()
    for p in room.get('players', {}).values():
        previous = state['actors'].get(p['id'])
        current = (p.get('hp', 0), p.get('wardUntil', 0) > now, p.get('status'))
        if previous and previous[2] == current[2] == 'alive':
            if current[0] > previous[0]: emit(room, 'heal', actor=p, amount=current[0]-previous[0])
            if current[1] and not previous[1]: emit(room, 'ward', actor=p)
        state['actors'][p['id']] = current
    live = {}
    for e in room.get('enemies', []):
        attack = e.get('pendingAttack') or e.get('roleAttack')
        token = (attack.get('kind'), attack.get('startedAt')) if attack else None
        recovery = max(e.get('recoverUntil', 0), e.get('roleRecoverUntil', 0)) > now
        charge = max(e.get('chargeUntil', 0), e.get('roleChargeUntil', 0)) > now
        previous = state['enemies'].get(e['id'])
        if token and (not previous or token != previous[0]):
            emit(room, 'windup', actor=e, boss=bool(e.get('boss') or e.get('miniBoss')), attack=attack['kind'], targetId=attack.get('targetId'))
        if previous and previous[0] and not token and (recovery or charge):
            emit(room, 'release', actor=e, boss=bool(e.get('boss') or e.get('miniBoss')), attack=previous[0][0])
        if previous and e.get('bossPhase', 1) > previous[1]: emit(room, 'boss_phase', actor=e)
        live[e['id']] = (token, e.get('bossPhase', 1))
    state['enemies'] = live
    phase, wave = room.get('phase'), room.get('stageWave')
    if state['phase'] == 'combat' and phase in ('chest', 'stage_exit', 'cleared'):
        emit(room, 'complete', major=phase == 'cleared')
    if state['wave'] is not None and wave != state['wave'] and phase == 'combat': emit(room, 'wave')
    state['phase'], state['wave'] = phase, wave


def restored(room, actor, kind, **data):
    """Record restoration at resolution, even between successive damage ticks."""
    emit(room, kind, actor=actor, **data)
    stream(room)['actors'][actor['id']] = (actor.get('hp', 0),
        actor.get('wardUntil', 0) > time.monotonic(), actor.get('status'))


def projectile_family(shot):
    """Presentation identity mirrors implemented missiles, including hostile elements."""
    ability = shot.get('abilityId', '')
    if shot.get('effectKind') == 'rock': return 'stone'
    if shot.get('effectKind') == 'lightning': return 'lightning'
    if shot.get('side') == 'enemy' and (shot.get('ownerKind') or shot.get('affinity')):
        return {'Fire':'fire','Ice':'frost','Storm':'lightning','Nature':'nature',
                'Poison':'nature','Dark':'shadow','Arcane':'arcane'}.get(shot.get('affinity'), 'arcane')
    if ability == 'frost_lance': return 'frost'
    return {'Archer':'arrow','Rogue':'blade','Knight':'blade','Wizard':'arcane',
            'Druid':'nature','Cleric':'mixture','Bard':'tonal','Healer':'sacred'}.get(shot.get('class'), 'arcane')


def action_state(room, p):
    """Small comparison around a confirmed request, never around client polling."""
    d=p.get('dialogue') or {}; m=p.get('magicRunes') or {}; a=room.get('adventure') or {}
    return dict(dialogue=(d.get('id'), d.get('presentation', d.get('kind'))),
        interior=p.get('townInterior'),floor=p.get('innFloor',1),
        abilities=tuple(p.get('abilities',[])),hero=p.get('class'),
        gear=tuple(i.get('id') if i else None for i in p.get('toolSlots',[])+p.get('utilitySlots',[])),
        inventory=tuple(i['id'] for i in p.get('inventory',[])),runes=room.get('runes',0),
        magic=m.get('balance',0),ascended=m.get('ascended',False),
        ranks=repr(p.get('heroProgress',{}).get('ranks',{}))+repr(p.get('skillRanks',{})),
        shrines=tuple(a.get('travelShrines',{}).get('active',[])),
        chapter=tuple(sorted(a.get('chapter',{}).get('stages',{}).items())),
        portal=bool(room.get('portalChannel')),
        evidence=tuple(a.get('chapter',{}).get('evidence',[])),cursor=stream(room)['cursor'],epoch=stream(room)['epoch'])


def accepted_action(room, p, payload, before):
    """One private outcome per accepted interaction; no cue for unchanged retries."""
    if before is None:return
    action=payload.get('action'); after=action_state(room,p)
    if action in ('input','ping','chat','revive','stopRevive','target','disconnect'): return
    caused=[e for e in stream(room)['events'] if after['epoch']!=before['epoch'] or e['id']>before['cursor']]
    cause=before['epoch']+':'+str(before['cursor'])
    for event in caused:event['causeId']=cause
    kind=None; extra={}
    if after['ascended'] and not before['ascended']: kind='ascension'
    elif after['shrines'] != before['shrines']: kind='shrine_activate'
    elif action=='dialogueChoice' and payload.get('choice') in ('accept','report') and after['chapter']!=before['chapter']:kind='quest_accept' if payload['choice']=='accept' else 'quest_report'
    elif action in ('chapterAccept','chapterReport') and after['chapter']!=before['chapter']:kind='quest_accept' if action=='chapterAccept' else 'quest_report'
    elif action=='chapterReport':
        # Reports may change the chapter stage without adding evidence; the retry
        # branch emits no new event because it changes no personal reward balance.
        if after['magic']>before['magic']:kind='quest_report'
    elif after['magic']>before['magic']: kind='rune_gain'
    elif after['magic']<before['magic']: kind='rune_spend'
    elif after['ranks']!=before['ranks']:kind='skill_learn'
    elif after['abilities']!=before['abilities'] or after['hero']!=before['hero']:kind='loadout'
    elif after['floor']!=before['floor']:kind='stairs'
    elif after['interior']!=before['interior']:kind='door'
    elif after['portal'] and not before['portal']:kind='portal_charge'
    elif action=='sellItem' and (after['inventory']!=before['inventory'] or after['gear']!=before['gear']):kind='sell'
    elif after['gear']!=before['gear']:kind='equip'
    elif action=='sellItem' and after['inventory']!=before['inventory']:kind='sell'
    elif after['evidence']!=before['evidence']:kind='mechanism' if any(k in after['evidence'] and k not in before['evidence'] for k in ('sluice_open','channel_west','channel_east')) else 'quest_progress'
    elif after['dialogue'][0]!=before['dialogue'][0]:
        kind=('inspect' if after['dialogue'][1] in ('inspection','sign') else 'conversation_open') if after['dialogue'][0] else 'conversation_close'
    elif action in ('loadout','chooseAbility') and after['abilities']!=before['abilities']:kind='loadout'
    if not kind:return
    # Existing chest/bed/quest/transaction events already carry the meaningful
    # outcome. Never stack a second generic confirmation behind them.
    emitted=[e['kind'] for e in stream(room)['events'] if e['id']>before['cursor']]
    if kind not in ('ascension','shrine_activate','rune_gain','rune_spend','quest_report') and any(k in emitted for k in ('loot','curse','rest','purchase','equip','quest','repair','restore','discovery','travel')):return
    emit(room,kind,actor=p,privateTo=None if kind in ('quest_report','shrine_activate','ascension') else p['id'],personal=kind not in ('shrine_activate','ascension'),
         runeAmount=after['magic']-before['magic'],objective=payload.get('quest'),causeId=cause,**extra)


def view(room, player_id):
    sample(room)
    state = stream(room)
    now = time.monotonic()
    state['events'] = [e for e in state['events'] if now-e['at'] < TTL]
    return dict(version=1, scene=state['scene'], epoch=state['epoch'], cursor=state['cursor'],
        events=[dict({k:v for k,v in e.items() if k not in ('at','privateTo')}, age=max(0, now-e['at'])) for e in state['events']
                if not e.get('privateTo') or e['privateTo'] == player_id])

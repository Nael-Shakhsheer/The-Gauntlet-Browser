"""Interruptible party transport: free at attuned shrines, otherwise personal souls."""
import math
import time
import copy
import secrets
import feedback
import adventure
import progression
import region_content as region
import soul_crystal

CHANNEL_SECONDS=3.0


def reason(room):
    if __import__('opening').active(room):return 'Finish the caravan defence before travelling.'
    if room['adventure'].get('locked') or room['phase']=='puzzle':return 'Finish the sealed encounter before travelling.'
    if any(p['status']!='alive' for p in room['players'].values() if p.get('connected',True) and not p.get('bot')):return 'Revive every connected hunter before travelling.'
    return None


def shrine(room):return room.get('townPortal') or {'x':480,'y':270}


def source_shrine(room,p):
    a=room['adventure']
    if a['current'] in region.HUBS:point=shrine(room)
    else:
        point=next((f for f in region.features(room) if f['kind']=='travel_shrine' and f['shrine'] in region.shrine_state(room)['active']),None)
    return bool(point and math.dist((p['x'],p['y']),(point['x'],point['y']))<=100)


def destinations(room):
    a=room['adventure'];result=[]
    entries=[(key,name+' village',key in a['visited']) for key,name in region.HUBS.items()]
    entries += [(s['area'],s['name'],key in region.shrine_state(room)['active']) for key,s in region.SHRINES.items()]
    for key,name,active in entries:
        if key not in a['discovered']:continue
        current=key==a['current']
        result.append(dict(id=key,name=name,position=adventure.AREAS[key]['pos'],current=current,active=active,
            locked='Current location' if current else None if active else 'Visit this village first.' if key in region.HUBS else 'Clear the named guards and attune this shrine.'))
    return result


def personal_reason(room,p,method):
    if p.get('townInterior') or progression.locked(room,p) or p.get('townInteraction')=='guild':return p['name']+': close the conversation and step outside.'
    if p.get('rootUntil',0)>time.monotonic():return p['name']+': wait for the root to end.'
    if method=='shrine' and not source_shrine(room,p):return p['name']+': gather at an activated shrine for free travel.'
    if method=='crystal' and soul_crystal.ensure(p)['charge']<soul_crystal.CAPACITY:return p['name']+': crystal needs 20 souls ('+str(p['soulCrystal']['charge'])+'/20).'
    return None


def charge_reason(room):
    return next((p['name']+': crystal needs 20 souls ('+str(soul_crystal.ensure(p)['charge'])+'/20).'
        for p in room['players'].values() if p.get('connected',True) and not p.get('bot') and soul_crystal.ensure(p)['charge']<20),None)


def readiness(room,p,pending):
    blocked=personal_reason(room,p,pending['method'])
    if blocked:return blocked
    if math.dist((p['x'],p['y']),pending['anchor'])>100:return p['name']+': gather at the transport circle.'
    if p['id'] not in pending['confirmations']:return p['name']+': confirm travel.'
    return None


def request(world,room,player,target,method=None):
    if not adventure.active(room):raise ValueError('Transport belongs to Adventure.')
    if player.get('bot'):raise ValueError('Human hunters choose party travel.')
    if blocked:=reason(room):raise ValueError(blocked)
    d=next((d for d in destinations(room) if d['id']==target),None)
    if not d or d['locked']:raise ValueError(d['locked'] if d else 'Discover and activate this travel point first.')
    method=method or ('shrine' if source_shrine(room,player) else 'crystal')
    if method not in ('shrine','crystal'):raise ValueError('Choose shrine or crystal travel.')
    if blocked:=personal_reason(room,player,method):raise ValueError(blocked)
    if method=='crystal' and (blocked:=charge_reason(room)):raise ValueError(blocked)
    if any(e['hp']>0 and math.dist((e['x'],e['y']),(player['x'],player['y']))<180 for e in room['enemies']):raise ValueError('Enemies are too close. Retreat before travelling.')
    pending=room.get('portalChannel')
    if not pending or pending['target']!=target or pending['method']!=method:
        pending=room['portalChannel']=dict(id=secrets.token_hex(8),target=target,method=method,source=room['adventure']['current'],anchor=[player['x'],player['y']],confirmations=[],startedAt=None,positions={},damage={})
    if math.dist((player['x'],player['y']),pending['anchor'])>100:raise ValueError('Gather near the hunter opening transport.')
    if player['id'] not in pending['confirmations']:pending['confirmations'].append(player['id']);pending['startedAt']=None
    room.pop('_portalOutcome',None)
    tick(world,room,time.monotonic())


def cancel(world,room,message):
    room.pop('portalChannel',None);room['_portalOutcome']=dict(message=message,at=time.monotonic())
    adventure.announce(world,room,message)


def tick(world,room,now):
    pending=room.get('portalChannel')
    if not pending:return
    humans=world._voting_players(room)
    if not humans:return
    if reason(room) or room['adventure']['current']!=pending['source']:cancel(world,room,'Transport interrupted by a sealed encounter.');return
    waiting=[readiness(room,p,pending) for p in humans]
    if any(waiting):
        if pending['startedAt'] is not None:cancel(world,room,next(w for w in waiting if w)+' No charge spent.')
        return
    if any(e['hp']>0 and any(math.dist((e['x'],e['y']),(p['x'],p['y']))<180 for p in humans) for e in room['enemies']):cancel(world,room,'Enemies are too close. Retreat before travelling.');return
    if pending['startedAt'] is None:
        pending.update(startedAt=now,positions={p['id']:[p['x'],p['y']] for p in humans},damage={p['id']:p.get('damageTaken',0) for p in humans})
        adventure.announce(world,room,'Transport opening: stand still for three seconds.');return
    if any(math.dist((p['x'],p['y']),pending['positions'].get(p['id'],[p['x'],p['y']]))>8 or p.get('damageTaken',0)!=pending['damage'].get(p['id'],p.get('damageTaken',0)) for p in humans):cancel(world,room,'Transport interrupted by movement or damage. No charge spent.');return
    if now-pending['startedAt']<CHANNEL_SECONDS:return
    before=copy.deepcopy(room);a=room['adventure'];target=pending['target'];source=a['current']
    try:
        if target in region.HUBS and source not in region.HUBS:a['portalReturn']=dict(area=source,positions=[[p['x'],p['y']] for p in room['players'].values()]) # Preserve legacy facts, never expose arbitrary return destinations.
        if pending['method']=='crystal':
            for p in humans:soul_crystal.ensure(p)['charge']=0
        room.pop('portalChannel',None);adventure.enter(world,room,target,'south')
        point=shrine(room) if target in region.HUBS else next(f for f in region.features(room) if f['kind']=='travel_shrine')
        import combat_environment as terrain
        for i,p in enumerate(room['players'].values()):
            pos=(point['x']+(i-(len(room['players'])-1)/2)*24,point['y']+65)
            if not terrain.walkable(room,*pos) or target in region.HUBS and not world._town_walkable(room,*pos):raise ValueError('No safe landing at this shrine.')
            p.update(x=pos[0],y=pos[1])
        if not adventure.save(world,room) and world.storage:raise ValueError('Transport could not save. No charge spent; the party remains at its origin.')
    except (ValueError,OSError) as error:
        room.clear();room.update(before);cancel(world,room,str(error));return
    feedback.emit(room,'portal_arrive',source=source,destination=target,participants=[dict(ownerId=p['id'],x=p['x'],y=p['y']) for p in humans])
    adventure.announce(world,room,'Arrived at '+adventure.area_name(room,target)+'. Health and recharge unchanged.')


def view(room,player=None):
    if not adventure.active(room):return None
    pending=room.get('portalChannel');humans=[p for p in room['players'].values() if p.get('connected',True) and not p.get('bot')]
    crystal=soul_crystal.ensure(player) if player else None
    waiting=[readiness(room,p,pending) for p in humans] if pending else []
    outcome=room.get('_portalOutcome',{})
    return dict(destinations=destinations(room),reason=reason(room),crystal=crystal and dict(charge=crystal['charge'],capacity=20),
        message=outcome.get('message') if time.monotonic()-outcome.get('at',0)<8 else None,
        methods={method:personal_reason(room,player,method) or (charge_reason(room) if method=='crystal' else None) for method in ('shrine','crystal')} if player else {},
        channel=pending and dict(target=pending['target'],method=pending['method'],id=pending['id'],anchor=list(pending['anchor']),duration=CHANNEL_SECONDS,
            participants=[p['id'] for p in humans],waiting=[w for w in waiting if w],
            ready=sum(w is None for w in waiting),total=len(humans),
            remaining=max(0,CHANNEL_SECONDS-(time.monotonic()-pending['startedAt'])) if pending['startedAt'] is not None and not any(waiting) else None))

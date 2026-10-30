"""Finite, milestone-driven services and discoveries. No timers or new currency."""
import copy
import math
import campaign_quests as quests

EVENTS={
 'workshop':('Orren’s reopened workshop','Orren repairs field equipment. Choose a mobile support standard or a build weapon; this is a personal, one-time fitting.'),
 'caravan':('The returning grain caravan','The repaired crossing and recovered watch records let Edda’s carriers return. Their storm lens rewards fighting groups, at a cost against a lone foe.'),
 'reserve':('The planted reserve','The chosen village kept the seeds alive. Its first small harvest supplies your next journey, rather than an automatic repeating income.'),
 'relief':('Relief at work','Your chosen relief reached the workers or farmers. They offer one supply parcel, with equal value for either outcome.'),
 'channel_cache':('The exposed maintenance shelf','Safe water uncovered a dry shelf beside the channel. The workers left their emergency reserve here.'),
 'lookout_cache':('The lookout’s side cache','Footprints circle the obvious approach. The low reed trail avoids the lookouts; patient movement, concealment or fighting all work.'),
 'oath_trial':('The spring-oath trial','Optional: gather here to face a rootguard, channeler and flanker. Try your transformed signature against a compact formation. Ordinary trails remain open; there is no repeating reward.'),
}


def unlocked(room,key):
    s=quests.state(room)
    return {'workshop':quests.done(room,'fire') and quests.done(room,'water'),
      'caravan':quests.done(room,'watch') and bool(room['adventure']['bridge']),
      'reserve':quests.done(room,'seeds') and quests.done(room,'failed_harvest'),
      'relief':quests.done(room,'steward'),'channel_cache':'intake_restored' in s['evidence'],
      'lookout_cache':quests.done(room,'watch'),'oath_trial':any(__import__('ascension').active(p) for p in room['players'].values())}[key]


def services(room,p,contact):
    result=[];s=quests.state(room)
    for key in ('workshop','reserve'):
        allowed=contact=='orren' if key=='workshop' else contact in ('sella','edda') if s['choices'].get('seeds')=='oakvale' else contact=='tovin'
        if allowed and unlocked(room,key) and 'event:'+key not in p.get('resolvedRewards',{}) and 'event:'+key not in p.get('pendingRewards',{}):result.append(('service_'+key,EVENTS[key][0]+' · choose supplies'))
    if contact in ('tovin','apprentice') and quests.done(room,'water'):
        result.append(('ascension_context','About Ascension and the old spring oath'))
    return result


def features(room):
    import adventure
    if 'seed' not in room['adventure']:return []
    here=room['adventure']['current'];s=quests.state(room);rows=[]
    places=[('caravan','border',630,235),('channel_cache','irrigation_channels',770,170),('lookout_cache','network',210,420)]
    places += [('relief','pump_exterior' if s['choices'].get('relief')=='workers' else 'farmstead',245,410)]
    for key,area,x,y in places:
        if here!=area or not unlocked(room,key):continue
        x,y=adventure.point(room,x,y);rows.append(dict(id='event_'+key,name=EVENTS[key][0],description=EVENTS[key][1],x=x,y=y,kind='discovery',event=key))
    if here=='fields' and unlocked(room,'oath_trial') and 'event:oath_started' not in room['adventure']['claimed']:
        x,y=adventure.point(room,210,375);rows.append(dict(id='oath_begin',name=EVENTS['oath_trial'][0],description=EVENTS['oath_trial'][1],x=x,y=y,kind='mechanism'))
    return rows


def claim(world,room,p,key):
    import adventure,adventure_rewards
    if key not in EVENTS or not unlocked(room,key):raise ValueError('This opportunity is not available yet.')
    receipt='event:'+key
    if receipt in p.get('pendingRewards',{}) or receipt in p.get('resolvedRewards',{}):return False
    before=copy.deepcopy(p);claims=list(room['adventure']['claimed'])
    adventure_rewards.offer(p,receipt,EVENTS[key][0])
    if receipt not in room['adventure']['claimed']:room['adventure']['claimed'].append(receipt)
    if not adventure.save(world,room) and world.storage:
        p.clear();p.update(before);room['adventure']['claimed']=claims
        raise ValueError('The supply choice was not saved; no reward committed.')
    adventure.announce(world,room,p['name']+' can choose a personal reward from '+EVENTS[key][0]+'. Open Rewards.')
    return True


def interact(world,room,p,point):
    if point['id']=='oath_begin':begin_trial(world,room,p);return True
    if not point.get('event'):return False
    import progression
    key=point['event'];claim(world,room,p,key)
    progression.inspect(p,EVENTS[key][0],EVENTS[key][1]+' Your one-time choice is in Rewards; returning does not refill it.')
    return True


def begin_trial(world,room,p):
    import adventure,dungeons,combat_environment as terrain
    if room['adventure']['current']!='fields' or not unlocked(room,'oath_trial'):raise ValueError('An Ascended hunter can invite the party to this optional field trial.')
    if 'event:oath_started' in room['adventure']['claimed']:return
    if any(q['status']!='alive' or q.get('dialogue') or math.dist((p['x'],p['y']),(q['x'],q['y']))>130 for q in world._voting_players(room)):raise ValueError('Gather the connected hunters at the oath marker. The trial is optional; ordinary trails stay open.')
    if any(math.dist((p['x'],p['y']),(e['x'],e['y']))<180 for e in room['enemies']):raise ValueError('Clear the immediate approach before starting the optional trial.')
    before=copy.deepcopy(room['enemies']);claims=list(room['adventure']['claimed']);cache=copy.deepcopy(room['adventure']['areas']['fields']);enemies=[]
    for i,(kind,role,x,y) in enumerate([('troll','defender',340,345),('serpent','channeler',390,405),('wolf','flanker',310,445)]):
        x,y=adventure.point(room,x,y)
        if not terrain.walkable(room,x,y):raise ValueError('The trial formation has no safe space here.')
        e=__import__('encounter_roles').enemy(world,room,'oath-trial-'+str(i),kind,role,x,y)
        e.update(group='oath-trial',combatRole=role,**{'class':{'defender':'Knight','channeler':'Wizard','flanker':'Rogue'}[role]})
        e.update(homeX=x,homeY=y,aggroRadius=190,leashRadius=260);enemies.append(e)
    room['enemies'].extend(enemies);room['adventure']['claimed'].append('event:oath_started')
    if not adventure.save(world,room) and world.storage:
        room['enemies']=before;room['adventure']['claimed']=claims;room['adventure']['areas']['fields']=cache;raise ValueError('Trial was not saved; no attempt started.')
    adventure.announce(world,room,'Spring-oath trial: flank the rootguard, break the marked channel, and dodge the pounce. Retreat remains possible.')


def killed(world,room,e):
    if e.get('group')!='oath-trial' or any(q.get('group')=='oath-trial' for q in room['enemies']):return
    import adventure
    adventure.reward(world,room,'event:oath_trial',0,'story_choice')
    adventure.announce(world,room,'The spring-oath trial is complete. Your new form is a way to protect the living; the remaining works still need you.')


def patrol(room,e,now,dt):
    """A few existing lookouts have readable gaps; no extra mobs or global alarm."""
    if not room.get('adventure') or e.get('group') not in ('network-sentries','hollow-shrine-flank','station-guards'):return False
    import combat_environment as terrain
    phase=(sum(map(ord,e['id']))%30)/5;index=int((now+phase)/4)%2
    goal=(e['homeX']+(-60 if index==0 else 60),e['homeY']+(-25 if index==0 else 25))
    dx,dy=goal[0]-e['x'],goal[1]-e['y'];distance=math.hypot(dx,dy);before=e['x'],e['y']
    if distance:
        step=min(distance,e['speed']*.45*dt);terrain.move(room,e,e['x']+dx/distance*step,e['y']+dy/distance*step,avoid=True)
    e['moving']=math.dist(before,(e['x'],e['y']))>.1
    return True

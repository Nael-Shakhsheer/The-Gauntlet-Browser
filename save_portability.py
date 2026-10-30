"""Portable progress, never session tokens. Validate before creating any room/file.

The internal v1 disk envelope remains readable. Portable v2 is an allow-listed
projection of that envelope, with fresh identities assigned at import.
"""
import copy
import json
import math
import re
import uuid

MAX_BYTES = 2_000_000
WORLD_KEYS = ('version','seed','current','discovered','visited','quests','areas','claimed',
              'bridge','bossComplete','checkpoint','wipeCount','revision','savedAt',
              'dungeons','rewardHistory','homeNpcs','portalReturn','opening','chapter',
              'regionProgress','hubStates','travelShrines','campaign')


def identity(room):
    a = room['adventure']
    # Deterministic migration also lets a preserved legacy file be recognized.
    a.setdefault('worldId', str(uuid.uuid5(uuid.NAMESPACE_URL, 'gauntlet:legacy:'+room['code'])))
    a.setdefault('name', 'Oakvale adventure')
    a.setdefault('revision',0)
    for p in room['players'].values():
        p.setdefault('characterId', str(uuid.uuid5(uuid.UUID(a['worldId']), p['id'])))
    a.setdefault('creatorCharacter', room['players'][room['host']]['characterId'])
    return a


def bounded(value, depth=0):
    if depth > 16: raise ValueError('Backup is too deeply nested.')
    if value is None or isinstance(value, bool): return
    if isinstance(value, (int,float)):
        if not math.isfinite(value) or abs(value)>10**13: raise ValueError('Invalid backup number.')
    elif isinstance(value,str):
        if len(value)>1200: raise ValueError('Backup text is too long.')
    elif isinstance(value,list):
        if len(value)>2000: raise ValueError('Backup list is too long.')
        for v in value: bounded(v,depth+1)
    elif isinstance(value,dict):
        if len(value)>2000 or any(not isinstance(k,str) or len(k)>100 for k in value):
            raise ValueError('Invalid backup object.')
        for v in value.values(): bounded(v,depth+1)
    else: raise ValueError('Invalid backup value.')


def project(record):
    import adventure
    saved=record['room']; a=saved['world']
    world={k:copy.deepcopy(a[k]) for k in WORLD_KEYS if k in a}
    # Receipt/session recipients are private recovery identities, not progress.
    for receipt in world.get('rewardHistory',[]):
        for recipient in receipt.get('recipients',[]): recipient.pop('id',None)
    chars=[]
    for p in saved['players'].values():
        char={k:copy.deepcopy(p[k]) for k in adventure.PLAYER_KEYS if k in p and k!='characterId'}
        char.update(cooldownRemaining=copy.deepcopy(p.get('cooldownRemaining',{})),
                    slotCooldownRemaining=copy.deepcopy(p.get('slotCooldownRemaining',{})),
                    dashRemaining=p.get('dashRemaining',0))
        char['pendingRewards']=copy.deepcopy(p.get('pendingRewards',{}))
        char['resolvedRewards']=copy.deepcopy(p.get('resolvedRewards',{}))
        chars.append(char)
    return dict(version=2,kind='gauntlet-adventure-backup',name=a.get('name','Oakvale adventure'),
                progress=dict(world=world,characters=chars,runes=saved['runes'],difficulty=saved['difficulty']))


def validate(document):
    import adventure, dungeons
    from game import ABILITY_SETS, CLASSES, ITEMS, DIFFICULTIES, CURSES
    raw=json.dumps(document,allow_nan=False)
    if len(raw.encode('utf-8'))>MAX_BYTES: raise ValueError('Backup exceeds 2 MB.')
    bounded(document)
    migrated=False
    if document.get('kind')=='adventure' and document.get('version')==1:
        document=project(document);migrated=True
    if document.get('kind')!='gauntlet-adventure-backup' or document.get('version')!=2:
        raise ValueError('Unsupported backup format. Original file is unchanged.')
    progress=document['progress'];a=progress['world'];chars=progress['characters']
    if a.get('version')!=1 or a.get('current') not in adventure.AREAS:
        raise ValueError('Unsupported world/location.')
    if not isinstance(a.get('seed'),int) or not 0<=a['seed']<2**31:raise ValueError('Invalid world seed.')
    __import__('opening').validate(a.get('opening'),a['current'])
    __import__('chapter_flow').validate(a.get('chapter'))
    __import__('campaign_progress').validate(a.get('campaign'))
    __import__('region_content').validate(a)
    if not isinstance(a.get('revision',0),int) or not 0<=a.get('revision',0)<=10**9:raise ValueError('Invalid save revision.')
    for field in ('bridge','bossComplete'):
        if not isinstance(a.get(field),bool):raise ValueError('Invalid world fact.')
    if not isinstance(a.get('claimed'),list) or any(not isinstance(k,str) for k in a['claimed']):raise ValueError('Invalid reward claims.')
    if a.get('checkpoint',{}).get('bed') not in {None,*[b['id'] for b in __import__('progression').rooms()]}:raise ValueError('Unknown inn recovery bed.')
    if not 1<=len(chars)<=4 or not any(not p.get('bot') for p in chars):raise ValueError('Backup needs 1–4 characters and a human hunter.')
    if progress['difficulty'] not in DIFFICULTIES or not isinstance(progress['runes'],int) or not 0<=progress['runes']<=10**8:
        raise ValueError('Invalid difficulty or Rune pool.')
    if set(a['quests'])!=set(adventure.QUESTS) or any(s not in ('active','tracked','kit_found','puzzle','guardian','complete') for s in a['quests'].values()):raise ValueError('Invalid quest facts.')
    for field in ('discovered','visited','areas'):
        if any(k not in adventure.AREAS for k in a[field]):raise ValueError('Unsupported area; backup preserved.')
    route=a.get('portalReturn')
    if route is not None:
        if not isinstance(route,dict) or route.get('area') not in a['visited'] or route.get('area')=='home':raise ValueError('Invalid portal return route.')
        positions=route.get('positions');size=a['areas'].get(route['area'],{}).get('size',[960,540])
        if not isinstance(positions,list) or len(positions)>4 or any(not isinstance(p,list) or len(p)!=2 or
            any(not isinstance(v,(int,float)) or not 0<=v<=size[i] for i,v in enumerate(p)) for p in positions):raise ValueError('Invalid portal return positions.')
    checkpoint=a['checkpoint'];sanctuary=checkpoint.get('sanctuary')
    if sanctuary is not None:
        spec=__import__('campaign_content').CHECKPOINTS.get(sanctuary)
        if not spec or checkpoint.get('area')!=spec['area'] or checkpoint.get('bed') is not None or sanctuary not in a.get('campaign',{}).get('sanctuaries',[]):raise ValueError('Invalid sanctuary recovery receipt.')
    elif checkpoint.get('area') not in __import__('region_content').HUBS:raise ValueError('Invalid recovery location.')
    for area,cache in a['areas'].items():
        if set(cache)-{'size','enemies','environment','encounterLayout','defeated','entered','details','respawns'}:raise ValueError('Unsupported area content.')
        if len(cache.get('enemies',[]))>80:raise ValueError('Too many enemies.')
        __import__('outdoor_respawns').validate(area,cache)
        templates=[e for g in cache.get('respawns',{}).get('groups',{}).values() for e in g['templates']]
        for e in cache.get('enemies',[])+templates:
            if e.get('combatRole') not in {None,'charger','ranged','ambusher','support','bruiser','draco','defender','channeler','flanker'}:raise ValueError('Unsupported enemy combat role; backup preserved.')
            if set(e)-set(adventure.ENEMY_KEYS) or e.get('kind') not in ('wolf','spider','serpent','troll','minotaur','behemoth','dragon','draco'):
                raise ValueError('Invalid enemy record.')
            if e.get('archetype') is not None:
                spec=__import__('campaign_content').ENEMIES.get(e['archetype'])
                if not spec or e['kind']!=spec['kind']:raise ValueError('Unsupported enemy archetype; original preserved.')
            if type(e.get('bodyRadius',12)) is not int or not 1<=e.get('bodyRadius',12)<=64:raise ValueError('Invalid enemy footprint.')
            if type(e.get('lifeGeneration',0)) is not int or not 0<=e.get('lifeGeneration',0)<=10**9 or not isinstance(e.get('lifeOrigin',e['id']),str) or len(e.get('lifeOrigin',e['id']))>100:raise ValueError('Invalid enemy life.')
            for field in ('x','y','hp','maxHp','damage','speed'):
                if not isinstance(e.get(field),(int,float)) or not 0<=e[field]<=100000:raise ValueError('Invalid enemy properties.')
        env=cache.get('environment') or {}
        if set(env)-{'stage','region','barriers','obstacles','zones'}:raise ValueError('Unsupported terrain.')
        for kind in ('barriers','obstacles','zones'):
            for obj in env.get(kind,[]):
                for field in ('x','y','width','height','radius'):
                    if field in obj and (not isinstance(obj[field],(int,float)) or not 0<=obj[field]<=10000):raise ValueError('Invalid terrain geometry.')
    for p in chars:
        if p.get('class') not in CLASSES:raise ValueError('Unknown hero.')
        if not isinstance(p.get('name'),str) or not 1<=len(p['name'])<=48:raise ValueError('Invalid hunter name.')
        p['name']=__import__('language_filter').clean_name(p['name'])
        if not isinstance(p.get('skillPoints',0),int) or not 0<=p.get('skillPoints',0)<=99:raise ValueError('Invalid training points.')
        for field in ('bot','classChangeUsed','trainingKnown','questAccepted','ultimateIntroduced'):
            if field in p and not isinstance(p[field],bool):raise ValueError('Invalid character flag.')
        curse=p.get('curse')
        if curse is not None:
            if not isinstance(curse,dict):raise ValueError('Invalid curse.')
            template=next((c for c in CURSES if c['effect']==curse.get('effect')),None)
            if not template:raise ValueError('Unknown curse.')
            p['curse']=copy.deepcopy(template)
        for field in ('maxHp','maxMana'):
            if not isinstance(p.get(field),(int,float)) or not 1<=p[field]<=2500:raise ValueError('Invalid character stats.')
        import hero_skills
        __import__('cottage').validate(p)
        __import__('soul_crystal').validate(p)
        __import__('dialogue_choices').validate(p)
        __import__('magic_runes').validate(p)
        __import__('magic_runes').validate_world(a,p)
        hero_skills.validate(p)
        __import__('loadout_presets').validate(p)
        abilities={x[0]:x[7] for x in ABILITY_SETS[p['class']]}
        if p.get('heroProgress'):abilities={k:a['attackType'] for k,a in hero_skills.catalog(p).items()}
        elif len(p['abilities']) not in (2,3) or {abilities.get(x) for x in p['abilities']} not in ({'light','special'},{'light','special','ultimate'}):raise ValueError('Invalid ability loadout.')
        __import__('pouch_storage').validate(p)
        if len(p['inventory'])>__import__('pouch_storage').capacity(p) or len(p['toolSlots'])!=2 or len(p['utilitySlots'])!=3:raise ValueError('Invalid pouch/slots.')
        if not isinstance(p.get('shopStock',[]),list) or len(p.get('shopStock',[]))>30:raise ValueError('Invalid shop stock.')
        all_items=p['inventory']+p['toolSlots']+p['utilitySlots']
        ids=[i['id'] for i in all_items if i]
        if len(ids)!=len(set(ids)):raise ValueError('Duplicate equipment identity.')
        for item in all_items+p.get('shopStock',[]):
            if not item:continue
            if item.get('key') not in ITEMS or not re.fullmatch(r'[a-zA-Z0-9_-]{1,80}',str(item.get('id',''))):raise ValueError('Invalid item.')
            base=ITEMS[item['key']]
            if item.get('slot')!=base['slot'] or any(not isinstance(item.get(k,0),(int,float)) or abs(item.get(k,0))>1000 for k in ('damage','armor')):raise ValueError('Invalid item properties.')
            # Existing items have fixed effects: never import injected factors,
            # effect keys, prices, healing, or presentation fields as gameplay.
            from game import GameWorld
            canonical=GameWorld._make_item(item['key']);canonical['id']=item['id']
            item.clear();item.update(canonical)
        for i,item in enumerate(p['toolSlots']):
            if item and item['slot']!='tool':raise ValueError('Utility in tool slot.')
        for item in p['utilitySlots']:
            if item and item['slot']!='utility':raise ValueError('Tool in utility slot.')
        p['weapon']=next((i for i in p['toolSlots'] if i and i['kind']=='weapon'),None)
        p['armor']=next((i for i in p['toolSlots'] if i and i['kind']=='armor'),None)
        for field in ('skillRanks',):
            if not isinstance(p.get(field,{}),dict) or any(k not in __import__('progression').SKILLS or not isinstance(v,int) or not 0<=v<=3 for k,v in p.get(field,{}).items()):raise ValueError('Invalid training.')
        if any(k not in abilities or not isinstance(v,(int,float)) or not 0<=v<=120 for k,v in p.get('cooldownRemaining',{}).items()):raise ValueError('Invalid recharge.')
        if any(k not in ('basic','active1','active2','active3','ultimate') or not isinstance(v,(int,float)) or not 0<=v<=120 for k,v in p.get('slotCooldownRemaining',{}).items()):raise ValueError('Invalid action-slot recharge.')
        if not isinstance(p.get('dashRemaining',0),(int,float)) or not 0<=p.get('dashRemaining',0)<=10:raise ValueError('Invalid dash recharge.')
        import adventure_rewards
        adventure_rewards.validate(p)
    # Validate additive dungeon state, including attempts, through its real adapter.
    temp={'adventure':copy.deepcopy(a)};dungeons.validate(temp)
    clean=project(dict(room=dict(world=a,players={str(i):p for i,p in enumerate(chars)},runes=progress['runes'],difficulty=progress['difficulty'])))
    clean['name']=str(document.get('name','Oakvale adventure'))[:48]
    return clean,migrated


def summary(document, migrated=False):
    p=document['progress'];a=p['world']
    return dict(name=document['name'],savedAt=a.get('savedAt'),characters=[dict(slot=i,name=c['name'],hero=c['class'],bot=bool(c.get('bot')),items=len(c['inventory']),training=sum(c.get('skillRanks',{}).values())) for i,c in enumerate(p['characters'])],
        runes=p['runes'],completed=sum(v=='complete' for v in a['quests'].values()),locations=len(a['visited']),
        recovery='Caravan encounter checkpoint · no Rune loss' if a.get('opening') and 'opening_complete' not in a['opening']['facts'] else a['checkpoint']['sanctuary'].replace('_',' ').title()+' sanctuary' if a['checkpoint'].get('sanctuary') else 'Upstairs inn bed' if a['checkpoint'].get('bed') else __import__('adventure').AREAS[a['checkpoint']['area']]['name']+' gate',
        dungeons=[k for k,s in a.get('dungeons',{}).items() if s.get('bossComplete')],migrated=migrated)

"""One connected woodland region. Python owns travel, quests and save transactions.

World records contain persistent facts, not monotonic combat clocks or inputs.
Ordinary enemies never respawn. Incomplete puzzle attempts restart on return.
"""
import copy
import logging
import math
import random
import secrets
import time
import feedback
import combat_environment as terrain
import enemy_roles
import dungeons
import progression
import town_layout
import save_portability
import adventure_rewards
import opening
import chapter_flow
from puzzles import new_puzzle
VERSION = 1
LARGE_AREAS = {'road': (1800, 900), 'crossroads': (1920, 1080), 'clearing': (1440, 900)}
BRIDGE_LAYOUT = dict(river=dict(left=568, right=640), crossing=dict(top=235, bottom=285), sprite=dict(x=604, y=337), eastPath=740)
AREAS = {'caravan': dict(name='The Last Caravan', pos=[0, -1], danger=1, region='woodland', exits=[]), 'home': dict(name='Oakvale · Home village', pos=[0, 0], danger=0, region='woodland', exits=[('road', 'south', 'north')]), 'road': dict(name='Southern road', pos=[0, 1], danger=1, region='woodland', exits=[('home', 'north', 'south'), ('crossroads', 'east', 'west'), ('bridge', 'south', 'north')]), 'crossroads': dict(name='Woodland crossroads', pos=[1, 1], danger=2, region='woodland', exits=[('road', 'west', 'east'), ('camp', 'south', 'north'), ('clearing', 'east', 'west'), ('shrine', 'south', 'north')]), 'camp': dict(name='Abandoned camp', pos=[1, 2], danger=3, region='woodland', exits=[('crossroads', 'north', 'south'), ('bridge', 'west', 'east')]), 'clearing': dict(name="Hunter's clearing", pos=[2, 1], danger=3, region='woodland', exits=[('crossroads', 'west', 'east'), ('shrine', 'south', 'north')]), 'shrine': dict(name='Overgrown shrine', pos=[2, 2], danger=4, region='woodland', exits=[('crossroads', 'north', 'south'), ('clearing', 'north', 'south')]), 'bridge': dict(name='Broken bridge', pos=[0, 2], danger=2, region='woodland', exits=[('camp', 'east', 'west'), ('road', 'north', 'south'), ('ruins', 'south', 'north')]), 'ruins': dict(name='Old ruins', pos=[0, 3], danger=6, region='ruins', exits=[('bridge', 'north', 'south')])}
AREAS.update(dungeons.AREAS)
AREAS['road']['exits'].append(('cave_entry', 'east', 'west'))
AREAS['clearing']['exits'].append(('cave_heart', 'west', 'east'))
AREAS['camp']['exits'].append(('tower_1', 'east', 'west'))
AREAS['bridge']['exits'].append(('tower_3', 'east', 'west'))
EXIT_POS = {'north': [480, 48], 'south': [480, 492], 'west': [48, 270], 'east': [912, 270]}
ENTRY_POS = {'north': [480, 108], 'south': [480, 432], 'west': [108, 270], 'east': [852, 270]}
EXIT_OFFSETS = {('crossroads', 'camp'): 0.32, ('crossroads', 'shrine'): 0.72, ('shrine', 'crossroads'): 0.3, ('shrine', 'clearing'): 0.73}
EXIT_OFFSETS.update({('road', 'cave_entry'): 0.78, ('clearing', 'cave_heart'): 0.78, ('bridge', 'tower_3'): 0.64})
SOLID_LANDMARKS = {'camp': [(202, 195, 49, 25), (233, 182, 50, 14), (288, 207, 13, 15)], 'ruins': [(437, 188, 23, 79), (520, 182, 21, 85)]}

def landmark_barriers(area):
    return [dict(id=f'{area}-structure-{i}', x=x, y=y, width=w, height=h, material='cloth' if area == 'camp' else 'stone', blocksShots=True) for i, (x, y, w, h) in enumerate(SOLID_LANDMARKS.get(area, []))]
ENCOUNTER_LAYOUT = 2
GROUPS = {'road': [('road_wolves', 'wolf', 470, 190, 1), ('road_spiders', 'spider', 250, 340, 1), ('road_east_wolves', 'wolf', 725, 305, 2)], 'crossroads': [('cross_spiders', 'spider', 305, 235, 2), ('cross_east_wolves', 'wolf', 750, 250, 1), ('cross_south_spiders', 'spider', 460, 430, 1)], 'camp': [('camp_guards', 'serpent', 585, 285, 2), ('camp_scouts', 'serpent', 280, 390, 1)], 'clearing': [('hunter_wolves', 'wolf', 490, 280, 2), ('hunter_trail_wolves', 'wolf', 205, 235, 1), ('hunter_watch_wolves', 'wolf', 780, 405, 1)], 'bridge': [('bridge_spiders', 'spider', 725, 140, 1), ('bridge_bank_spiders', 'spider', 910, 485, 1)]}
LEGACY_GROUPS = {'road': 'road_wolves', 'crossroads': 'cross_spiders', 'camp': 'camp_guards', 'clearing': 'hunter_wolves', 'bridge': 'bridge_spiders'}
FEATURES = {'home': [('runner', 'Village Runner', 360, 390, 'talk')], 'road': [('tracks', "Hunter's tracks", 405, 315, 'clue'), ('cache', 'Moss-covered cache', 175, 355, 'discovery'), ('rootwater_sign', 'Rootwater passage → lower eastern trail', 665, 365, 'signpost')], 'crossroads': [('sign', 'Woodland signpost', 490, 275, 'signpost')], 'camp': [('kit', 'Guarded repair chest', 555, 265, 'chest')], 'clearing': [('hunter', 'Injured hunter', 480, 315, 'hunter'), ('watch', 'Abandoned watch', 700, 365, 'discovery')], 'shrine': [('altar', 'Shrine altar', 480, 265, 'shrine')], 'bridge': [('repair', 'Bridge workbench', 718, 335, 'bridge')], 'ruins': [('seal', 'Ruins gate seal', 480, 375, 'boss')]}
QUESTS = {'hunter': 'Missing hunter', 'bridge': 'Restore the bridge', 'shrine': 'Silence the shrine', 'region': 'Secure the old ruins'}
DISCOVERIES = {'east_landmark': dict(title='The last irrigated farm', area='eastern_threshold', runes=0, item=None, text='Beyond Dunmere’s surviving irrigation, abandoned farms and dry channels lead toward the pumping works and distant Ashen Ridge. The ridge remains a future region.'), 'cache': dict(title='The old trail cache', area='road', runes=12, item='healing_draught', text='Under the moss, a traveller left supplies for the next person on this side trail.'), 'watch': dict(title='The burned watch', area='clearing', runes=8, item='mana_draught', text='Dragon burns scar the watch. A warning names the Minotaur awakened beneath the old ruins. The dragon flew beyond this woodland.')}
CLASS_REWARDS = {'Knight': 'moonsteel_sword', 'Wizard': 'arcane_conductor', 'Archer': 'arcane_conductor', 'Cleric': 'dragonbone_armor', 'Rogue': 'pursuit_blade', 'Druid': 'summoners_staff', 'Bard': 'dragonbone_armor', 'Healer': 'dragonbone_armor'}
PLAYER_KEYS = ('name', 'class', 'maxHp', 'maxMana', 'abilities', 'inventory', 'toolSlots', 'utilitySlots', 'weapon', 'armor', 'curse', 'classChangeUsed', 'skillPoints', 'skillRanks', 'skillRewards', 'trainingKnown', 'questAccepted', 'bot', 'shopStock', 'adventureGifts', 'trackedObjective', 'characterId', 'pendingRewards', 'resolvedRewards', 'heroProgress', 'adventureLoadout', 'ultimateIntroduced', 'magicRunes', 'dialogueDecisions', 'soulCrystal', 'cottageReceipts', 'loadoutPresets', 'abilityUpgrades', 'pouchLevel')
ENEMY_KEYS = ('id', 'name', 'kind', 'class', 'affinity', 'color', 'baseColor', 'x', 'y', 'hp', 'maxHp', 'damage', 'speed', 'attackRate', 'boss', 'miniBoss', 'bossPhase', 'combatRole', 'homeX', 'homeY', 'group', 'aggroRadius', 'leashRadius', 'lifeOrigin', 'lifeGeneration', 'structure', 'archetype', 'bodyRadius')
PAGES = {'caravan_aftermath': ('Village Runner', ['You got the wounded through. Grain deliveries from Dunmere stopped before this attack; the dragon striking our watch has only made matters worse. Our hunter followed the missing wagons down the Southern road. Read the caravan manifest if you want another clue.', 'Speak to me again to accept the Missing Hunter assignment before setting off. Shops and Skills are open; your two starting skill points are already yours. Inn beds choose recovery. Adventure saves automatically; export a backup before leaving.']), 'adventure_welcome': ('Village Runner', ['Our hunter is missing. Speak to me again to accept the Missing Hunter assignment, then follow the Southern road tracks toward the clearing. Gather at a trail and press E together. Open Skills to spend your two starting points in Oakvale. Map and Journal show your next step; inn beds choose your recovery point.']), 'adventure_tracks': ("Hunter's trail", ["A torn cloak and a trail of blood lead east to the crossroads, then east again to the hunter's clearing. The trail is marked on your map. You can slip around the creatures or retreat through any ordinary trail."]), 'adventure_sign': ('Woodland signpost', ['North: abandoned camp, with tools for the broken bridge. East: the missing hunter. South: the overgrown shrine. The clearing also has a path to the shrine; you need not retrace every step.']), 'adventure_hunter': ('Injured Hunter', ['I followed the missing grain wagons. The brook was already cloudy when the dragon struck the old watch. The woodland guardians turned hostile after the seal broke; I fled here wounded. Restore the bridge and shrine, then face the Minotaur beneath the ruins. We still do not know what the dragon wanted.']), 'adventure_recovered': ('Recovered Hunter', ["Your help brought me home. The shrine's light and a repaired bridge will open the way to the old ruins. Our stores are yours to use; rest upstairs before facing the guardian."]), 'adventure_kit': ('Repair supplies', ['A usable repair kit! The camp path reaches the far side of the broken bridge. Take the kit to its workbench; repairing it opens a direct shortcut to the Southern road.']), 'adventure_repair': ('Bridge restored', ['The missing boards are replaced. Your party can now cross directly between this bridge and the Southern road. Oakvale is a much shorter journey away.']), 'adventure_shrine': ('Shrine inscription', ["Read your totem, then stand on its rune. Alone, it describes your answer. In a party, it describes a teammate's answer: use Share clue or chat. Only connected humans must solve it. The guardian will awaken; its circle traps you until it falls. Trails stay open while you solve the puzzle."]), 'adventure_training': ('Innkeeper', ["Open Skills to learn your hero's abilities. Visiting the road opens a second active slot; completing a woodland quest opens the third. Milestones award points once. Learn, equip or freely respec in either village; recharge and resources are kept. The Guild still offers one class change.", "Rest in an unlocked bed upstairs to choose the party's recovery location. Adventure progress saves automatically. A wipe returns here and costs15% of shared Runes once. Export a backup in Menu → Save files; free online storage is temporary."]), 'adventure_complete': ("Oakvale's watch", ['The Minotaur falls. Recover the pumping register and report to Oakvale’s runner. The Grain Road assignment will open the route to Dunmere’s failing croplands. Ashen Ridge and the pumping works remain later leads. Shops and exploration stay open; export a backup before leaving.']), **{'adventure_' + key: (spec['title'], [spec['text']]) for key, spec in DISCOVERIES.items()}}
progression.PAGES.update(PAGES)
progression.REPLIES.update({key: ['We understand.'] * len(pages) for key, (_, pages) in PAGES.items()})

def active(room):
    return room.get('mode') == 'adventure' and bool(room.get('adventure'))

def point(room, x, y):
    width, height = room.get('areaSize', (960, 540))
    return (x * width / 960, y * height / 540)

def edge_point(room, edge, entry=False, destination=None):
    width, height = room.get('areaSize', (960, 540))
    inset = 108 if entry else 48
    area = room.get('adventure', {}).get('current')
    gate = room.get('hubExitPoints', {}).get(edge) if area in __import__('region_content').HUBS else None
    if gate is not None:
        return {'east': (width - inset, gate), 'west': (inset, gate), 'north': (gate, inset), 'south': (gate, height - inset)}[edge]
    if area == 'bridge' and edge == 'south':
        return (BRIDGE_LAYOUT['eastPath'], height - inset)
    offset = EXIT_OFFSETS.get((area, destination), 0.5)
    return {'north': (width * offset, inset), 'south': (width * offset, height - inset), 'west': (inset, height * offset), 'east': (width - inset, height * offset)}[edge]

def area_name(room, area):
    return 'Restored bridge' if area == 'bridge' and room['adventure']['bridge'] else AREAS[area]['name']

def announce(world, room, text):
    a = room['adventure']
    events = a.setdefault('notifications', [])
    events.append(dict(text=text, at=time.time()))
    del events[:-5]
    world._say(room, 'system', 'Adventure', text)

def start(world, room):
    room['mode'] = 'adventure'
    room['adventure'] = dict(version=VERSION, seed=secrets.randbelow(2 ** 31), current='home', discovered=['home', 'road'], visited=[], quests={key: 'active' for key in QUESTS}, areas={}, claimed=[], bridge=False, bossComplete=False, checkpoint={'area': 'home', 'bed': None}, wipeCount=0, revision=0, savedAt=None, worldId=str(__import__('uuid').uuid4()), name=room.pop('adventureTitle', 'Oakvale adventure'))
    room.update(townsVisited=0, townPressureStages=[], routePressure=0, routeEffect=None, story={'encountered': True, 'quest': 'not_started'}, townWelcome=None, assassinationStage=None, objective=None, bossStages=[], miniBossStages=[], totalStages=25)
    room.update(town_layout.generate(room['adventure']['seed']))
    room['townInstance'] = 'adventure-home-' + str(room['adventure']['seed'])
    room['town'] = 'Oakvale'
    for p in room['players'].values():
        from game import ABILITY_SETS
        p['abilities'] = [ABILITY_SETS[p['class']][0][0], ABILITY_SETS[p['class']][2][0]]
        p['_freshHero'] = True
        p.update(hp=p['maxHp'], mana=p['maxMana'], questAccepted=True)
        p['trackedObjective'] = 'hunter'
        world._stock_shop(room, p)
        __import__('magic_runes').ensure(p)
    world._reset_cooldowns(room)
    enter(world, room, 'home', 'south', initial=True)
    place_checkpoint(room)
    opening.begin(world, room, skip=room.pop('_skipOpening', False))
    chapter_flow.ensure(room, legacy=room.pop('_legacyChapter', False))
    if not opening.active(room):
        for p in world._voting_players(room):
            progression.start_dialogue(p, 'adventure_welcome')
    save(world, room)

def clean_enemies(enemies):
    return [{k: copy.deepcopy(e[k]) for k in ENEMY_KEYS if k in e} for e in enemies]

def capture(room):
    a = room['adventure']
    state = a['areas'].get(a['current'])
    if state is not None:
        state['enemies'] = clean_enemies(room['enemies'])
        state['environment'] = copy.deepcopy(room.get('environment'))
        for z in (state['environment'] or {}).get('zones', []):
            z.update(warnAt=0, readyAt=0)

def snapshot(room):
    capture(room)
    __import__('campaign_progress').reconcile_personal(room)
    __import__('magic_runes').reconcile_reports(room)
    for p in room['players'].values():
        __import__('hero_skills').ensure(room, p)
    a = save_portability.identity(room)
    snapshot = dict(code=room['code'], host=room['host'], difficulty=room['difficulty'], creation=copy.deepcopy(room.get('creation')), world=copy.deepcopy(a), runes=room['runes'], runStats=copy.deepcopy(room.get('runStats', {})), runId=room['runId'], players={pid: {k: copy.deepcopy(p[k]) for k in PLAYER_KEYS if k in p} for pid, p in room['players'].items()}, home={k: copy.deepcopy(room.get(k)) for k in ('townLayout', 'townPaths', 'townVillagers', 'townDecor', 'townSeed', 'townInstance', 'townPortal', 'townDesignVersion', 'innRooms')} if room.get('_currentHub', 'home') == 'home' else {})
    now = time.monotonic()
    for pid, p in room['players'].items():
        snapshot['players'][pid]['recoveryProof'] = p.get('recoveryProof')
        snapshot['players'][pid]['strictSession'] = p.get('strictSession', False)
        if p.get('joinRequestKey'):
            snapshot['players'][pid]['joinRequestKey'] = p['joinRequestKey']
        snapshot['players'][pid]['cooldownRemaining'] = {key: max(0, until - now) for key, until in p.get('abilityCooldowns', {}).items()}
        snapshot['players'][pid]['slotCooldownRemaining'] = {key: max(0, until - now) for key, until in p.get('skillSlotCooldowns', {}).items()}
        from game import SUMMON_TYPES
        for key in p.get('activeSummons', {}):
            snapshot['players'][pid]['cooldownRemaining'][key] = SUMMON_TYPES[key]['recharge']
            s = __import__('hero_skills').slot(p, key)
            if s:
                snapshot['players'][pid]['slotCooldownRemaining'][s] = max(snapshot['players'][pid]['slotCooldownRemaining'].get(s, 0), SUMMON_TYPES[key]['recharge'])
        snapshot['players'][pid]['dashRemaining'] = max(0, p.get('dashCooldownUntil', 0) - now)
    return dict(version=VERSION, kind='adventure', room=snapshot)

def save(world, room):
    if not active(room):
        return False
    if __import__('adventure_transactions').deferred(room):
        return True
    __import__('acquisitions').prime(room)
    pending_before = adventure_rewards.settle(world, room)
    room['_saveAttempt'] = room.get('_saveAttempt', 0) + 1
    __import__('magic_runes').reconcile_reports(room)
    for p in room['players'].values():
        __import__('hero_skills').ensure(room, p)
    __import__('hero_skills').train_companions(world, room)
    a = save_portability.identity(room)
    if not world.storage:
        __import__('acquisitions').confirmed(room)
        return False
    record = snapshot(room)
    stamp = time.time()
    record['room']['world'].update(savedAt=stamp, revision=a['revision'] + 1)
    try:
        with world.metrics.time('adventureDiskMs'):
            world.storage.save_adventure(record)
        a.update(savedAt=stamp, revision=record['room']['world']['revision'])
        a.pop('saveError', None)
        __import__('acquisitions').confirmed(room)
        return True
    except OSError as error:
        if pending_before:
            adventure_rewards.rollback(room, pending_before)
        logging.exception('Adventure could not be saved: %s', room['code'])
        a['saveError'] = 'Save conflict: original/newer progress is preserved. Export this session, then import a separate world before leaving.' if error.errno == __import__('errno').EAGAIN else 'Automatic save failed. Check disk space before leaving; export a backup.'
        for pid in room['players']:
            room.setdefault('privateNotices', {})[pid] = a['saveError']
        return False

def restore(world, record):
    save_portability.validate(save_portability.project(record))
    saved = record['room']
    a = saved['world']
    if a['current'] not in AREAS or any((key not in AREAS for key in a['areas'])) or any((key not in AREAS for key in a.get('discovered', []) + a.get('visited', []))):
        raise ValueError('Unknown Adventure area')
    if saved['code'] in world.rooms:
        raise ValueError('Duplicate saved room code')
    fresh, _ = world.create_room('Adventure restore')
    room = world.rooms.pop(fresh)
    room.update(code=saved['code'], host=saved['host'], mode='adventure', adventure=copy.deepcopy(a), creation=copy.deepcopy(saved.get('creation')), players={}, runes=saved['runes'], difficulty=saved['difficulty'], runId=saved['runId'], runStats=saved.get('runStats', {}), town='Oakvale', townsVisited=0, townWelcome=None, story={'encountered': True, 'quest': 'not_started'})
    room.update(town_layout.generate(a['seed']))
    home = saved.get('home', {})
    if home.get('townDesignVersion') == 2:
        room.update({k: v for k, v in home.items() if v is not None})
    elif home.get('innRooms'):
        room['innRooms'] = copy.deepcopy(home['innRooms'])
    if home.get('townDesignVersion') != 2:
        room['adventure'].pop('homeNpcs', None)
    room['townInstance'] = 'adventure-home-' + str(a['seed'])
    for pid, progress in saved['players'].items():
        p = world._player(pid, progress['name'])
        p.update(copy.deepcopy(progress))
        p['abilityCooldowns'] = {key: time.monotonic() + remaining for key, remaining in p.pop('cooldownRemaining', {}).items()}
        p['skillSlotCooldowns'] = {key: time.monotonic() + remaining for key, remaining in p.pop('slotCooldownRemaining', {}).items()}
        p['dashCooldownUntil'] = time.monotonic() + p.pop('dashRemaining', 0)
        p.update(hp=p['maxHp'], mana=p['maxMana'], connected=bool(p.get('bot')))
        room['players'][pid] = p
        __import__('magic_runes').ensure(p)
        __import__('magic_runes').refresh(p)
    if room['host'] not in room['players']:
        raise ValueError('Missing host')
    a = save_portability.identity(room)
    a.pop('saveError', None)
    dungeons.recover(room)
    chapter_flow.ensure(room)
    __import__('region_content').recover(room)
    enter(world, room, 'caravan' if opening.active(room) else a['checkpoint'].get('area', 'home'), 'south', initial=True)
    if opening.active(room):
        opening.prepare(world, room)
    else:
        place_checkpoint(room)
    room['pausedAt'] = time.monotonic()
    for p in room['players'].values():
        p['adventureRestoredAtBed'] = bool(p.get('townInterior'))
    for pid in room['players']:
        room.setdefault('privateNotices', {})[pid] = 'Caravan checkpoint restored: the unfinished encounter restarts; no Rune penalty.' if opening.active(room) else 'Adventure restored at your recovery point. Completed objectives and equipment are kept.'
    world.rooms[room['code']] = room

def group_positions(area, size, environment, x, y, number, rng):
    """Seeded pack spacing on usable ground, clear of all four arrival positions."""
    width, height = size
    layout = dict(areaSize=size, adventure={'current': area}, environment=environment)
    arrivals = [(px + offset, py) for target, edge, _ in AREAS[area]['exits'] for px, py in [edge_point(layout, edge, entry=True, destination=target)] for offset in (-30, -10, 10, 30)]
    cx, cy = (x * width / 960 + rng.uniform(-8, 8), y * height / 540 + rng.uniform(-8, 8))
    angle = rng.uniform(0, math.tau)
    candidates = [(cx, cy)] + [(cx + math.cos(angle + i * math.tau / 16) * radius, cy + math.sin(angle + i * math.tau / 16) * radius) for radius in (28, 44, 64, 88, 112) for i in range(16)]
    positions = []
    for px, py in candidates:
        px, py = (max(32, min(width - 32, px)), max(32, min(height - 32, py)))
        if area == 'bridge' and px < BRIDGE_LAYOUT['river']['right'] + 20:
            continue
        if not terrain.walkable(layout, px, py) or any((math.dist((px, py), p) < 160 for p in arrivals)) or any((math.dist((px, py), p) < 28 for p in positions)):
            continue
        positions.append((px, py))
        if len(positions) == number:
            return positions
    raise ValueError('No safe encounter positions for ' + area)

def scatter_legacy_enemies(area, state, seed):
    """Spread surviving old large-field mobs once; never add enemies or heal them."""
    if state.get('encounterLayout', 0) >= ENCOUNTER_LAYOUT:
        return
    state['encounterLayout'] = ENCOUNTER_LAYOUT
    if area not in LARGE_AREAS or tuple(state['size']) != LARGE_AREAS[area]:
        return
    sites = GROUPS[area]
    occupied = {}
    for e in state['enemies']:
        if e.get('boss') or e.get('group') != LEGACY_GROUPS[area]:
            continue
        suffix = e['id'].rsplit('-', 1)[-1]
        if not suffix.isdecimal():
            continue
        slot = int(suffix) % len(sites)
        occupied.setdefault(slot, []).append(e)
    for slot, enemies in occupied.items():
        _, _, x, y, _ = sites[slot]
        rng = random.Random(seed + list(AREAS).index(area) * 7919 + slot * 101)
        positions = group_positions(area, state['size'], state['environment'], x, y, len(enemies), rng)
        for e, (px, py) in zip(enemies, positions):
            e.update(x=px, y=py, homeX=px, homeY=py, group=LEGACY_GROUPS[area] + ':' + str(slot))

def build_area(world, room, area):
    expanded = __import__('campaign_expansion').build(world, room, area)
    if expanded is not None:
        return expanded
    if area == 'caravan':
        return dict(size=[1200, 720], enemies=[], environment=opening.environment(), encounterLayout=ENCOUNTER_LAYOUT, defeated=[], entered=True, details=[0] * 6)
    if area in dungeons.AREAS:
        return dungeons.build(world, room, area)
    from game import AFFINITIES, DIFFICULTIES
    spec = AREAS[area]
    danger = spec['danger']
    rng = random.Random(room['adventure']['seed'] + list(AREAS).index(area) * 7919)
    count = max(1, len(world._active_players(room)))
    scale = DIFFICULTIES[room['difficulty']]['multiplier'] / 1.25
    objects = []
    if area == 'camp':
        objects = [dict(id='camp-crate', kind='crate', x=370, y=200, radius=24, hp=24, maxHp=24)]
    if area == 'ruins':
        objects = [dict(id='ruins-rock-' + str(i), kind='rock', x=x, y=y, radius=24, hp=90, maxHp=90) for i, (x, y) in enumerate(((310, 170), (650, 370)))]
    zones = []
    if area == 'shrine':
        zones = [dict(id='shrine-poison', kind='poison', x=675, y=185, radius=43, warnAt=0, readyAt=0)]
    size = list(LARGE_AREAS.get(area, (960, 540)))
    environment = {'stage': danger or 1, 'region': spec['region'], 'obstacles': objects, 'zones': zones, 'barriers': landmark_barriers(area) + __import__('region_content').environment(dict(areaSize=size, adventure={'current': area}))}
    enemies = []
    groups = GROUPS.get(area, [])
    bonus_sites = 1 if area == 'bridge' else len(groups)
    for slot, (group, kind, x, y, number) in enumerate(groups):
        if slot < bonus_sites:
            number += (count - 1) // bonus_sites + int(slot < (count - 1) % bonus_sites)
        positions = group_positions(area, size, environment, x, y, number, rng)
        for i, (px, py) in enumerate(positions):
            hp = round((32 + danger * 10) * (1 + 0.22 * (count - 1)) * scale)
            e = dict(id=area + '-' + group + '-' + str(i), name={'wolf': 'Wolf', 'spider': 'Cave Spider', 'serpent': 'Serpent Guard', 'troll': 'Marsh Troll', 'minotaur': 'Forest Charger'}[kind], kind=kind, affinity='Nature', color=AFFINITIES['Nature'], baseColor='#85977a', x=px, y=py, hp=hp, maxHp=hp, damage=max(2, round((4 + danger) * scale)), speed=64 + danger * 4, attackRate=1, group=group, aggroRadius=150, leashRadius=245)
            e.update(homeX=e['x'], homeY=e['y'], lastAttack=0, stunUntil=0, bleedUntil=0, bleedDamage=0, lastBleedTick=0)
            enemies.append(e)
    enemy_roles.assign({'enemies': enemies})
    return dict(size=size, enemies=clean_enemies(enemies), environment=environment, encounterLayout=ENCOUNTER_LAYOUT, defeated=[], entered=True, details=[rng.randint(-12, 12) for _ in range(6)])

def enter(world, room, area, edge, initial=False, source=None):
    room.pop('_campaignVotes', None)
    __import__('chapter_observations').travel(room, area)
    a = room['adventure']
    first_visit = area not in a['visited']
    if not initial:
        capture(room)
    room.update(skillZones=[], skillHeals=[], skillEchoes=[], ascensionCasts=[], campaignFields=[])
    a['current'] = area
    if area in __import__('region_content').HUBS:
        __import__('region_content').enter_hub(room, area)
    if area not in a['discovered']:
        a['discovered'].append(area)
    if area not in a['visited']:
        a['visited'].append(area)
    if area not in a['areas']:
        a['areas'][area] = build_area(world, room, area)
    state = a['areas'][area]
    __import__('outdoor_respawns').prepare(area, state, world, room)
    state.setdefault('size', [960, 540])
    scatter_legacy_enemies(area, state, a['seed'])
    room['areaSize'] = list(state['size'])
    room.update(phase='town' if area in __import__('region_content').HUBS else 'combat', stage=AREAS[area]['danger'] or 1, region=AREAS[area]['region'], enemies=copy.deepcopy(state['enemies']), environment=copy.deepcopy(state['environment']), effects=[], projectiles=[], hazards=[], pings=[], puzzle=None, objective=None, chest=None, routes=[], routeVotes={}, waveStartsAt=0, encounterName=AREAS[area]['name'], encounterType='adventure', stageWave=1, stageWaves=1)
    sync_bridge_terrain(room)
    __import__('encounter_roles').assign(room, area)
    if area in SOLID_LANDMARKS:
        room['environment']['barriers'] = landmark_barriers(area)
    if area in __import__('region_content').AREAS:
        room['environment']['barriers'] = __import__('region_content').environment(room)
    if not initial:
        world._dismiss_summons(room)
    base = edge_point(room, edge, entry=True, destination=source)
    if area in __import__('region_content').HUBS and (not (area != 'home' and source)):
        base = [480, 460]
    now = time.monotonic()
    arrivals = []
    for i, p in enumerate(room['players'].values()):
        offset = (i - (len(room['players']) - 1) / 2) * (42 if area == 'home' else 20)
        arrival = (base[0] + offset, base[1])
        if area in __import__('region_content').HUBS and area != 'home' and source:
            candidates = [(base[0] + dx, base[1] + dy) for dx in range(-30, 31, 10) for dy in range(-30, 31, 10) if town_layout.clear(room['townLayout'], base[0] + dx, base[1] + dy, 18) and all((town_layout.clear(room['townLayout'], base[0] + dx * t / 6, base[1] + dy * t / 6, 18) for t in range(7)))]
            separated = [q for q in candidates if all((math.dist(q, old) >= 18 for old in arrivals))]
            arrival = min(separated or candidates or [base], key=lambda q: math.dist(q, arrival))
        arrivals.append(arrival)
        p.update(x=arrival[0], y=arrival[1], dx=0, dy=0, attacking=False, reviving=None, townInterior=None, townInteraction=None, townReturn=None, townExitReady=False, innFloor=1, dialogue=None, lastMove=now, lastManaTick=now, preferredTarget=None, aiMoveAt=0, aiDodgeUntil=0, slideVx=0, slideVy=0, adventureTravel=None)
        p.pop('adventureRestoredAtBed', None)
        p.pop('abilityAnimation', None)
        for key in ('campaignAnchor', 'campaignDashUntil', 'campaignStillSince', 'pendingRescueBarrier'):
            p.pop(key, None)
    for e in room['enemies']:
        e.update(lastAttack=0, stunUntil=0, bleedUntil=0, bleedDamage=0, lastBleedTick=0)
    a.pop('travel', None)
    a['locked'] = any((e.get('boss') for e in room['enemies']))
    dungeons.entered(world, room, source)
    __import__('campaign_expansion').entered(world, room)
    if dungeons.inside(room):
        reveal(room, *(target for target, _, _ in AREAS[area]['exits'] if target in dungeons.AREAS and (not dungeons.closed(room, area, target))))
    announce(world, room, 'Arrived at ' + area_name(room, area) + '.')
    if area == 'road' and first_visit:
        announce(world, room, 'Rootwater: lower east cave mouth. West: brook and mill-trail loop. Ordinary trails permit retreat; read signs with E.')
    if area == 'dunmere' and first_visit:
        announce(world, room, 'Dunmere reached. Report the Grain Road assignment to the village runner. Rest upstairs to choose a local recovery bed; the central portal links visited villages.')
    if not initial:
        feedback.emit(room, 'travel', destination=area, dungeon=AREAS[area].get('dungeon'), floor=AREAS[area].get('floor'))

def reveal(room, *areas):
    changed = False
    for area in areas:
        if area not in room['adventure']['discovered']:
            room['adventure']['discovered'].append(area)
            changed = True
    return changed

def sync_bridge_terrain(room):
    """Derived from the saved quest fact, including older cached bridge areas."""
    if room['adventure']['current'] != 'bridge':
        return
    river, crossing = (BRIDGE_LAYOUT['river'], BRIDGE_LAYOUT['crossing'])
    width, height = room['areaSize']

    def barrier(key, top, bottom):
        return dict(id=key, x=river['left'], y=top, width=river['right'] - river['left'], height=bottom - top)
    barriers = [barrier('river-north', 0, crossing['top']), barrier('river-south', crossing['bottom'], height)]
    if not room['adventure']['bridge']:
        barriers.append(barrier('broken-span', crossing['top'], crossing['bottom']))
    room['environment']['barriers'] = barriers

def signpost(room, player):
    if room['phase'] != 'combat' or player.get('townInterior') or player.get('dialogue') or player.get('bot') or (not player.get('connected', True)) or (player['status'] != 'alive'):
        return None
    sign = next((f for f in features(room) if f['kind'] == 'signpost' and math.hypot(f['x'] - player['x'], f['y'] - player['y']) <= 120), None)
    if not sign:
        return None
    return dict(id=sign['id'], name=sign['name'], directions=[dict(direction=edge, directionLabel=edge + (' · left path' if EXIT_OFFSETS.get((room['adventure']['current'], destination), 0.5) < 0.5 else ' · right path' if EXIT_OFFSETS.get((room['adventure']['current'], destination), 0.5) > 0.5 else ''), name=area_name(room, destination), destination=destination) for destination, edge, _ in AREAS[room['adventure']['current']]['exits']])

def exits(room):
    if opening.active(room):
        return []
    a = room['adventure']
    current = a['current']
    result = []
    for destination, edge, reverse in AREAS[current]['exits']:
        x, y = edge_point(room, edge, destination=destination)
        if current == 'home':
            x, y = (480, 490)
        reason = dungeons.closed(room, current, destination)
        if {current, destination} == {'road', 'bridge'} and (not a['bridge']):
            reason = 'Repair the bridge from its workbench.'
        if destination == 'ruins' and (not all((a['quests'][q] == 'complete' for q in ('hunter', 'bridge', 'shrine')))):
            reason = objective(room, 'region')
        if a.get('locked'):
            reason = 'Dungeon encounter sealed. Clear this floor or guardian; a wipe returns to your recovery point.' if dungeons.inside(room) else 'The guardian seals the trails until defeated.'
        name = area_name(room, destination) if destination in a['discovered'] or destination == 'ruins' else 'Unexplored trail'
        if destination in dungeons.AREAS and current not in dungeons.AREAS:
            spec = dungeons.SPECS[dungeons.AREAS[destination]['dungeon']]
            name = spec['name'] + ' · ' + spec['type'] + ' · danger ' + str(spec['danger'])
            if dungeons.ensure(room)[dungeons.AREAS[destination]['dungeon']]['routeOpen']:
                name += ' · cleared'
        reason = reason or __import__('region_content').blocked(room, current, destination)
        reason = reason or __import__('campaign_expansion').closed(room, current, destination)
        detail = None
        entrance = None
        if destination in dungeons.AREAS and current not in dungeons.AREAS:
            key = AREAS[destination]['dungeon']
            spec = dungeons.SPECS[key]
            complete = dungeons.ensure(room)[key]['routeOpen']
            entrance = dict(id=key, name=spec['name'], type=spec['type'], danger=spec['danger'], complete=complete)
            detail = 'Open route · cleared encounters stay cleared.' if complete else 'Retreat before awakening the troll.' if key == 'cave' else 'Retreat between floors; waves seal the stairs.'
            detail = spec['type'].title() + ' · danger ' + str(spec['danger']) + '. ' + detail
        result.append(dict(id=destination, name=name, description=detail, dungeonEntrance=entrance, dungeonComplete=bool(entrance and entrance['complete']), x=x, y=y, edge=edge, entry=reverse, locked=bool(reason), reason=reason))
    return result

def features(room):
    a = room['adventure']
    items = []
    items.extend(dungeons.features(room))
    items.extend(__import__('region_content').features(room))
    items.extend(__import__('settlement_events').features(room))
    items.extend(__import__('campaign_expansion').features(room))
    for key, name, x, y, kind in FEATURES.get(a['current'], []):
        if key == 'hunter' and a['quests']['hunter'] == 'complete':
            continue
        if key == 'kit' and 'repair_kit' in a['claimed']:
            continue
        if key == 'cache' and 'discovery:cache' in a['claimed']:
            continue
        if key == 'seal' and a['bossComplete']:
            continue
        if key == 'altar' and a['quests']['shrine'] == 'complete':
            name = 'Restored shrine'
        if key == 'repair' and a['bridge']:
            name = 'Repaired bridge'
        if a['current'] == 'home':
            x, y = home_npc_position(room, x, y)
        else:
            x, y = point(room, x, y)
        items.append(dict(id=key, name=name, x=x, y=y, kind=kind))
    if a['current'] == 'home' and a['quests']['hunter'] == 'complete':
        x, y = home_npc_position(room, 640, 390, [(f['x'], f['y']) for f in items])
        items.append(dict(id='recovered', name='Corin · recovered hunter', x=x, y=y, kind='hunter'))
    if 'seed' in a:
        items.extend(__import__('campaign_quests').features(room))
        items.extend(__import__('pumping_works').features(room))
    if a['current'] in __import__('region_content').HUBS:
        portal = __import__('village_portals').shrine(room)
        items.append(dict(id='village_portal', name='Village portal shrine', kind='portal', **portal))
    if a.get('opening') and (not a['opening']['manifestRead']) and (a['current'] in ('caravan', 'road')):
        x, y = (550, 430) if a['current'] == 'caravan' else point(room, 425, 300)
        items.append(dict(id='caravan_manifest', name='Read caravan manifest', x=x, y=y, kind='manifest'))
    return items

def home_npc_position(room, x, y, occupied=()):
    cache = room['adventure'].setdefault('homeNpcs', {})
    legacy_key = f'{x},{y}'
    hub = room['adventure']['current']
    key = hub + ':' + legacy_key
    if hub == 'home' and legacy_key in cache and (key not in cache):
        cache[key] = cache[legacy_key]
    if key in cache:
        return cache[key]
    candidates = [(cx, cy) for cy in range(330, 461, 20) for cx in range(200, 781, 20) if town_layout.clear(room['townLayout'], cx, cy, 18) and math.dist((cx, cy), (480, 440)) >= 100 and all((math.dist((cx, cy), p) >= 160 for p in occupied))]
    cache[key] = list(min(candidates, key=lambda p: math.dist(p, (x, y))))
    return cache[key]

def nearby(room, player):
    if player.get('townInterior') or room['phase'] == 'defeat':
        return None
    if room['phase'] == 'puzzle':
        candidates = exits(room)
    else:
        candidates = [f for f in features(room) if f['kind'] != 'signpost'] + exits(room)
    return min((p for p in candidates if math.hypot(p['x'] - player['x'], p['y'] - player['y']) <= 68), key=lambda p: math.hypot(p['x'] - player['x'], p['y'] - player['y']), default=None)

def travel(world, room, player, destination):
    if player.get('bot'):
        return
    if progression.locked(room, player):
        raise ValueError('Finish the conversation first.')
    exit = next((e for e in exits(room) if e['id'] == destination), None)
    if not exit or player.get('townInterior') or math.hypot(exit['x'] - player['x'], exit['y'] - player['y']) > (76 if exit.get('dungeonEntrance') else 68):
        raise ValueError('Gather at that trail marker to travel.')
    if exit['locked']:
        raise ValueError(exit['reason'])
    if player['status'] != 'alive':
        raise ValueError('Ask a teammate for a revive first.')
    player['adventureTravel'] = destination
    room['adventure']['travel'] = destination
    tick_travel(world, room)

def tick_travel(world, room):
    a = room['adventure']
    target = a.get('travel')
    if not target:
        return
    exit = next((e for e in exits(room) if e['id'] == target), None)
    voters = world._voting_players(room)
    if not exit or exit['locked']:
        a.pop('travel', None)
        return
    for p in voters:
        if p.get('townInterior') or math.hypot(p['x'] - exit['x'], p['y'] - exit['y']) > 78:
            p['adventureTravel'] = None
    if voters and all((p.get('adventureTravel') == target and (not progression.locked(room, p)) and (p['status'] == 'alive') and (math.hypot(p['x'] - exit['x'], p['y'] - exit['y']) <= 78) for p in voters)):
        source = a['current']
        enter(world, room, target, exit['entry'], source=source)
        save(world, room)

def reward(world, room, key, runes, item=None):
    a = room['adventure']
    if key in a['claimed']:
        return False
    a['claimed'].append(key)
    room['runes'] += runes
    recipients = []
    if item and key not in adventure_rewards.ACTIVITIES:
        from game import ITEMS, CLASS_WEAPONS
        for p in room['players'].values():
            personal = CLASS_WEAPONS[p['class']] if item == 'class_weapon' else CLASS_REWARDS[p['class']] if item == 'class_reward' else item
            converted = 0
            if len(p['inventory']) < __import__('pouch_storage').capacity(p):
                p['inventory'].append(world._make_item(personal))
            else:
                converted = ITEMS[personal]['sell']
                room['runes'] += converted
            recipients.append(dict(id=p['id'], name=p['name'], item=ITEMS[personal]['name'], convertedRunes=converted))
    dungeon_titles = {'dungeon:cave_supplies': 'Rootwater supplies', 'dungeon:cave_survey': 'Surveyor’s cache', 'dungeon:sluice_supplies': 'Sluice maintenance supplies', 'dungeon:sluice_survey': 'Dry survey reserve', **{'story:' + k: spec['title'] for k, spec in chapter_flow.SPECS.items()}, **{'dungeon:' + k: spec['name'] for k, spec in dungeons.SPECS.items()}, **{f'dungeon:tower:floor{i}': f'Briarwatch · Floor {i}' for i in (1, 2, 3)}}
    title = dungeon_titles.get(key) or QUESTS.get(key, DISCOVERIES.get(key.removeprefix('discovery:'), {}).get('title', key.replace('_', ' ').title()))
    if key in adventure_rewards.ACTIVITIES:
        for p in room['players'].values():
            recipient = adventure_rewards.deliver(world, room, p, key, title)
            if recipient:
                recipients.append(recipient)
    receipts = a.setdefault('rewardHistory', [])
    receipts.append(dict(id=key, title=title, runes=runes, recipients=recipients))
    del receipts[:-8]
    if not key.startswith('dungeon:') or key in ('dungeon:cave_supplies', 'dungeon:cave_survey'):
        feedback.emit(room, 'discovery' if key.startswith(('discovery:', 'dungeon:')) else 'repair' if key == 'bridge' else 'restore' if key == 'shrine' else 'quest', objective=key, major=key == 'region')
    details = '; '.join((p['name'] + ': ' + p['item'] + (f" → {p['convertedRunes']} shared Runes (pouch full)" if p['convertedRunes'] else ' added to pouch') for p in recipients))
    announce(world, room, f'{title}: +{runes} shared Runes' + ('. ' + details if details else '.'))
    return True

def clear_local(room):
    group = {'clearing': 'hunter_wolves', 'camp': 'camp_guards'}.get(room['adventure']['current'])
    return not any((not group or e.get('group') == group or e.get('group', '').startswith(group + ':') for e in room['enemies']))

def interact(world, room, player, point=None):
    if player.get('townInterior'):
        return False
    point = point or nearby(room, player)
    if not point:
        return False
    if player['status'] != 'alive':
        raise ValueError('An ally must revive you before you can interact or travel.')
    if point['id'] in {e['id'] for e in exits(room)}:
        travel(world, room, player, point['id'])
        return True
    if progression.locked(room, player):
        raise ValueError('Finish the conversation first.')
    a = room['adventure']
    key = point['id']
    if point.get('kind') == 'signpost':
        board = signpost(room, player)
        if not board:
            raise ValueError('Move closer to the signpost.')
        reveal(room, *(d['destination'] for d in board['directions']))
        progression.inspect(player, board['name'], '\n'.join((d['directionLabel'].title() + ': ' + d['name'] for d in board['directions'])), 'signpost')
        save(world, room)
        return True
    if key == 'caravan_manifest':
        if not a['opening']['manifestRead']:
            a['opening']['manifestRead'] = True
            announce(world, room, opening.MANIFEST)
            save(world, room)
        progression.inspect(player, 'Caravan manifest', opening.MANIFEST)
        return True
    if key == 'village_portal':
        player['portalMenu'] = time.monotonic()
        return True
    if __import__('campaign_expansion').interact(world, room, player, point):
        return True
    if __import__('settlement_events').interact(world, room, player, point):
        return True
    if __import__('campaign_quests').interact(world, room, player, point):
        return True
    if __import__('pumping_works').interact(world, room, player, key):
        return True
    if dungeons.inside(room) and dungeons.interact(world, room, player, key):
        return True
    if __import__('region_content').interact(world, room, player, point):
        return True
    if key == 'runner':
        progression.start_dialogue(player, 'adventure_runner')
        chapter_flow.ensure(room)
        statuses = {q['status'] for q in chapter_flow.menu(room, player) if q['actionable']}
        player['dialogue']['runnerActions'] = (['accept'] if 'offered' in statuses else []) + (['report'] if 'ready-to-turn-in' in statuses else [])
        return True
    gate = {'kit': 'bridge', 'repair': 'bridge', 'hunter': 'hunter', 'altar': 'shrine', 'seal': 'ruins'}.get(key)
    if gate:
        chapter_flow.require(room, gate)
    if key in ('runner', 'recovered'):
        completed = [dungeons.SPECS[k]['name'] for k, s in dungeons.ensure(room).items() if s['routeOpen']]
        if completed:
            world._say(room, 'system', 'Village Runner' if key == 'runner' else 'Recovered Hunter', 'Your reopened routes are helping Oakvale: ' + ', '.join(completed) + '.')
        progression.start_dialogue(player, 'adventure_complete' if a['bossComplete'] else 'adventure_welcome' if key == 'runner' else 'adventure_recovered')
    elif key == 'tracks':
        if a['quests']['hunter'] != 'complete':
            a['quests']['hunter'] = 'tracked'
        reveal(room, 'crossroads', 'clearing')
        progression.start_dialogue(player, 'adventure_tracks')
    elif key in DISCOVERIES:
        spec = DISCOVERIES[key]
        reward(world, room, 'discovery:' + key, spec['runes'], spec['item'])
        progression.start_dialogue(player, 'adventure_' + key)
    elif key == 'kit':
        if not clear_local(room):
            raise ValueError('Drive off the camp guards to open their repair chest. Trails remain open.')
        if reward(world, room, 'repair_kit', 8):
            a['quests']['bridge'] = 'kit_found'
        reveal(room, 'bridge')
        progression.start_dialogue(player, 'adventure_kit')
    elif key == 'repair':
        if a['bridge']:
            world._say(room, 'system', 'Adventure', 'The bridge is already repaired.')
        elif 'repair_kit' not in a['claimed']:
            raise ValueError('Recover a repair kit from the abandoned camp first.')
        else:
            a['bridge'] = True
            a['quests']['bridge'] = 'complete'
            reward(world, room, 'bridge', 25, 'warding_tonic')
            sync_bridge_terrain(room)
            announce(world, room, 'Shortcut open: cross the restored bridge, then take the north trail to the Southern road.')
            progression.start_dialogue(player, 'adventure_repair')
    elif key == 'hunter':
        if not clear_local(room):
            raise ValueError('Drive off the wolves before helping the injured hunter. You can retreat.')
        progression.start_dialogue(player, 'adventure_hunter')
    elif key == 'altar':
        if a['quests']['shrine'] == 'complete':
            world._say(room, 'system', 'Adventure', 'The shrine is quiet. Its light has returned.')
        elif a['quests']['shrine'] == 'guardian':
            raise ValueError('Defeat the awakened guardian.')
        else:
            progression.start_dialogue(player, 'adventure_shrine')
    elif key == 'seal':
        if not all((a['quests'][q] == 'complete' for q in ('hunter', 'bridge', 'shrine'))):
            raise ValueError('Finish the hunter, bridge and shrine objectives first.')
        spawn_guardian(world, room, final=True)
    save(world, room)
    return True

def advance(world, room, player, kind):
    a = room['adventure']
    if kind == 'adventure_hunter':
        a['quests']['hunter'] = 'complete'
        reward(world, room, 'hunter', 20, 'healing_draught')
        announce(world, room, 'The recovered hunter is home in Oakvale.')
    elif kind == 'adventure_shrine':
        if a['quests']['shrine'] in ('complete', 'guardian') or room.get('puzzle'):
            return
        room['puzzle'] = new_puzzle([p['id'] for p in world._voting_players(room)], {p['id']: p['name'] for p in world._voting_players(room)})
        room['phase'] = 'puzzle'
        a['quests']['shrine'] = 'puzzle'
        world._say(room, 'system', 'Adventure', 'Exchange totem clues. Trails remain open until the guardian awakens.')
    elif kind == 'adventure_training':
        player['trainingKnown'] = True
        player['townInteraction'] = 'innkeeper'
        for p in room['players'].values():
            if p.get('bot'):
                p['trainingKnown'] = True
    reveal_final(room)
    save(world, room)

def reveal_final(room):
    if all((room['adventure']['quests'][q] == 'complete' for q in ('hunter', 'bridge', 'shrine'))):
        reveal(room, 'ruins')

def spawn_guardian(world, room, final=False):
    from game import AFFINITIES, DIFFICULTIES
    a = room['adventure']
    area = a['current']
    key = 'region' if final else 'shrine'
    state = a['areas'][area]
    __import__('outdoor_respawns').prepare(area, state, world, room)
    if key in a['claimed'] or room['enemies']:
        return
    count = max(1, len(world._active_players(room)))
    scale = DIFFICULTIES[room['difficulty']]['multiplier'] / 1.25
    hp = round((540 if final else 250) * (1 + 0.65 * (count - 1)) * scale)
    boss = dict(id=area + '-guardian', name='Labyrinth Minotaur King' if final else 'Shrine Stone Guardian', kind='minotaur' if final else 'troll', affinity='Nature', color=AFFINITIES['Nature'], baseColor='#85977a', x=480, y=205, hp=hp, maxHp=hp, damage=round((11 if final else 8) * scale), speed=75 if final else 48, attackRate=1, boss=True, bossPhase=1, group=key, lastAttack=0, stunUntil=0, bleedUntil=0, bleedDamage=0, lastBleedTick=0, nextBossAttack=time.monotonic() + 1.5)
    room['enemies'] = [boss]
    room['phase'] = 'combat'
    room['puzzle'] = None
    room['encounterType'] = 'large_boss'
    room['encounterName'] = boss['name']
    a['locked'] = True
    if not final:
        a['quests']['shrine'] = 'guardian'
    world._say(room, 'system', 'Adventure', boss['name'] + ' awakens! Trails are sealed until the guardian falls. A wipe returns to the inn; completed quests remain.')
    save(world, room)

def on_kill(world, room, enemy):
    __import__('settlement_events').killed(world, room, enemy)
    if opening.active(room):
        return
    a = room['adventure']
    state = a['areas'][a['current']]
    repeat = __import__('outdoor_respawns').killed(room, enemy)
    key = 'enemy:' + enemy['id']
    if not repeat and key not in a['claimed']:
        a['claimed'].append(key)
        room['runes'] += 3
    origin = enemy.get('lifeOrigin', enemy['id'])
    state['defeated'].append(origin) if origin not in state['defeated'] else None
    if __import__('campaign_progress').on_kill(world, room, enemy):
        save(world, room)
        return
    if __import__('region_content').on_kill(room, enemy):
        save(world, room)
        return
    if __import__('pumping_works').on_kill(world, room, enemy):
        save(world, room)
        return
    if dungeons.inside(room):
        dungeons.on_kill(world, room)
        save(world, room)
        return
    if enemy.get('boss'):
        a.pop('locked', None)
        if a['current'] == 'shrine':
            a['quests']['shrine'] = 'complete'
            room['environment']['zones'] = []
            reward(world, room, 'shrine', 35, 'class_weapon')
            announce(world, room, 'Shrine restored: green light and new growth replace the creeping poison.')
        else:
            a['quests']['region'] = 'complete'
            a['bossComplete'] = True
            reward(world, room, 'region', 70, 'class_reward')
            for p in world._voting_players(room):
                progression.start_dialogue(p, 'adventure_complete')
            world._add_effect(room, 'puzzle_solved', 480, 270, '#ffe08a', duration=2, text='WOODLAND REGION COMPLETE')
    reveal_final(room)
    save(world, room)

def puzzle_solved(world, room):
    room['puzzle'] = None
    spawn_guardian(world, room)

def leash(world, room, enemy, target, now):
    if opening.active(room):
        return False
    if room['adventure']['current'] == 'cellar' and room['adventure'].get('locked'):
        return False
    if enemy.get('boss') or (dungeons.inside(room) and dungeons.state(room).get('attempt')):
        return False
    hx, hy = (enemy['homeX'], enemy['homeY'])
    limit = enemy['leashRadius']
    target_distance = math.hypot(target['x'] - hx, target['y'] - hy)
    here = math.hypot(enemy['x'] - hx, enemy['y'] - hy)
    if not enemy.get('aggro') and target_distance <= enemy['aggroRadius']:
        enemy['aggro'] = True
    if target_distance > limit or here > limit or enemy.get('returning'):
        enemy.update(aggro=False, returning=True)
    if enemy.get('aggro'):
        return False
    enemy.pop('roleAttack', None)
    enemy.pop('pendingAttack', None)
    enemy.update(roleChargeUntil=0, chargeUntil=0, moveDecisionAt=0)
    room['projectiles'] = [s for s in room['projectiles'] if s['ownerId'] != enemy['id']]
    room['hazards'] = [h for h in room['hazards'] if h['ownerId'] != enemy['id']]
    dt = min(0.1, max(0, now - enemy.get('lastAiTick', now - 0.05)))
    enemy['lastAiTick'] = now
    distance = max(0.001, here)
    step = min(here, enemy['speed'] * dt)
    old = (enemy['x'], enemy['y'])
    terrain.move(room, enemy, enemy['x'] + (hx - enemy['x']) / distance * step, enemy['y'] + (hy - enemy['y']) / distance * step, avoid=True)
    enemy['moving'] = math.dist(old, (enemy['x'], enemy['y'])) > 0.1
    if here < 12:
        enemy['returning'] = False
    return True

def rest(world, room, player, bed_id):
    bed = next((r for r in room['innRooms'] if 'bed_' + r['id'] == bed_id and (not r['locked'])), None)
    if player.get('innFloor') != 2 or not bed:
        raise ValueError('Find an unlocked upstairs bed.')
    room['adventure']['checkpoint'] = {'area': room['adventure']['current'], 'bed': bed['id']}
    room['checkpoint'] = {'stage': 1, 'town': area_name(room, room['adventure']['current']), 'bed': bed['id'], 'townInstance': room['townInstance'], 'shopStock': {pid: copy.deepcopy(p['shopStock']) for pid, p in room['players'].items()}}
    for p in room['players'].values():
        p.update(hp=p['maxHp'], mana=p['maxMana'], status='alive', deathRecorded=False)
    room['checkpointSavedAt'] = time.time()
    feedback.emit(room, 'rest', actor=player)
    world._say(room, 'system', 'Innkeeper', 'Party rested. Recovery point set at ' + bed['name'] + '. World progress is saved automatically.')
    save(world, room)

def place_checkpoint(room):
    sanctuary = room['adventure']['checkpoint'].get('sanctuary')
    if sanctuary:
        spec = __import__('campaign_content').CHECKPOINTS[sanctuary]
        x, y = point(room, *spec['position'])
        for i, p in enumerate(room['players'].values()):
            p.update(x=x + i * 20, y=y, dx=0, dy=0)
        return
    bed = room['adventure']['checkpoint'].get('bed')
    room['checkpoint'] = {'stage': 1, 'town': area_name(room, room['adventure']['current']), 'bed': bed, 'townInstance': room['townInstance'], 'shopStock': {pid: copy.deepcopy(p['shopStock']) for pid, p in room['players'].items()}}
    if bed:
        for p in room['players'].values():
            progression.place_at_checkpoint(room, p)

def wipe(world, room):
    if opening.active(room):
        return opening.wipe(world, room)
    __import__('chapter_observations').event(room, 'wipe')
    a = room['adventure']
    a['wipeCount'] += 1
    capture(room)
    __import__('region_content').recover(room)
    loss = __import__('adventure_economy').wipe_loss(room['runes'])
    room['runes'] -= loss
    for p in world._active_players(room):
        world._record_death(room, p)
    world._finish_stage_stats(room, 'defeat')
    world._dismiss_summons(room)
    if dungeons.inside(room):
        capture(room)
        dungeons.recover(room)
        room['enemies'] = copy.deepcopy(a['areas'][a['current']]['enemies'])
        room['environment'] = copy.deepcopy(a['areas'][a['current']]['environment'])
    if a.get('locked'):
        room['enemies'] = []
        a.pop('locked', None)
        if a['current'] == 'shrine':
            a['quests']['shrine'] = 'active'
    enter(world, room, a['checkpoint'].get('area', 'home'), 'south')
    place_checkpoint(room)
    for p in room['players'].values():
        p.update(status='alive', hp=p['maxHp'], mana=p['maxMana'], deathRecorded=False, dialogue=None)
        room.setdefault('privateNotices', {})[p['id']] = f'Party wipe: {loss} Runes lost once. Returned to the inn; completed quests and routes remain.'
    world._say(room, 'system', 'Adventure', f'The party returns to its inn. Lost {loss} shared Runes (15%); objectives and items remain.')
    save(world, room)

def tick(world, room, now):
    if opening.active(room):
        return opening.tick(world, room, now)
    __import__('campaign_expansion').tick(world, room, now)
    __import__('outdoor_respawns').tick(world, room, now)
    __import__('village_portals').tick(world, room, now)
    tick_travel(world, room)
    chapter_flow.reconcile(room)

def objective(room, key):
    a = room['adventure']
    status = a['quests'][key]
    if status == 'complete':
        return {'bridge': 'Restored bridge · north shortcut open.', 'hunter': 'Recovered hunter · home in Oakvale.', 'shrine': 'Shrine restored · poison removed.', 'region': 'Minotaur King defeated · Oakvale celebrates.'}[key]
    if key == 'hunter':
        return 'Follow the Southern road tracks to the clearing; drive off the wolves and help the hunter.'
    if key == 'bridge':
        return 'Take the repair kit to the bridge workbench.' if 'repair_kit' in a['claimed'] else 'Find the repair kit in the abandoned camp.'
    if key == 'shrine':
        return 'Defeat the awakened shrine guardian.' if status == 'guardian' else 'Read the shrine altar, share rune clues, then defeat its guardian.'
    remaining = [QUESTS[q] for q in ('hunter', 'bridge', 'shrine') if a['quests'][q] != 'complete']
    return 'Enter the old ruins through the restored bridge; awaken the Minotaur King.' if not remaining else 'Old ruins sealed. Required: ' + ', '.join(remaining) + '. Complete these in any order.'

def track(world, room, player, key):
    if isinstance(key, str) and key in __import__('campaign_content').QUESTS:
        if __import__('campaign_progress').status(room, key) not in ('offered', 'accepted', 'ready-to-turn-in'):
            raise ValueError('This campaign assignment is not active.')
        player['trackedObjective'] = key
        save(world, room)
        return
    if isinstance(key, str) and key in chapter_flow.SPECS and (not chapter_flow.ensure(room)['legacy']):
        if room['adventure']['chapter']['stages'][key] not in ('offered', 'accepted', 'ready-to-turn-in'):
            raise ValueError('That assignment is not active.')
        player['trackedObjective'] = key
        save(world, room)
        return
    if isinstance(key, str) and key in dungeons.SPECS:
        s = dungeons.ensure(room)[key]
        if not s['entrances']:
            raise ValueError('Discover that dungeon entrance first.')
        if s['bossComplete']:
            raise ValueError('That dungeon is already complete.')
        player['trackedObjective'] = key
        save(world, room)
        return
    if not isinstance(key, str) or key not in QUESTS:
        raise ValueError('Choose a woodland objective from the journal.')
    if key == 'region' and 'ruins' not in room['adventure']['discovered']:
        raise ValueError('Complete the three woodland objectives to reveal the ruins first.')
    if room['adventure']['quests'][key] == 'complete':
        raise ValueError('That objective is already complete.')
    if player.get('trackedObjective', 'hunter') == key:
        return
    player['trackedObjective'] = key
    save(world, room)

def tracking(room, player):
    if opening.active(room):
        return dict(id='opening', title='The Last Caravan', area='caravan', complete=False, nextExit=None, nextStep=opening.view(room)['objective'])
    expanded = __import__('campaign_expansion').tracking(room, player)
    if expanded is not None:
        return expanded
    a = room['adventure']
    key = player.get('trackedObjective', 'hunter')
    chapter = chapter_flow.ensure(room)
    chapter_flow.reconcile(room)
    if not chapter['legacy'] and key not in dungeons.SPECS:
        assignment = key if key in chapter_flow.SPECS and chapter['stages'][key] in ('offered', 'accepted', 'ready-to-turn-in') else next((k for k in chapter_flow.MAIN_ORDER if chapter['stages'][k] != 'complete'), None)
        if assignment:
            spec = chapter_flow.SPECS[assignment]
            status = chapter['stages'][assignment]
            target = chapter_flow.action_hub(assignment, status) if status in ('offered', 'ready-to-turn-in') else {'hunter': 'clearing', 'bridge': 'bridge' if 'repair_kit' in a['claimed'] else 'camp', 'water': 'brook', 'shrine': 'shrine', 'watch': 'watch', 'ruins': 'ruins', 'border': 'dunmere', 'failed_harvest': 'fields', 'irrigation': 'mill', 'mill_cellar': 'cellar', 'chapter_outcome': 'fields', 'upstream': 'irrigation_channels' if 'upstream_sample' not in chapter['evidence'] else 'farmstead', 'steward': 'pump_exterior' if 'steward_account' not in chapter['evidence'] else 'dunmere', 'sluice_route': 'sluice_entry' if 'valve_west' not in chapter['evidence'] else 'sluice_gallery' if 'valve_east' not in chapter['evidence'] else 'pump_chamber', 'pumping_finale': 'pump_chamber', 'fire': 'yard', 'letters': next((area for fact, area in [('letter_road', 'road'), ('letter_brook', 'brook'), ('letter_yard', 'yard')] if fact not in chapter['evidence']), 'home'), 'seeds': 'home' if chapter['stages']['fire'] == 'complete' and 'seed_supply' in chapter['evidence'] else 'yard', 'root_sump': 'farmstead'}[assignment]
            contact = __import__('campaign_quests').NAMES.get(__import__('campaign_quests').CONTACTS.get(assignment, ['runner'])[0], 'the village runner')
            text = 'Speak to ' + contact + ' to ' + ('accept this assignment.' if status == 'offered' else 'report your findings.') if status in ('offered', 'ready-to-turn-in') else spec['objective']
            waypoint = target if target in a['discovered'] else 'crossroads' if 'crossroads' in a['discovered'] else 'road'
            queue = [(a['current'], [])]
            seen = set()
            route = []
            while queue:
                here, path = queue.pop(0)
                if here == waypoint:
                    route = path
                    break
                if here in seen:
                    continue
                seen.add(here)
                for other, _, _ in AREAS[here]['exits']:
                    if other in a['discovered'] and (not ({here, other} == {'road', 'bridge'} and (not a['bridge']))) and (not dungeons.closed(room, here, other)):
                        queue.append((other, path + [other]))
            return dict(id=assignment, title=spec['title'], area=target if target in a['discovered'] else None, complete=False, nextExit=route[0] if route else None, nextStep=text)
    if not chapter['legacy'] and all((chapter['stages'][k] == 'complete' for k in chapter_flow.MAIN_ORDER)) and (key not in dungeons.SPECS):
        return dict(id='pumping_finale', title='Water within reach', area='dunmere', complete=True, nextExit=None, nextStep='The works are safe. Review unfinished optional stories and dungeons, shop or export a backup. Ashen Ridge is a future lead.')
    if key in dungeons.SPECS:
        s = dungeons.ensure(room)[key]
        spec = dungeons.SPECS[key]
        target = ('pump_chamber' if 'pump_chamber' in a['discovered'] else 'sluice_entry') if key == 'sluice' else 'cave_heart' if key == 'cave' and 'cave_heart' in a['discovered'] else 'cave_entry' if key == 'cave' else 'tower_' + str(min(3, len(s['completedFloors']) + 1))
        if target not in a['discovered']:
            target = spec['entrances'][0]
        queue = [(a['current'], [])]
        seen = set()
        route = []
        while queue:
            here, path = queue.pop(0)
            if here == target:
                route = path
                break
            if here in seen:
                continue
            seen.add(here)
            for other, _, _ in AREAS[here]['exits']:
                if other not in a['discovered'] or dungeons.closed(room, here, other) or ({here, other} == {'road', 'bridge'} and (not a['bridge'])):
                    continue
                queue.append((other, path + [other]))
        text = 'Dungeon complete · choose another goal in Journal.' if s['bossComplete'] else 'Head to ' + area_name(room, target) + '.' if a['current'] != target else 'Secure both mechanisms and report to Tovin before awakening the Harvest Warden.' if key == 'sluice' else 'Explore east and awaken the troll in its den.' if key == 'cave' else 'Gather at the watch bell, clear this floor, then choose the stairs.'
        return dict(id=key, title=spec['name'], area=target, nextStep=text, nextExit=route[0] if route and (not s['bossComplete']) else None, complete=s['bossComplete'])
    if key not in QUESTS:
        key = 'hunter'
    target = {'hunter': 'clearing', 'shrine': 'shrine', 'region': 'ruins', 'bridge': 'bridge' if 'repair_kit' in a['claimed'] else 'camp'}[key]
    complete = a['quests'][key] == 'complete'
    known = a['discovered']
    waypoint = target if target in known else 'crossroads' if 'crossroads' in known else 'road'
    queue = [(a['current'], [])]
    seen = set()
    route = []
    while queue:
        here, path = queue.pop(0)
        if here == waypoint:
            route = path
            break
        if here in seen:
            continue
        seen.add(here)
        for other, _, _ in AREAS[here]['exits']:
            if other not in known or ({here, other} == {'road', 'bridge'} and (not a['bridge'])):
                continue
            if dungeons.closed(room, here, other):
                continue
            if other == 'ruins' and (not a['bossComplete']) and any((a['quests'][q] != 'complete' for q in ('hunter', 'bridge', 'shrine'))):
                continue
            queue.append((other, path + [other]))
    if complete:
        text = objective(room, key) + ' Choose another goal in Journal.'
    elif target not in known:
        text = 'Read the crossroads signpost to find the trail.' if a['current'] == 'crossroads' else "Read the hunter's tracks on the Southern road." if a['current'] == 'road' else 'Follow the Southern road toward the crossroads.'
    elif a['current'] != target:
        text = 'Head to ' + area_name(room, target) + '.'
    else:
        text = {'hunter': 'Drive off the wolves, then help the injured hunter.', 'bridge': 'Use the repair kit at the east-bank workbench.' if 'repair_kit' in a['claimed'] else 'Drive off the camp guards and open the repair chest.', 'shrine': 'Defeat the awakened guardian.' if a['quests']['shrine'] == 'guardian' else 'Read the altar, then solve the rune clues.', 'region': 'Awaken and defeat the Minotaur King.'}[key]
    return dict(id=key, title=QUESTS[key], area=target if target in known else None, nextStep=text, nextExit=route[0] if route and (not complete) else None, complete=complete)

def view(world, room, player):
    if not active(room):
        return None
    a = room['adventure']
    known = a['discovered']
    locations = []
    links = []
    tracked = __import__('campaign_guidance').enrich(room, player, tracking(room, player))
    chapter_rows = chapter_flow.menu(room, player) + __import__('campaign_expansion').menu(room, player)
    for key in known:
        if key == 'caravan':
            continue
        if key in dungeons.AREAS or key == 'cellar':
            continue
        quest = {'clearing': 'hunter', 'shrine': 'shrine', 'ruins': 'region'}.get(key)
        if key == 'camp' and 'repair_kit' not in a['claimed']:
            quest = 'bridge'
        if key == 'bridge':
            quest = 'bridge'
        locations.append(dict(id=key, name=area_name(room, key), position=AREAS[key]['pos'], tracked=key == tracked['area'] and (not tracked['complete']), visited=key in a['visited'], current=key == a['current'], description=__import__('region_content').description(key), objective=('✓ ' if a['quests'][quest] == 'complete' else 'Quest: ') + QUESTS[quest] if quest else None))
        for other, edge, entry in AREAS[key]['exits']:
            if other in known and other not in dungeons.AREAS and (other != 'cellar') and (key < other):
                links.append(dict(fromId=key, toId=other, fromEdge=edge, toEdge=entry, locked={key, other} == {'road', 'bridge'} and (not a['bridge']) or bool(__import__('region_content').blocked(room, key, other)) or bool(dungeons.closed(room, key, other)) or bool(__import__('campaign_expansion').closed(room, key, other) or __import__('campaign_expansion').closed(room, other, key)) or ('ruins' in (key, other) and (not all((a['quests'][q] == 'complete' for q in ('hunter', 'bridge', 'shrine')))))))
    travel_to = a.get('travel')
    exit = next((e for e in exits(room) if e['id'] == travel_to), None)
    humans = world._voting_players(room)
    ready = sum((p.get('adventureTravel') == travel_to and (not p.get('townInterior')) and exit and (math.hypot(p['x'] - exit['x'], p['y'] - exit['y']) <= 78) for p in humans)) if exit else 0
    markers = exits(room)
    for e in markers:
        e['tracked'] = e['id'] == tracked['nextExit']
    members = [dict(id=p['id'], name=p['name'], state='downed' if p['status'] != 'alive' else 'conversation' if progression.locked(room, p) else 'gather' if not exit or p.get('townInterior') or math.hypot(p['x'] - exit['x'], p['y'] - exit['y']) > 78 else 'confirm' if p.get('adventureTravel') != travel_to else 'ready') for p in humans] if travel_to else []
    discoveries = [dict(id=k, title=v['title'], text=v['text'], area=v['area']) for k, v in DISCOVERIES.items() if 'discovery:' + k in a['claimed']]
    if 'dry_spring_found' in a['claimed']:
        discoveries.append(dict(id='dry_spring', title='The dry spring casket', text='A surveyor hid one personal Magic Rune above the old spring. Each character can inspect it once.', area='hollow'))
    if a.get('opening', {}).get('manifestRead'):
        discoveries.append(dict(id='caravan_manifest', title='Caravan manifest', text=opening.MANIFEST, area='road'))
    for key, (title, text) in __import__('settlement_events').EVENTS.items():
        if 'event:' + key in a['claimed']:
            discoveries.append(dict(id='event:' + key, title=title, text=text, area=None))
    result = dict(area=a['current'], name=area_name(room, a['current']), danger=AREAS[a['current']]['danger'], exits=markers, features=features(room), nearby=nearby(room, player), signpost=None, bridgeLayout=BRIDGE_LAYOUT if a['current'] == 'bridge' else None, locations=locations, connections=links, dungeons=dungeons.view(room) + __import__('region_content').dungeon_view(room), dungeon=dict(id=AREAS[a['current']]['dungeon'], type=dungeons.SPECS[AREAS[a['current']]['dungeon']]['type'], floor=AREAS[a['current']].get('floor'), chamber=a['current']) if dungeons.inside(room) else dict(id='mill_cellar', type='underground', chamber='cellar') if a['current'] == 'cellar' else None, opening=opening.view(room), openingComplete=bool(a.get('opening') and (not opening.active(room))), chapter=chapter_rows, chapterMenu=player.get('chapterMenu'), campaignExtension=__import__('campaign_expansion').view(room), magicRunes=__import__('magic_runes').view(room, player), campaign=__import__('campaign_quests').world_view(room), nextRegion=__import__('campaign_expansion').next_region(room), journal=[dict(id='opening', title='The Last Caravan', status='active', objective=opening.view(room)['objective'], visibility='active')] if opening.active(room) else __import__('campaign_guidance').journal(room, player, chapter_rows) if not chapter_flow.ensure(room)['legacy'] else [dict(id=k, title=v, status=a['quests'][k], objective=objective(room, k), visibility='completed' if a['quests'][k] == 'complete' else 'undiscovered' if k == 'region' and 'ruins' not in known else 'active') for k, v in QUESTS.items()], tracked=tracked, recap=__import__('campaign_guidance').recap(room, player, tracked), discoveries=discoveries, undiscoveredCount=sum(('discovery:' + k not in a['claimed'] for k in DISCOVERIES)) + int('dry_spring_found' not in a['claimed']), rewards=a.get('rewardHistory', []), notifications=[e for e in a.get('notifications', []) if time.time() - e['at'] < 7], travelMembers=members, bridge=a['bridge'], hunterHome=a['quests']['hunter'] == 'complete', shrineRestored=a['quests']['shrine'] == 'complete', complete=a['bossComplete'], travel=travel_to, ready=ready, total=len(humans), locked=bool(a.get('locked')), savedAt=a.get('savedAt'), saveError=a.get('saveError'), checkpointBed=a['checkpoint'].get('bed'), saveInfo=world.adventure_summary(room, player), pendingRewards=adventure_rewards.view(world, player), portals=__import__('village_portals').view(room, player), portalMenu=player.get('portalMenu'), persistence=bool(world.storage), landmarkDetails=a['areas'][a['current']]['details'])
    return result
__import__('region_content').install(__import__(__name__))
__import__('pumping_works').install(__import__(__name__))
__import__('campaign_expansion').install(__import__(__name__))

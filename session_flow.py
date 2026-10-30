"""Creation retry receipts belong to a private nonce, never a public room code."""
import hashlib
import re
import uuid
import language_filter
import adventure

def key(payload):
    nonce = payload.get('requestId')
    if not isinstance(nonce, str) or not re.fullmatch('[A-Za-z0-9_-]{24,128}', nonce):
        raise ValueError('A valid private creation request is required.')
    return hashlib.sha256(nonce.encode()).hexdigest()

def create(world, payload, instance):
    from game import CLASSES, DIFFICULTIES
    token = key(payload)
    mode = payload.get('mode')
    hero = payload.get('hero')
    difficulty = payload.get('difficulty', 'medium')
    if mode not in ('adventure', 'gauntlet') or hero not in CLASSES or difficulty not in DIFFICULTIES:
        raise ValueError('Choose a mode, hero and challenge level.')
    if not isinstance(payload.get('companion', False), bool):
        raise ValueError('Invalid companion choice.')
    if not isinstance(payload.get('skipIntro', False), bool):
        raise ValueError('Invalid introduction choice.')
    settings = dict(mode=mode, hero=hero, difficulty=difficulty, companion=payload.get('companion', False), name=language_filter.clean_name(payload.get('name', 'Adventurer')), title=language_filter.filter_text(str(payload.get('title', 'Oakvale adventure')))[:48].strip() or 'Oakvale adventure', skipIntro=payload.get('skipIntro', False))
    with world.lock:
        for room in world.rooms.values():
            creation = room.get('creation') or {}
            if creation.get('key') == token:
                previous = {**creation['settings']}
                previous.setdefault('skipIntro', False)
                if previous != settings:
                    raise ValueError('This retry belongs to a different creation request. Existing world is unchanged.')
                return (room['code'], creation['player'])
        if payload.get('instance') != instance:
            raise ValueError('The server restarted before this creation was confirmed. Review Continue, then create another request; no replacement world was made.')
        code, pid = world.create_room(settings['name'])
        room = world.rooms[code]
        room['creation'] = dict(key=token, player=pid, settings=settings)
        p = room['players'][pid]
        p['strictSession'] = True
        world._action(code, pid, dict(action='class', **{'class': hero}))
        world._action(code, pid, dict(action='runOptions', mode=mode, difficulty=difficulty, companion=settings['companion']))
        if mode == 'adventure':
            room['adventureTitle'] = settings['title']
            room['_skipOpening'] = settings['skipIntro']
            world._action(code, pid, dict(action='start'))
        return (code, pid)

def join(world, payload):
    from game import CLASSES, MAX_PLAYERS
    token = key(payload)
    hero = payload.get('hero')
    name = language_filter.clean_name(payload.get('name', 'Adventurer'))
    with world.lock:
        room = world.rooms.get(str(payload.get('room', '')).upper())
        if not room:
            raise ValueError('That party code was not found.')
        for p in room['players'].values():
            if p.get('joinRequestKey') == token:
                return (room['code'], p['id'])
        if hero not in CLASSES:
            raise ValueError('Choose a hero to join the party.')
        if any((p['class'] == hero for p in room['players'].values())):
            raise ValueError('That hero is already in the party. Choose another hero.')
        if len(room['players']) >= MAX_PLAYERS:
            raise ValueError('This party is full, including its companion.')
        if room['phase'] == 'lobby':
            code, pid = world.join_room(room['code'], name)
            world._action(code, pid, dict(action='class', **{'class': hero}))
            p = room['players'][pid]
        elif adventure.active(room) and (room['adventure']['current'] in __import__('region_content').HUBS or __import__('opening').active(room)) and (not room['adventure'].get('locked')):
            import secrets, progression
            pid = secrets.token_urlsafe(18)
            p = world._player(pid, name)
            p.update(**{'class': hero}, maxHp=CLASSES[hero]['hp'], hp=CLASSES[hero]['hp'], x=480, y=460, characterId=str(uuid.uuid4()))
            from game import ABILITY_SETS
            p['abilities'] = [ABILITY_SETS[hero][0][0], ABILITY_SETS[hero][2][0]]
            p['_freshHero'] = True
            room['players'][pid] = p
            progression.defaults(room)
            world._stock_shop(room, p)
            if __import__('opening').active(room):
                import time
                from opening import MUSTER
                anchor = next((a for a in room['players'].values() if a['id'] != pid and a['status'] == 'alive'), None)
                p.update(x=anchor['x'] if anchor else MUSTER[0], y=anchor['y'] if anchor else MUSTER[1], lastMove=time.monotonic())
            else:
                progression.inspect(p, 'Village Runner', 'You joined the party in ' + room['town'] + '. Journal recaps accepted assignments and reports. Speak to this village’s runner for the next step; the party shares world progress, while equipment and Magic Runes are personal.', 'npc')
                p['dialogue']['portrait'] = 'Villager02'
        else:
            raise ValueError('The party is exploring. Join when it returns to Oakvale or Dunmere, or use Continue for your existing character.')
        p.update(strictSession=True, joinRequestKey=token)
        if adventure.active(room):
            adventure.save(world, room)
        return (room['code'], pid)

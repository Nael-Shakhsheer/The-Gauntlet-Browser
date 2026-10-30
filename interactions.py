"""One server-owned nearby action for prompts, keyboard, mouse and touch."""
import math
import progression

def scene(room, p):
    value = ':'.join(map(str, (room['code'], room.get('adventure', {}).get('current', ''), room['phase'], p.get('townInterior') or '', p.get('innFloor', 1))))
    return value

def select(world, room, p):
    import adventure
    targets = []

    def add(key, kind, label, x, y, radius, priority, point=None, reason=None, hold=False):
        distance = math.hypot(p['x'] - x, p['y'] - y)
        if distance > radius:
            return
        if progression.locked(room, p):
            reason = 'Finish the current conversation first.'
        elif p['status'] != 'alive':
            reason = 'An ally must revive you first.'
        targets.append(dict(id=key, kind=kind, label=label, x=x, y=y, range=radius, distance=round(distance), available=not reason, reason=reason, hold=hold, priority=priority, point=point))
    if room['phase'] == 'combat' and p['status'] == 'alive':
        for ally in world._active_players(room):
            if ally['status'] == 'downed' and ally['id'] != p['id'] and (not ally.get('townInterior')):
                blocked = not __import__('combat_environment').line_clear(room, p, ally)
                add('revive:' + ally['id'], 'revive', 'Revive ' + ally['name'], ally['x'], ally['y'], 62, 0, reason='Move around the obstruction to reach your ally.' if blocked else None, hold=True)
    if room['phase'] == 'town':
        house = world._nearby_house(room, p)
        if house:
            x, y = (480, 450) if p.get('townInterior') else (house['doorX'], house['doorY'])
            add('door:' + house['id'], 'door', 'Return to village' if p.get('townInterior') else 'Enter ' + house['name'], x, y, 62 if p.get('townInterior') else 44, 1, house)
        npc = world._nearby_npc(room, p)
        if npc and (not (adventure.active(room) and npc['id'] == 'gate')):
            key = npc['id']
            kind = 'bed' if key.startswith('bed_') else 'stairs' if key.startswith('stairs_') else 'npc'
            label = 'Rest at ' + npc['name'] if kind == 'bed' else npc['name'] if kind == 'stairs' else 'Talk to ' + npc['name']
            reason = 'Occupied room; choose an unlocked room.' if key.startswith('locked_') else None
            add('npc:' + key, kind, label, npc['x'], npc['y'], 70, 2, npc, reason)
    if adventure.active(room) and (not p.get('townInterior')) and (room['phase'] != 'defeat'):
        exits = adventure.exits(room)
        exit_ids = {e['id'] for e in exits}
        for point in ([] if room['phase'] == 'puzzle' else adventure.features(room)) + exits:
            if point.get('kind') == 'dungeon_story':
                continue
            exit = point['id'] in exit_ids
            reason = point.get('reason')
            if point['id'] in ('kit', 'hunter') and (not adventure.clear_local(room)):
                reason = 'Defeat the nearby guards first; ordinary trails remain open.'
            label = ('Enter ' + point['dungeonEntrance']['name'] if point.get('dungeonEntrance') else 'Travel to ' + point['name']) if exit else point['name']
            if point.get('kind') == 'signpost':
                label = 'Read signpost'
            add(('exit:' if exit else 'feature:') + point['id'], 'trail' if exit else 'feature', label, point['x'], point['y'], 76 if point.get('dungeonEntrance') else 68, 5 if exit else 3, point, reason)
    if room['phase'] == 'puzzle' and room.get('puzzle'):
        chamber = room['puzzle'].get('rooms', {}).get(p['id'], {})
        totem = chamber.get('totem')
        if totem:
            add('totem', 'totem', 'Read your totem', totem['x'], totem['y'], 58, 2, totem)
    if not adventure.active(room):
        if room['phase'] == 'chest' and room.get('chest'):
            chest = room['chest']
            add('chest', 'chest', 'Open your chest', chest['x'], chest['y'], 62, 3, chest)
        elif room['phase'] == 'routes':
            route = world._near_route(room, p)
            if route:
                route = next((r for r in room['routes'] if r['id'] == route['id']))
                add('route:' + route['id'], 'route', 'Take ' + route['name'], route['x'], route['y'], 72, 5, route)
        elif room['phase'] == 'peace':
            add('hunter', 'hunter', 'Talk to wounded hunter', 480, 250, 70, 2)
    return min(targets, key=lambda t: (not t['available'], t['priority'], t['distance'], t['id']), default=None)

def public(world, room, p):
    target = select(world, room, p)
    return {k: v for k, v in target.items() if k not in ('point', 'priority')} if target else None

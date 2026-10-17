"""Public, transient cast choreography. Never delays or modifies combat rules."""
import secrets
import time


def record(room, player, ability, origin, target, recipient_ids, *, release_after=0.0, visual=None, facing=None):
    now = time.monotonic()
    attack_type = ability['attackType']
    duration = {'light': .46, 'special': .85, 'ultimate': 1.25}[attack_type]
    if ability['kind'] == 'summon':
        duration = 1.1 if attack_type == 'special' else 1.5
    duration=max(duration,release_after+.4)
    cast = dict(id=secrets.token_hex(6), abilityId=ability['id'], name=ability['name'],
                attackType=attack_type, kind=ability['kind'], ownerId=player['id'],
                heroClass=player['class'], stage=room['stage'], duration=duration, startedAt=now,
                facingX=facing[0] if facing else player.get('facingX', 0), facingY=facing[1] if facing else player.get('facingY', 1),
                recipientIds=recipient_ids,releaseAt=release_after,released=release_after==0,
                visual=visual or __import__('ability_visuals').describe(ability,player,origin,target))
    # Holding Light must not erase the pose of a longer Special/Ultimate.
    previous = player.get('abilityAnimation') or {}
    priority = {'light': 1, 'special': 2, 'ultimate': 3}
    active = (previous.get('stage') == room['stage'] and previous.get('heroClass') == player['class']
              and now < previous.get('startedAt', 0) + previous.get('duration', 0))
    if not active or priority[attack_type] >= priority.get(previous.get('attackType'), 0):
        player['abilityAnimation'] = cast
    room['effects'].append(dict(cast, type='ability_cast', x=origin[0], y=origin[1],
        targetX=target[0], targetY=target[1], color='', until=time.time()+duration,
        text='', **{'class': player['class']}))
    room['effects'] = room['effects'][-80:]
    return cast


def resolve(room, player, cast_id, now, *, cancelled=False, recipients=None):
    """Resolve BOTH copies of a committed pose; clients never invent a release."""
    records=[player.get('abilityAnimation') or {}]+room['effects']
    for record in records:
        if record.get('id')!=cast_id:continue
        record.update(cancelled=cancelled,released=not cancelled,releaseAt=max(0,now-record['startedAt']))
        if recipients is not None:record['recipientIds']=list(recipients)


def view(player, now, stage):
    cast = player.get('abilityAnimation')
    if not cast or cast.get('stage') != stage or cast.get('heroClass') != player.get('class') or player.get('status') != 'alive':
        return None
    elapsed = now - cast['startedAt']
    if not 0 <= elapsed < cast['duration']:
        return None
    return dict(cast, elapsed=elapsed, remaining=cast['duration']-elapsed)


def preparation(room, player, now):
    """Use only the last 140ms of an existing held-attack recharge as wind-up.

    A first click is immediate; presentation must never add attack latency.
    """
    if room['phase']!='combat' or player['status']!='alive' or not player.get('attacking') or room.get('waveStartsAt'):return 0
    from game import ABILITY_SETS
    import hero_skills
    entry=next((a for a in ABILITY_SETS.get(player['class'],[]) if a[7]=='light' and a[0] in player['abilities']),None)
    if not entry:return 0
    left=hero_skills.ready_at(player,entry[0])-now
    if not 0<left<=.14:return 0
    if not any(__import__('math').hypot(e['x']-player['x'],e['y']-player['y'])<=entry[5] for e in room['enemies']):return 0
    return round(left,3)

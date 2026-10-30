"""Opt-in seeded modifier schedule, separate from Adventure's permanent power."""
import hashlib


def current(room):
    if room.get('mode')=='adventure' or room.get('challengeMode','classic')!='seeded':return None
    seed=room.get('challengeSeed',0);stage=max(1,room.get('stage',0))
    index=hashlib.sha256(f'gauntlet-challenge-v1:{seed}:{stage}'.encode()).digest()[0]%2
    return dict(id=('pursuit','thin_air')[index],seed=seed,name=('Hunting packs','Thin air')[index],
        rules=('Ordinary enemies: +18% movement, -15% HP. Each kill awards 1 extra shared Rune.' if index==0 else 'Combat mana regeneration -25%. Each kill awards 1 extra shared Rune.'))


def prepare(room):
    modifier=current(room)
    if not modifier or modifier['id']!='pursuit':return
    for e in room['enemies']:
        if e.get('boss') or e.get('miniBoss') or e.get('_challengeApplied'):continue
        e.update(maxHp=max(1,round(e['maxHp']*.85)),hp=max(1,round(e['hp']*.85)),speed=e['speed']*1.18,_challengeApplied=True)


def mana_factor(room):
    modifier=current(room)
    return .75 if modifier and modifier['id']=='thin_air' else 1


def bonus(room):return int(current(room) is not None)

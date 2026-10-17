"""Repeatable NORMAL-stat encounter observations; no active server/private save use.

Fixed ordinary town kit: class weapon, Oakguard, one heal/mana/ward, no ranks or
stat boosts. Tactical bots are limited and do not measure human enjoyment.
python -B tools/chapter_probe.py --matrix --output reports/chapter-probe.json
"""
import argparse
import json
import math
from pathlib import Path
import random
import sys
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from game import GameWorld,ABILITY_SETS,CLASS_WEAPONS
import adventure,companion_ai,dungeons,chapter_observations as observations
import combat_environment as terrain


def probe(area,heroes=('Knight',),difficulty='medium',companion=False,seed=41,limit=180):
    now=[1000.0];random.seed(seed)
    ids_rng=random.Random(seed*9173)
    with patch('game.time.monotonic',side_effect=lambda:now[0]), \
         patch('game.secrets.token_urlsafe',side_effect=lambda n:format(ids_rng.getrandbits(n*8),'x')), \
         patch('game.secrets.token_hex',side_effect=lambda n:format(ids_rng.getrandbits(n*8),'x')), \
         patch('game.secrets.choice',side_effect=ids_rng.choice), \
         patch('game.secrets.randbelow',side_effect=ids_rng.randrange):
        w=GameWorld();code,host=w.create_room('Probe');ids=[host]+[w.join_room(code,'Probe')[1] for _ in heroes[1:]]
        for pid,hero in zip(ids,heroes):
            w.action(code,pid,dict(action='class',**{'class':hero}));w.action(code,pid,dict(action='loadout',abilities=[a[0] for a in ABILITY_SETS[hero][::2]]))
        r=w.rooms[code];r.update(mode='adventure',difficulty=difficulty,_skipOpening=True)
        w._configure_companion(r,companion);w.action(code,host,dict(action='start'))
        for p in r['players'].values():
            # This established benchmark uses the legacy three-skill kit at
            # ordinary stats, rather than representing a fresh Adventure hero.
            p.pop('heroProgress',None);p.pop('adventureLoadout',None)
            p['abilities']=[a[0] for a in ABILITY_SETS[p['class']][::2]]
            __import__('hero_skills').ensure(r,p)
            p['abilityCooldowns']={aid:now[0]+15 for aid in p['abilities'] if next(a[7] for a in ABILITY_SETS[p['class']] if a[0]==aid)=='ultimate'}
            p['dialogue']=None;p['toolSlots']=[w._make_item(CLASS_WEAPONS[p['class']]),w._make_item('oakguard_vest')]
            p['utilitySlots']=[w._make_item(k) for k in ('healing_draught','mana_draught','warding_tonic')]
        adventure.enter(w,r,area,'west' if area.startswith('cave') else 'south',initial=True)
        r['runes']=20;observations.enable(r)
        if area in ('cave_heart','tower_1','tower_2','tower_3'):
            f=next(f for f in dungeons.features(r) if f['id']=='dungeon_begin')
            for p in w._voting_players(r):p.update(x=f['x'],y=f['y'])
            dungeons.interact(w,r,r['players'][host],'dungeon_begin')
        outcome='timeout/abandoned'
        for _ in range(int(limit/.05)):
            for p in r['players'].values():
                if p.get('bot') or p['status']!='alive' or r['waveStartsAt']:continue
                fallen=next((a for a in r['players'].values() if a['status']=='downed'),None)
                if fallen:
                    dx,dy=fallen['x']-p['x'],fallen['y']-p['y'];dist=max(.001,math.hypot(dx,dy))
                    if dist<55:
                        if p.get('reviving')!=fallen['id']:w._revive(r,p)
                        p.update(dx=0,dy=0,attacking=False);continue
                    p.update(dx=dx/dist,dy=dy/dist,attacking=False);continue
                target=min(r['enemies'],key=lambda e:math.hypot(e['x']-p['x'],e['y']-p['y']),default=None)
                if not target:continue
                light=next(a for a in ABILITY_SETS[p['class']] if a[0]==p['abilities'][0])
                dx,dy=target['x']-p['x'],target['y']-p['y'];dist=max(.001,math.hypot(dx,dy))
                p.update(dx=dx/dist if dist>light[5]*.7 else 0,dy=dy/dist if dist>light[5]*.7 else 0,attacking=True)
                companion_ai.defensive_move(r,p,target,light[5],now[0])
                if not terrain.line_clear(r,p,target):
                    # Probe navigation, not a change to enemy/companion AI.
                    # One-bend detours around the tower's authored pillars.
                    candidates=[dict(x=x,y=y) for x,y in ((200,155),(200,350),(350,155),(350,350),(760,155),(760,350),(480,270))]
                    detours=[v for v in candidates if terrain.walkable(r,v['x'],v['y']) and terrain.line_clear(r,p,v) and terrain.line_clear(r,v,target)]
                    goal=min(detours,key=lambda v:math.dist((p['x'],p['y']),(v['x'],v['y']))+math.dist((v['x'],v['y']),(target['x'],target['y'])),default=dict(x=480,y=270))
                    dx,dy=goal['x']-p['x'],goal['y']-p['y'];dist=max(1,math.hypot(dx,dy));p.update(dx=dx/dist,dy=dy/dist)
                for slot in (1,2):
                    try:w.action(code,p['id'],dict(action='ability',slot=slot+1))
                    except ValueError:pass
                for item in list(p['utilitySlots']):
                    if item and ((item['kind']=='heal' and p['hp']<p['maxHp']*.5) or (item['kind']=='mana' and p['mana']<25) or (item['kind']=='ward' and p['hp']<p['maxHp']*.7 and p['wardUntil']<=now[0])):
                        try:w.action(code,p['id'],dict(action='useItem',item=item['id']))
                        except ValueError:pass
            observations.tick(r);now[0]+=.05;w.tick()
            if r['adventure']['current']=='home':outcome='wipe';break
            if not r['enemies'] and not r['waveStartsAt']:outcome='cleared';break
        if outcome!='cleared':observations.event(r,'abandoned',reason=outcome)
        report=observations.finish(r,outcome);report['seed']=seed;return report


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--matrix',action='store_true');parser.add_argument('--output',default='reports/chapter-probe.json');parser.add_argument('--location',default='tower_1');args=parser.parse_args()
    lineups=[(hero,) for hero in ABILITY_SETS]+[('Knight','Healer'),('Knight','Druid','Wizard'),('Knight','Druid','Archer','Healer')]
    cases=[(area,heroes,False) for area in ('road','cave_entry','cave_gallery','cave_heart','tower_1','tower_2','tower_3') for heroes in lineups] if args.matrix else [(args.location,('Knight',),False)]
    if args.matrix:cases+=[('tower_3',('Knight','Healer','Archer'),True)]
    results=[probe(a,h,companion=c) for a,h,c in cases];path=Path(args.output);path.parent.mkdir(exist_ok=True);path.write_text(json.dumps(results,indent=2),encoding='utf-8')
    print(json.dumps([dict(location=r['location'],classes=r['classes'],outcome=r['outcome'],seconds=r['duration'],downings=r['downings']) for r in results],indent=2))


if __name__=='__main__':main()

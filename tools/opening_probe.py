"""Ordinary starter-stat automated observations, NOT human balance evidence."""
import sys,json,math,random
from pathlib import Path
from unittest.mock import patch
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parents[1]/'tests')]
from test_opening import new
from game import CLASSES
import opening,combat_environment as terrain


def probe(heroes,companion=False):
    clock=[1000.0];random.seed(42)
    with patch('time.monotonic',side_effect=lambda:clock[0]):
        w,r,ps=new(heroes,companion=companion);casts=0;phases={};low=10000
        for frame in range(4200):
            clock[0]+=.05
            if not opening.active(r):break
            phase=r['_opening']['phase'];phases.setdefault(phase,round(clock[0]-1000,2))
            if r['_opening'].get('retry'):break
            for i,p in enumerate(ps):
                p['lastSeen']=clock[0];p['attacking']=True
                if p['status']!='alive':continue
                low=min(low,p['hp'])
                if phase=='withdrawal':goal=opening.MUSTER
                else:
                    e=min(r['enemies'],key=lambda e:math.dist((e['x'],e['y']),(p['x'],p['y'])),default=None)
                    if not e:p['dx']=p['dy']=0;continue
                    d=math.dist((e['x'],e['y']),(p['x'],p['y']));cat=__import__('hero_skills').catalog(p);reach=min(cat[p['abilities'][0]]['range']*.7,160)
                    if not terrain.line_clear(r,p,e):goal=(p['x'],550) if p['y']<505 else (e['x'],550)
                    elif d>reach:goal=(e['x'],e['y'])
                    else:
                        angle=(frame//36+i)*math.pi/4;goal=(p['x']+math.cos(angle)*50,p['y']+math.sin(angle)*50)
                    if frame%10==0:
                        try:w._cast_ability(r,p,1);casts+=1
                        except ValueError:pass
                dx,dy=goal[0]-p['x'],goal[1]-p['y'];length=max(1,math.hypot(dx,dy));p['dx'],p['dy']=(dx/length,dy/length) if length>15 else (0,0)
                p['lastInputAt']=clock[0]
            w._tick_room(r,clock[0])
        return dict(heroes=list(heroes),companion=companion,difficulty=r['difficulty'],kit='unmodified fresh starters; no gear, ranks, consumables or stat boosts',
            completed=not opening.active(r),seconds=round(clock[0]-1000,2),phaseTimes=phases,lowestHP=low,hp=[p['hp'] for p in ps],mana=[round(p['mana'],1) for p in ps],
            activeCasts=casts,runes=r['runes'],points=[__import__('hero_skills').points(p) for p in ps],retry=r.get('_opening',{}).get('retry',False))


if __name__=='__main__':
    rows=[probe((hero,)) for hero in CLASSES]+[probe(('Knight','Healer')),probe(('Knight','Healer','Bard')),probe(('Knight','Healer','Bard','Druid')),probe(('Healer',),True)]
    result=dict(label='Automated ordinary-stat starter controller; not human/physical-device playtesting',observations=rows)
    Path('reports/CARAVAN_ORDINARY_PROBES_2026-10-14.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    for row in rows:print(', '.join(row['heroes']),row['companion'],row['completed'],row['seconds'],row['hp'],row['runes'])

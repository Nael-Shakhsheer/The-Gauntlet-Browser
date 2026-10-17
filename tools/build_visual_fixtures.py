"""Disposable helper states for visual review; no private saves or balance claims."""
import copy,json,sys,tempfile,time
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
import run_storage
with tempfile.TemporaryDirectory(prefix='gauntlet-art-') as directory:
    original=run_storage.RunStorage.__init__
    with patch.object(run_storage.RunStorage,'__init__',lambda self,_path:original(self,Path(directory)/'singleton')):import game
    import adventure,ascension,chapter_flow,region_content,skill_casts,hero_skills,progression
    from test_expansion import start,report_chain
    from test_adventure import finish,interact
    fixtures={}
    w,r,ps=start(('Knight','Wizard','Druid','Healer'),directory=Path(directory)/'scenes');p=ps[0]
    def capture(key):fixtures[key]=copy.deepcopy(w.state(r['code'],p['id']))
    def area(key):
        adventure.enter(w,r,key,'south');finish(w,r,p)
        for i,m in enumerate(ps):m.update(x=380+i*65,y=400,dx=0,dy=0,dialogue=None)
    p['inventory']=[w._make_item(k) for k in ('healing_draught','mana_draught','arcane_conductor','wind_bow')]
    p['toolSlots']=[w._make_item('iron_sword'),w._make_item('oakguard_vest')]
    p['utilitySlots']=[w._make_item(k) for k in ('healing_draught','mana_draught','warding_tonic')]
    capture('village')
    for place in ['brook','mill_trail','watch','fields','mill','cellar','cave_gallery','tower_2']:
        area(place);capture(place)
    area('brook');f=next(f for f in region_content.features(r) if f['kind']=='travel_shrine');p.update(x=f['x'],y=f['y']+40)
    r['enemies']=[];region_content.interact(w,r,p,f);finish(w,r,p);capture('shrine-active')
    area('fields');f=next(f for f in region_content.features(r) if f['id']=='rooted_crop');p.update(x=f['x'],y=f['y']);region_content.interact(w,r,p,f);capture('object-inspection');finish(w,r,p)
    area('dunmere');report_chain(w,r,p,'chapter_outcome');finish(w,r,p);capture('dunmere')
    for m in ps:
        m['magicRunes'].update(ascended=True,balance=1);hero_skills.ensure(r,m)
    area('mill');r['enemies']=r['enemies'][:1];e=r['enemies'][0];e.update(x=650,y=400,hp=10000,maxHp=10000)
    r['environment']={'barriers':[],'obstacles':[],'zones':[]}
    for m in ps:ascension.cast(w,r,m,ascension.ability(m))
    capture('signatures-windup');due=max(c['releaseAt'] for c in r['ascensionCasts']);ascension.tick(w,r,due+.01)
    # Relative clocks are shifted only in this frozen review export, never simulation.
    for c in r['effects']:
        if c.get('type')=='ability_cast':c['startedAt']-=.65
    for m in ps:
        if m.get('abilityAnimation'):m['abilityAnimation']['startedAt']-=.65
    capture('signatures-release')
    r['effects']=[]
    for kind,hero,radius,x,y in [('banner',ps[0],150,220,260),('rift',ps[1],95,500,280),('spring',ps[2],130,780,260),('beacon',ps[3],160,1000,480)]:
        hero.update(x=x,y=y);skill_casts.zone(r,hero,kind,radius,6)
    capture('zones')
    # Representative actual shop, Skills/Ascension and room panels.
    area('dunmere');p['townInteraction']='merchant';capture('shop')
    # Separate ordinary Gauntlet setup and authoritative boss warning fixture.
    gw=game.GameWorld(storage_dir=Path(directory)/'waves');code,pid=gw.create_room('Visual wave');gr=gw.rooms[code]
    gw.action(code,pid,dict(action='class',**{'class':'Archer'}));gw.action(code,pid,dict(action='loadout',abilities=['piercing_volley','eagle_eye','deadeye']));fixtures['gauntlet-lobby']=gw.state(code,pid)
    gw.action(code,pid,dict(action='start'));fixtures['gauntlet-wave']=gw.state(code,pid)
    gr.update(stage=gr['bossStages'][0],stageWave=gr['stageWaves'],enemies=[]);gw._spawn_large_boss(gr)
    boss=gr['enemies'][0];player=gr['players'][pid];boss.update(x=500,y=210);player.update(x=350,y=390)
    gw._tick_enemy(gr,boss,player,time.monotonic()+.1);fixtures['gauntlet-boss']=gw.state(code,pid)
    gr['phase']='defeat';fixtures['defeat']=gw.state(code,pid)
    gr['phase']='cleared';fixtures['victory']=gw.state(code,pid)
    target=ROOT/'art/visual-quality-v3/review/fixtures.json';target.write_text(json.dumps(dict(label=__doc__,states=fixtures)),encoding='utf-8')
    print('Exported '+str(len(fixtures))+' explicitly helper-prepared states.')

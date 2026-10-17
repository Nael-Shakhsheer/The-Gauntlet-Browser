import copy
import json
import math
from pathlib import Path
import tempfile
import time
import unittest
import adventure
import dungeons
import boss_ai
import combat_environment as terrain
from game import GameWorld
from game import ABILITY_SETS
from test_adventure import party,travel,interact,kill


def begin(w,r,ps):
    f=next(f for f in adventure.features(r) if f['id']=='dungeon_begin')
    for p in w._voting_players(r):p.update(x=f['x'],y=f['y'])
    interact(w,r,ps[0],'dungeon_begin')


def clear_floor(w,r,ps):
    begin(w,r,ps)
    while r['adventure']['locked']:
        kill(w,r,ps[0])
        if r['waveStartsAt']:
            r['waveStartsAt']=time.monotonic()-1;w.tick()


class DungeonTests(unittest.TestCase):
    def test_cave_retreat_optional_branch_and_permanent_exit_do_not_complete_hunter(self):
        w,r,ps=party();travel(w,r,'road');travel(w,r,'cave_entry')
        self.assertTrue(r['enemies']);interact(w,r,ps[0],'cave_supplies')
        money=r['runes'];travel(w,r,'road');travel(w,r,'cave_entry')
        self.assertEqual(r['runes'],money);self.assertNotIn('cave_supplies',[f['id'] for f in adventure.features(r)])
        travel(w,r,'cave_gallery');self.assertTrue(r['enemies']);travel(w,r,'cave_cache')
        interact(w,r,ps[0],'cave_survey');self.assertTrue(dungeons.view(r)[0]['surveyFound'])
        travel(w,r,'cave_gallery');travel(w,r,'cave_heart')
        self.assertTrue(next(e for e in adventure.exits(r) if e['id']=='clearing')['locked'])
        begin(w,r,ps)
        with self.assertRaises(ValueError):travel(w,r,'cave_gallery')
        kill(w,r,ps[0]);self.assertTrue(dungeons.state(r)['routeOpen']);travel(w,r,'clearing')
        self.assertEqual(r['adventure']['quests']['hunter'],'active');self.assertFalse(r['adventure']['bridge'])
        travel(w,r,'cave_heart');self.assertFalse(r['enemies']);self.assertNotIn('dungeon_begin',[f['id'] for f in adventure.features(r)])

    def test_three_floors_finite_waves_manual_advancement_and_far_bridge_bank(self):
        w,r,ps=party();travel(w,r,'road');travel(w,r,'crossroads');travel(w,r,'camp');travel(w,r,'tower_1')
        with self.assertRaises(ValueError):travel(w,r,'tower_2')
        for floor in (1,2,3):
            clear_floor(w,r,ps)
            self.assertEqual(r['adventure']['current'],'tower_'+str(floor))
            self.assertIn(floor,dungeons.state(r)['completedFloors'])
            self.assertFalse(r['chest']);self.assertEqual(r['townsVisited'],0)
            if floor<3:travel(w,r,'tower_'+str(floor+1))
        before=r['runes'];travel(w,r,'bridge')
        self.assertGreater(ps[0]['x'],adventure.BRIDGE_LAYOUT['river']['right'])
        self.assertFalse(r['adventure']['bridge']);travel(w,r,'tower_3');travel(w,r,'tower_2');travel(w,r,'tower_1');travel(w,r,'camp')
        self.assertEqual(r['runes'],before)
        self.assertEqual(len(r['adventure']['dungeons']['tower']['completedEncounters']),5)

    def test_floor_retreat_cleared_enemies_never_return(self):
        w,r,ps=party();adventure.enter(w,r,'tower_1','west',source='camp');clear_floor(w,r,ps)
        adventure.track(w,r,ps[0],'tower')
        self.assertEqual(adventure.tracking(r,ps[0])['nextExit'],'tower_2')
        self.assertEqual(next(e for e in adventure.exits(r) if e['id']=='tower_2')['name'],'Briarwatch · Floor 2')
        travel(w,r,'camp');travel(w,r,'tower_1')
        self.assertFalse(r['enemies']);self.assertFalse(dungeons.features(r));travel(w,r,'tower_2')
        travel(w,r,'tower_1');travel(w,r,'camp')

    def test_scaling_safe_ordinary_arrivals_and_roles_one_to_four(self):
        for n in (1,2,3,4):
            w,r,ps=party(tuple(['Knight','Druid','Wizard','Healer'][:n]))
            for area in ('cave_entry','cave_gallery','cave_cache'):
                adventure.enter(w,r,area,'west');self.assertGreaterEqual(len(r['enemies']),3)
                self.assertGreaterEqual(len({e['combatRole'] for e in r['enemies']}),2)
                for e in r['enemies']:
                    self.assertTrue(terrain.walkable(r,e['x'],e['y']))
                    for dest,edge,_ in adventure.AREAS[area]['exits']:
                        x,y=adventure.edge_point(r,edge,True,dest)
                        for offset in (-30,-10,10,30):
                            self.assertGreater(math.dist((e['x'],e['y']),(x+offset,y)),195)
            adventure.enter(w,r,'tower_1','west');begin(w,r,ps)
            self.assertEqual(len(r['enemies']),n+2)
            kill(w,r,ps[0])
            for p,(x,y) in zip(ps,((365,145),(437,145),(509,145),(581,145))):p.update(x=x,y=y)
            r['waveStartsAt']=time.monotonic()-1;w.tick()
            for e in r['enemies']:
                self.assertTrue(terrain.walkable(r,e['x'],e['y']))
                self.assertTrue(all(math.dist((e['x'],e['y']),(p['x'],p['y']))>=85 for p in ps))

    def test_companion_offline_gather_reconnect_host_and_pause(self):
        w,r,ps=party(('Knight','Druid'),companion=True);travel(w,r,'road')
        e=next(e for e in adventure.exits(r) if e['id']=='cave_entry');ps[0].update(x=e['x'],y=e['y'])
        adventure.travel(w,r,ps[0],'cave_entry');self.assertEqual(r['adventure']['current'],'road')
        w._disconnect_player(r,ps[1]);adventure.tick_travel(w,r)
        self.assertEqual(r['adventure']['current'],'cave_entry')
        snapshot=w.state(r['code'],ps[1]['id']);self.assertEqual(snapshot['adventure']['area'],'cave_entry')
        self.assertTrue(terrain.walkable(r,ps[1]['x'],ps[1]['y']))
        w._disconnect_player(r,ps[0]);w._update_presence(r,time.monotonic());self.assertEqual(r['host'],ps[1]['id'])
        w._disconnect_player(r,ps[1]);before=copy.deepcopy(r['enemies']);w.tick();self.assertEqual(r['enemies'],before)

    def test_walls_block_dash_projectiles_targeting_and_ai(self):
        w,r,ps=party(('Wizard',));adventure.enter(w,r,'cave_entry','west');p=ps[0]
        p.update(x=220,y=110);e=r['enemies'][0];e.update(x=370,y=110)
        self.assertFalse(terrain.line_clear(r,p,e))
        terrain.move(r,p,420,110);self.assertLess(p['x'],250)
        w._launch_projectile(r,side='hero',owner_id=p['id'],target_id=e['id'],x=p['x'],y=p['y'],damage=999,color='#fff',attack_class='Wizard',speed=500)
        hp=e['hp'];w._tick_projectiles(r,time.monotonic()+.6)
        self.assertEqual(e['hp'],hp);self.assertFalse(r['projectiles'])
        self.assertIsNotNone(terrain.shot_block(r,200,110,400,110))
        self.assertTrue(terrain.ground_clear(r,108,270,852,270))

    def test_solid_landmark_footprints_preserve_tent_and_arch_openings_and_old_caches(self):
        w,r,ps=party();p=ps[0];adventure.enter(w,r,'camp','west')
        self.assertFalse(terrain.walkable(r,227,210));self.assertTrue(terrain.walkable(r,267,222))
        p.update(x=267,y=265);terrain.move(r,p,267,150)
        self.assertGreater(p['y'],200);self.assertLess(p['y'],235)
        self.assertFalse(terrain.line_clear(r,dict(x=190,y=210),dict(x=240,y=210)))
        adventure.capture(r);r['adventure']['areas']['camp']['environment'].pop('barriers')
        adventure.enter(w,r,'home','south',initial=True);adventure.enter(w,r,'camp','west')
        self.assertFalse(terrain.walkable(r,227,210),'Old cached areas receive the same solid footprints')
        adventure.enter(w,r,'ruins','north')
        self.assertTrue(terrain.ground_clear(r,480,108,480,400))
        self.assertFalse(terrain.walkable(r,447,225));self.assertFalse(terrain.walkable(r,530,225))
        p.update(x=410,y=225);terrain.move(r,p,490,225);self.assertLess(p['x'],437)

    def test_travel_carries_cooldown_health_mana_and_discards_foreign_shots(self):
        w,r,ps=party(('Druid',));travel(w,r,'road');p=ps[0]
        now=time.monotonic();p.update(hp=27,mana=19,abilityCooldowns={'fire_wolf':now+8,'ice_bear':now+15},dashCooldownUntil=now+2)
        r['projectiles']=[{'id':'old'}];travel(w,r,'cave_entry');travel(w,r,'road');travel(w,r,'cave_entry')
        self.assertEqual((p['hp'],p['mana']),(27,19));self.assertEqual(p['abilityCooldowns']['ice_bear'],now+15)
        self.assertEqual(p['dashCooldownUntil'],now+2);self.assertFalse(r['projectiles'])
        p.update(abilityCooldowns={},mana=100)
        w.action(r['code'],p['id'],dict(action='ability',slot=2))
        self.assertTrue(r['summons']);travel(w,r,'cave_gallery')
        self.assertFalse(r['summons']);self.assertFalse(p['activeSummons'])
        recharge=p['abilityCooldowns']['lightning_bird'];self.assertGreater(recharge-time.monotonic(),7)
        travel(w,r,'cave_entry');self.assertEqual(p['abilityCooldowns']['lightning_bird'],recharge)
        with self.assertRaises(ValueError):w.action(r['code'],p['id'],dict(action='ability',slot=2))

    def test_sealed_wave_restart_is_full_and_kill_runes_are_not_paid_twice(self):
        with tempfile.TemporaryDirectory() as directory:
            w,r,ps=party(storage_dir=directory);adventure.enter(w,r,'tower_1','west');begin(w,r,ps)
            ids={e['id'] for e in r['enemies']};first=r['enemies'][0]['id'];w._damage_enemy(r,ps[0],r['enemies'][0],99999)
            money=r['runes'];remaining=len(r['enemies'])
            restarted=GameWorld(storage_dir=directory);rr=restarted.rooms[r['code']];rp=rr['players'][ps[0]['id']]
            restarted.state(rr['code'],rp['id']);self.assertEqual(rr['adventure']['current'],'home')
            adventure.enter(restarted,rr,'tower_1','west');self.assertFalse(rr['enemies']);begin(restarted,rr,[rp])
            self.assertEqual({e['id'] for e in rr['enemies']},ids);self.assertGreater(len(rr['enemies']),remaining)
            e=next(e for e in rr['enemies'] if e['id']==first);restarted._damage_enemy(rr,rp,e,99999)
            self.assertEqual(rr['runes'],money)

    def test_completed_waves_survive_wipe_and_restart_penalty_once(self):
        with tempfile.TemporaryDirectory() as directory:
            w,r,ps=party(storage_dir=directory);adventure.enter(w,r,'tower_1','west');begin(w,r,ps);kill(w,r,ps[0])
            self.assertEqual(dungeons.state(r)['attempt']['wave'],2)
            r['runes']=100;ps[0].update(status='downed',hp=0);w._check_party_wipe(r)
            self.assertEqual(r['runes'],60);self.assertFalse(w._check_party_wipe(r));self.assertEqual(r['runes'],60)
            restarted=GameWorld(storage_dir=directory);rr=restarted.rooms[r['code']];rp=rr['players'][ps[0]['id']]
            restarted.state(rr['code'],rp['id']);adventure.enter(restarted,rr,'tower_1','west');begin(restarted,rr,[rp])
            self.assertEqual(rr['stageWave'],2);self.assertEqual(rr['runes'],60)
            self.assertTrue(all('-w2-' in e['id'] for e in rr['enemies']))

    def test_old_v1_extension_and_unsupported_records_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            w,r,ps=party(storage_dir=directory);path=w.storage.adventure_paths[r['adventure']['worldId']]
            doc=json.loads(path.read_text());doc['room']['world'].pop('dungeons');path.write_text(json.dumps(doc));before=path.read_bytes()
            restored=GameWorld(storage_dir=directory);self.assertIn(r['code'],restored.rooms);self.assertEqual(path.read_bytes(),before)
            doc['room']['world']['dungeons']={'cave':dict(version=99,type='underground')};path.write_text(json.dumps(doc));before=path.read_bytes()
            with self.assertLogs(level='ERROR'):bad=GameWorld(storage_dir=directory)
            self.assertNotIn(r['code'],bad.rooms);self.assertEqual(path.read_bytes(),before)
        # Legacy Gauntlet records may explicitly contain a null Adventure field.
        w=GameWorld();code,pid=w.create_room('Legacy');_,other=w.join_room(code,'Second')
        for player,hero in ((pid,'Knight'),(other,'Druid')):
            w.action(code,player,dict(action='class',**{'class':hero}))
            w.action(code,player,dict(action='loadout',abilities=[a[0] for a in ABILITY_SETS[hero][::2]]))
        w.action(code,pid,dict(action='start'));r=w.rooms[code];r['adventure']=None
        a,b=r['players'][pid],r['players'][other];a.update(x=100,y=270);b.update(x=125,y=270)
        before=b['hp'];now=time.monotonic();e=r['enemies'][0]
        w._launch_projectile(r,side='enemy',owner_id=e['id'],target_id=pid,x=70,y=270,damage=1,color='#fff',attack_class='Boss',speed=400,splash=80)
        w._tick_projectiles(r,now+.12);self.assertLess(b['hp'],before)
        boss_ai.area(r,e,100,270,now,radius=80,delay=.05,duration=1,power=.1)
        before=b['hp'];boss_ai.tick_areas(w,r,now+.1);self.assertLess(b['hp'],before)

    def test_full_pouch_treasure_and_boss_reward_once(self):
        w,r,ps=party(('Healer',));p=ps[0];p['inventory']=[w._make_item('mana_draught') for _ in range(10)]
        adventure.enter(w,r,'cave_cache','south');interact(w,r,p,'cave_survey');money=r['runes']
        dungeons.interact(w,r,p,'cave_survey');self.assertEqual(r['runes'],money)
        adventure.enter(w,r,'cave_heart','west');begin(w,r,ps);kill(w,r,p)
        self.assertEqual(len(p['inventory']),10);receipt=r['adventure']['rewardHistory'][-1]
        self.assertEqual(receipt['title'],'Rootwater passage')
        self.assertIn('dungeon:cave',p['pendingRewards'])
        w.action(r['code'],p['id'],dict(action='adventureReward',reward='dungeon:cave',item='phoenix_flask',delivery='sell'))
        self.assertGreater(receipt['recipients'][0]['convertedRunes'],0)
        before=r['runes'];adventure.enter(w,r,'cave_heart','west');self.assertFalse(r['enemies']);self.assertEqual(r['runes'],before)

    def test_completed_dungeons_and_existing_world_facts_survive_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            w,r,ps=party(('Knight','Druid'),storage_dir=directory);p=ps[0]
            adventure.enter(w,r,'cave_entry','west');interact(w,r,p,'cave_supplies');kill(w,r,p)
            travel(w,r,'cave_gallery');kill(w,r,p);travel(w,r,'cave_cache');interact(w,r,p,'cave_survey');kill(w,r,p)
            travel(w,r,'cave_gallery');travel(w,r,'cave_heart');begin(w,r,ps);kill(w,r,p)
            adventure.enter(w,r,'tower_1','west')
            for floor in (1,2,3):
                clear_floor(w,r,ps)
                if floor<3:travel(w,r,'tower_'+str(floor+1))
            r['adventure']['bridge']=True
            for key in ('hunter','bridge','shrine'):r['adventure']['quests'][key]='complete'
            adventure.save(w,r);money=r['runes'];inventories=[copy.deepcopy(m['inventory']) for m in ps]
            restart=GameWorld(storage_dir=directory);rr=restart.rooms[r['code']]
            rps=[rr['players'][m['id']] for m in ps]
            for m in rps:restart.state(rr['code'],m['id'])
            self.assertEqual(rr['adventure']['current'],'home')
            self.assertTrue(rr['adventure']['bridge']);self.assertTrue(adventure.view(restart,rr,rps[0])['hunterHome'])
            self.assertTrue(adventure.view(restart,rr,rps[0])['shrineRestored'])
            for area in ('cave_entry','cave_gallery','cave_cache','cave_heart','tower_1','tower_2','tower_3'):
                adventure.enter(restart,rr,area,'west');self.assertFalse(rr['enemies'])
                self.assertFalse([f for f in dungeons.features(rr) if f['kind']!='dungeon_story'])
            for key in ('cave','tower'):self.assertTrue(rr['adventure']['dungeons'][key]['routeOpen'])
            self.assertEqual(rr['runes'],money);self.assertEqual([m['inventory'] for m in rps],inventories)

    def test_tracking_fog_and_location_danger_do_not_inherit_campaign_pressure(self):
        w,r,ps=party();p=ps[0]
        with self.assertRaises(ValueError):adventure.track(w,r,p,'tower')
        travel(w,r,'road');adventure.track(w,r,p,'cave')
        self.assertEqual(adventure.tracking(r,p)['nextExit'],'cave_entry')
        a=adventure.view(w,r,p);self.assertEqual([n['id'] for n in a['dungeons'][0]['nodes']],['cave_entry'])
        travel(w,r,'cave_entry');a=adventure.view(w,r,p)
        self.assertNotIn('cave_heart',[n['id'] for n in a['dungeons'][0]['nodes']])
        self.assertNotIn('clearing',a['dungeons'][0]['entrances'])
        original=[(e['id'],e['hp'],e['damage']) for e in r['enemies']]
        r.update(townsVisited=40,routePressure=99,totalStages=9,bossStages=[4],miniBossStages=[4])
        travel(w,r,'road');travel(w,r,'cave_entry')
        self.assertEqual([(e['id'],e['hp'],e['damage']) for e in r['enemies']],original)
        self.assertEqual(r['stage'],4);self.assertEqual(r['adventure']['current'],'cave_entry')

    def test_walls_block_area_attacks_summons_and_boss_windups_and_charge(self):
        w,r,ps=party(('Wizard','Druid'));p,druid=ps
        adventure.enter(w,r,'cave_entry','west');p.update(x=230,y=110,abilities=['arc_burst','spell_surge','arcane_cataclysm'],abilityCooldowns={})
        enemy=r['enemies'][0];enemy.update(x=360,y=110)
        r['enemies']=[enemy];hp=enemy['hp']
        with self.assertRaises(ValueError):w._cast_ability(r,p,2)
        self.assertEqual(enemy['hp'],hp)
        druid.update(x=230,y=110);w._summon_companion(r,druid,'fire_wolf',999,time.monotonic())
        summon=r['summons'][0];summon.update(x=230,y=110,lastAttack=0,lastTick=time.monotonic()-.1)
        w._tick_summons(r,time.monotonic());self.assertTrue(terrain.walkable(r,summon['x'],summon['y']));self.assertEqual(enemy['hp'],hp)
        adventure.enter(w,r,'tower_3','south');begin(w,r,ps)
        boss=r['enemies'][0];p.update(x=320,y=180);boss.update(x=190,y=180,nextBossAttack=0)
        boss_ai.tick(w,r,boss,p,time.monotonic(),.1);self.assertNotIn('pendingAttack',boss)
        now=time.monotonic();boss.update(chargeUntil=now+1,chargeVx=300,chargeVy=0,chargeHits=[])
        boss_ai.tick(w,r,boss,p,now,.2)
        self.assertLess(boss['x'],225);self.assertGreater(boss['vulnerableUntil'],now)
        self.assertTrue(terrain.walkable(r,boss['x'],boss['y']))

    def test_cooldowns_and_full_arena_survive_interrupted_boss_recovery(self):
        with tempfile.TemporaryDirectory() as directory:
            w,r,ps=party(('Druid',),storage_dir=directory);p=ps[0]
            adventure.enter(w,r,'cave_heart','west');begin(w,r,ps)
            now=time.monotonic();p.update(abilityCooldowns={'lightning_bird':now+6},dashCooldownUntil=now+4)
            w._summon_companion(r,p,'ice_bear',10,now)
            for cover in r['environment']['obstacles']:cover['hp']=0
            adventure.save(w,r)
            restart=GameWorld(storage_dir=directory);rr=restart.rooms[r['code']];rp=rr['players'][p['id']]
            self.assertGreater(rp['abilityCooldowns']['ice_bear']-time.monotonic(),14)
            self.assertGreater(rp['abilityCooldowns']['lightning_bird']-time.monotonic(),5)
            self.assertGreater(rp['dashCooldownUntil']-time.monotonic(),3)
            restart.state(rr['code'],rp['id']);adventure.enter(restart,rr,'cave_heart','west')
            self.assertTrue(all(o['hp']==o['maxHp'] for o in rr['environment']['obstacles']))
            begin(restart,rr,[rp]);self.assertEqual(rr['enemies'][0]['hp'],rr['enemies'][0]['maxHp'])

    def test_full_party_with_companion_finishes_without_bot_votes_or_false_disconnect_deaths(self):
        w,r,ps=party(('Knight','Druid','Wizard'),companion=True)
        adventure.enter(w,r,'tower_1','west');begin(w,r,ps)
        self.assertEqual(len(r['enemies']),6)
        for p in ps:w._disconnect_player(r,p)
        bodies=copy.deepcopy(r['enemies']);w.tick()
        self.assertEqual(r['enemies'],bodies);self.assertTrue(r['adventure']['locked'])
        self.assertEqual(r['adventure']['wipeCount'],0);self.assertFalse(dungeons.state(r)['completedFloors'])
        for p in ps:w.state(r['code'],p['id'])
        self.assertTrue(all(p['status']=='alive' for p in ps))
        kill(w,r,ps[0]);r['waveStartsAt']=time.monotonic()-1;w.tick();kill(w,r,ps[0])
        for floor in (2,3):
            travel(w,r,'tower_'+str(floor));clear_floor(w,r,ps)
        self.assertTrue(dungeons.state(r)['routeOpen']);self.assertEqual(dungeons.state(r)['completedFloors'],[1,2,3])
        self.assertFalse(w._tick_errors)


if __name__=='__main__':unittest.main()

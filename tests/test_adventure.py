"""Disposable parties verify the complete route and transactional world facts."""
import copy
import json
import math
from pathlib import Path
import tempfile
import time
import unittest

import adventure
import progression
from game import GameWorld, ABILITY_SETS


def finish(world,room,player):
    while player.get('dialogue'):
        d=player['dialogue'].copy()
        world.action(room['code'],player['id'],dict(action='dialogueNext',id=d['id'],page=d['page']))


def party(heroes=('Knight',),storage_dir=None,companion=False):
    world=GameWorld(storage_dir=storage_dir)
    code,host=world.create_room('Explorer')
    ids=[host]+[world.join_room(code,'Friend '+str(i))[1] for i in range(len(heroes)-1)]
    for pid,hero in zip(ids,heroes):
        world.action(code,pid,{'action':'class','class':hero})
        world.action(code,pid,{'action':'loadout','abilities':[a[0] for a in ABILITY_SETS[hero][::2]]})
    world.action(code,host,dict(action='runOptions',mode='adventure',companion=companion))
    world.rooms[code].update(_skipOpening=True,_legacyChapter=True) # Pre-sequential woodland compatibility fixture.
    world.action(code,host,dict(action='start'))
    room=world.rooms[code]
    for p in world._voting_players(room):finish(world,room,p)
    return world,room,[room['players'][pid] for pid in ids]


def travel(world,room,target):
    e=next(e for e in adventure.exits(room) if e['id']==target)
    for p in world._voting_players(room):p.update(x=e['x'],y=e['y'],townInterior=None)
    for p in list(world._voting_players(room)):
        world.action(room['code'],p['id'],dict(action='adventureTravel',destination=target))


def interact(world,room,player,key,complete=True):
    f=next(f for f in adventure.features(room) if f['id']==key)
    player.update(x=f['x'],y=f['y'])
    world.action(room['code'],player['id'],dict(action='interact'))
    if complete:finish(world,room,player)


def read_sign(world,room,player):
    f=next(f for f in adventure.features(room) if f['id']=='sign')
    player.update(x=f['x'],y=f['y'])
    world.action(room['code'],player['id'],dict(action='interact'));finish(world,room,player)


def kill(world,room,player):
    for e in list(room['enemies']):world._damage_enemy(room,player,e,99999)


def shrine(world,room,player):
    interact(world,room,player,'altar')
    for p in world._voting_players(room):
        chamber=room['puzzle']['rooms'][p['id']]
        rune=next(r for r in chamber['runes'] if r['rune']==chamber['target'])
        p.update(x=rune['x'],y=rune['y'])
    world._tick_puzzle(room)
    kill(world,room,player)


class AdventureTests(unittest.TestCase):
    def test_atomic_ability_choices_preserve_other_categories(self):
        w=GameWorld();c,p=w.create_room('Fast choices')
        w.action(c,p,{'action':'class','class':'Knight'})
        expected=[a[0] for a in ABILITY_SETS['Knight'][::2]]
        for aid in expected:w.action(c,p,dict(action='chooseAbility',ability=aid))
        self.assertEqual(w.rooms[c]['players'][p]['abilities'],expected)
        w.action(c,p,dict(action='chooseAbility',ability=expected[1]))
        self.assertEqual(w.rooms[c]['players'][p]['abilities'],[expected[0],expected[2]])
        with self.assertRaises(ValueError):w.action(c,p,dict(action='chooseAbility',ability=[]))

    def test_save_failure_is_reported_and_success_clears_it(self):
        with tempfile.TemporaryDirectory() as directory:
            w,r,ps=party(storage_dir=directory);prior=r['adventure']['savedAt']
            from unittest.mock import patch
            with patch.object(w.storage,'save_adventure',side_effect=OSError('Disk full')):
                with self.assertLogs(level='ERROR'):adventure.save(w,r)
            self.assertEqual(r['adventure']['savedAt'],prior)
            self.assertIn('failed',w.state(r['code'],ps[0]['id'])['adventure']['saveError'])
            adventure.save(w,r);self.assertNotIn('saveError',r['adventure'])

    def test_unsupported_save_is_preserved_and_not_restored(self):
        with tempfile.TemporaryDirectory() as directory:
            w,r,ps=party(storage_dir=directory)
            path=w.storage.adventure_paths[r['adventure']['worldId']]
            record=json.loads(path.read_text(encoding='utf-8'));record['version']=99
            path.write_text(json.dumps(record),encoding='utf-8');original=path.read_bytes()
            with self.assertLogs(level='ERROR'):restart=GameWorld(storage_dir=directory)
            self.assertNotIn(r['code'],restart.rooms);self.assertEqual(path.read_bytes(),original)

    def test_corrupt_record_does_not_install_a_partial_room(self):
        with tempfile.TemporaryDirectory() as directory:
            w,r,ps=party(storage_dir=directory)
            path=w.storage.adventure_paths[r['adventure']['worldId']]
            record=json.loads(path.read_text(encoding='utf-8'))
            del record['room']['world']['areas']['home']['enemies']
            path.write_text(json.dumps(record),encoding='utf-8');original=path.read_bytes()
            with self.assertLogs(level='ERROR'):restart=GameWorld(storage_dir=directory)
            self.assertEqual(restart.rooms,{})
            self.assertEqual(path.read_bytes(),original)

    def test_full_pouch_converts_reward_once_and_downed_interaction_is_rejected(self):
        w,r,ps=party();p=ps[0];p['inventory']=[w._make_item('healing_draught') for _ in range(10)]
        from game import ITEMS
        before=r['runes'];self.assertTrue(adventure.reward(w,r,'hunter',20,'healing_draught'))
        self.assertEqual(r['runes'],before+20+ITEMS['healing_draught']['sell'])
        self.assertFalse(adventure.reward(w,r,'hunter',20,'healing_draught'))
        self.assertEqual(len(p['inventory']),10)
        travel(w,r,'road');f=adventure.features(r)[0];p.update(x=f['x'],y=f['y'],status='downed',hp=0)
        with self.assertRaises(ValueError):w.action(r['code'],p['id'],dict(action='interact'))
    def test_graph_bidirectional_connected_and_has_loop(self):
        seen={'home'}; frontier=['home']
        while frontier:
            area=frontier.pop()
            for target,edge,reverse in adventure.AREAS[area]['exits']:
                self.assertIn((area,reverse,edge),adventure.AREAS[target]['exits'])
                if target not in seen:seen.add(target);frontier.append(target)
        self.assertEqual(seen,set(adventure.AREAS)-{'caravan'}) # One-shot defence transitions into home; no return/farming route.
        self.assertGreater(sum(len(a['exits']) for a in adventure.AREAS.values())//2,len(seen)-1)

    def test_home_quest_npcs_accessible_across_shuffled_villages(self):
        import town_layout
        for seed in range(80):
            room=dict(adventure={'current':'home','quests':{'hunter':'complete'}})
            room.update(town_layout.generate(seed))
            for i in range(4):self.assertTrue(GameWorld._town_walkable(room,480+(i-1.5)*42,460))
            npcs=adventure.features(room)
            for npc in npcs:self.assertTrue(GameWorld._town_walkable(room,npc['x'],npc['y']))
            self.assertGreater(math.dist((npcs[0]['x'],npcs[0]['y']),(npcs[1]['x'],npcs[1]['y'])),159)

    def test_two_area_loop_preserves_layout_damage_and_kills(self):
        w,r,ps=party();p=ps[0];layout=copy.deepcopy(r['townLayout'])
        travel(w,r,'road');foes=copy.deepcopy(r['enemies']);env=copy.deepcopy(r['environment'])
        w._damage_enemy(r,p,r['enemies'][0],99999)
        w._damage_enemy(r,p,r['enemies'][0],5)
        hp=r['enemies'][0]['hp'];money=r['runes']
        travel(w,r,'home');self.assertEqual(r['townLayout'],layout)
        travel(w,r,'road');self.assertEqual(len(r['enemies']),len(foes)-1)
        self.assertEqual(r['enemies'][0]['hp'],hp);self.assertEqual(r['runes'],money)
        self.assertEqual(r['environment'],env)
        self.assertEqual(r['phase'],'combat');self.assertFalse(r['waveStartsAt'])

    def test_enemy_roles_stay_fixed_when_support_is_defeated_and_area_revisited(self):
        w,r,ps=party(('Knight','Druid'));p=ps[0];travel(w,r,'road')
        support=next(e for e in r['enemies'] if e['combatRole']=='support')
        w._damage_enemy(r,p,support,99999)
        roles={e['id']:(e['class'],e['combatRole']) for e in r['enemies']}
        travel(w,r,'home');travel(w,r,'road')
        self.assertEqual(roles,{e['id']:(e['class'],e['combatRole']) for e in r['enemies']})

    def test_projectiles_draw_territorial_aggression_without_extending_pursuit(self):
        w,r,ps=party(('Wizard',));p=ps[0];travel(w,r,'road');e=r['enemies'][0]
        p.update(x=e['homeX']-200,y=e['homeY']);w._damage_enemy(r,p,e,1)
        self.assertTrue(e['aggro'])
        p['x']=e['homeX']-300
        self.assertTrue(adventure.leash(w,r,e,p,time.monotonic()))
        self.assertFalse(e['aggro'])

    def test_gather_requires_present_humans_but_not_bot_or_offline(self):
        w,r,ps=party(('Knight','Druid'),companion=True);e=adventure.exits(r)[0]
        ps[0].update(x=e['x'],y=e['y'])
        w.action(r['code'],ps[0]['id'],dict(action='adventureTravel',destination='road'))
        self.assertEqual(r['adventure']['current'],'home')
        w._disconnect_player(r,ps[1]);adventure.tick_travel(w,r)
        self.assertEqual(r['adventure']['current'],'road')
        self.assertTrue(any(p.get('bot') for p in r['players'].values()))
        ps[1].update(x=800,y=80,townInterior='inn')
        snapshot=w.state(r['code'],ps[1]['id'])
        self.assertEqual(snapshot['adventure']['area'],'road');self.assertIsNone(ps[1]['townInterior'])
        self.assertLess(math.hypot(ps[1]['x']-ps[0]['x'],ps[1]['y']-ps[0]['y']),10)

    def test_gather_cancel_when_player_walks_away(self):
        w,r,ps=party(('Knight','Druid'));e=adventure.exits(r)[0]
        for p in ps:p.update(x=e['x'],y=e['y'])
        adventure.travel(w,r,ps[0],'road');ps[0]['y']=300
        adventure.travel(w,r,ps[1],'road')
        self.assertEqual(r['adventure']['current'],'home');self.assertIsNone(ps[0]['adventureTravel'])

    def test_puzzle_trail_gather_releases_when_other_human_disconnects(self):
        w,r,ps=party(('Knight','Druid'));adventure.enter(w,r,'shrine','west')
        interact(w,r,ps[0],'altar');self.assertEqual(r['phase'],'puzzle')
        e=next(e for e in adventure.exits(r) if e['id']=='crossroads')
        ps[0].update(x=e['x'],y=e['y'])
        w.action(r['code'],ps[0]['id'],dict(action='adventureTravel',destination='crossroads'))
        self.assertEqual(r['adventure']['current'],'shrine')
        w._disconnect_player(r,ps[1]);w.tick()
        self.assertEqual(r['adventure']['current'],'crossroads')

    def test_surviving_enemies_do_not_block_ordinary_trails(self):
        w,r,ps=party();travel(w,r,'road');self.assertTrue(r['enemies'])
        travel(w,r,'crossroads');self.assertEqual(r['adventure']['current'],'crossroads')

    def test_difficulty_fixed_by_location_not_visits_routes_or_stage(self):
        w,r,ps=party();travel(w,r,'road');stats=[(e['maxHp'],e['damage'],e['speed']) for e in r['enemies']]
        baseline=w._effective_stage(r);r.update(townsVisited=20,routePressure=100,stage=17,totalStages=9)
        self.assertEqual(w._town_pressure(r),0);self.assertEqual(w._effective_stage(r),baseline)
        travel(w,r,'home');travel(w,r,'road')
        self.assertEqual(stats,[(e['maxHp'],e['damage'],e['speed']) for e in r['enemies']])

    def test_party_size_scales_initial_placed_group(self):
        w,r,_=party();travel(w,r,'road');solo=copy.deepcopy(r['enemies'])
        w2,r2,_=party(('Knight','Druid','Wizard'));travel(w2,r2,'road')
        self.assertGreater(len(r2['enemies']),len(solo));self.assertGreater(r2['enemies'][0]['maxHp'],solo[0]['maxHp'])

    def test_leash_never_attacks_distant_player_and_returns_without_healing(self):
        w,r,ps=party();p=ps[0];travel(w,r,'road');e=r['enemies'][0];now=time.monotonic()
        p.update(x=100,y=440);oldhp=p['hp'];w._tick_enemy(r,e,p,now)
        self.assertFalse(e.get('roleAttack'));self.assertEqual(p['hp'],oldhp)
        p.update(x=e['homeX']+60,y=e['homeY']);w._tick_enemy(r,e,p,now+.05)
        self.assertTrue(e['aggro'])
        e.update(x=e['homeX']+250,hp=e['hp']-10);hp=e['hp'];p.update(x=30,y=500)
        for i in range(100):w._tick_enemy(r,e,p,now+.1+i*.1)
        self.assertLess(math.hypot(e['x']-e['homeX'],e['y']-e['homeY']),12)
        self.assertEqual(e['hp'],hp);self.assertFalse(e.get('roleAttack'))

    def test_map_hides_undiscovered_areas_until_clues_reveal_them(self):
        w,r,ps=party();v=w.state(r['code'],ps[0]['id'])['adventure']
        self.assertEqual({n['id'] for n in v['locations']},{'home','road'})
        self.assertNotIn('ruins',json.dumps(v['locations']))
        travel(w,r,'road');interact(w,r,ps[0],'tracks')
        self.assertIn('clearing',r['adventure']['discovered']);self.assertNotIn('ruins',r['adventure']['discovered'])

    def test_full_region_solo_and_multiplayer_quests_rewards_and_consequences(self):
        for heroes in (('Healer',),('Knight','Druid','Wizard')):
            with self.subTest(heroes=heroes):
                w,r,ps=party(heroes,companion=len(heroes)==1);p=ps[0]
                travel(w,r,'road');interact(w,r,p,'tracks');travel(w,r,'crossroads');read_sign(w,r,p)
                travel(w,r,'clearing');kill(w,r,p);interact(w,r,p,'hunter')
                self.assertEqual(r['adventure']['quests']['hunter'],'complete')
                money=r['runes'];adventure.advance(w,r,p,'adventure_hunter');self.assertEqual(r['runes'],money)
                travel(w,r,'shrine');shrine(w,r,p)
                self.assertTrue(w.state(r['code'],p['id'])['adventure']['shrineRestored'])
                self.assertEqual(r['environment']['zones'],[])
                travel(w,r,'crossroads');travel(w,r,'camp');kill(w,r,p);interact(w,r,p,'kit')
                travel(w,r,'bridge');interact(w,r,p,'repair')
                self.assertTrue(r['adventure']['bridge']);self.assertIn('ruins',r['adventure']['discovered'])
                travel(w,r,'road');travel(w,r,'home')
                self.assertIn('recovered',[f['id'] for f in adventure.features(r)])
                travel(w,r,'road');interact(w,r,p,'tracks')
                self.assertEqual(r['adventure']['quests']['hunter'],'complete')
                travel(w,r,'bridge');travel(w,r,'ruins');interact(w,r,p,'seal',complete=False)
                self.assertTrue(all(e['locked'] for e in adventure.exits(r)))
                kill(w,r,p);self.assertTrue(r['adventure']['bossComplete'])
                for member in ps:finish(w,r,member)
                money=r['runes'];travel(w,r,'bridge');travel(w,r,'ruins')
                self.assertFalse(r['enemies']);self.assertEqual(r['runes'],money)
                self.assertFalse(r['adventure']['locked']);self.assertEqual(r['phase'],'combat')

    def test_puzzle_humans_only_reassigns_offline_clues_no_danger_growth(self):
        w,r,ps=party(('Knight','Druid'),companion=True)
        adventure.enter(w,r,'shrine','west');interact(w,r,ps[0],'altar')
        self.assertEqual(set(r['puzzle']['rooms']),{p['id'] for p in ps})
        for p in ps:self.assertNotEqual(r['puzzle']['rooms'][p['id']]['clueFor'],p['id'])
        w._disconnect_player(r,ps[1]);w._update_presence(r,time.monotonic())
        self.assertEqual(r['puzzle']['rooms'][ps[0]['id']]['clueFor'],ps[0]['id'])
        wrong=next(e for e in r['puzzle']['rooms'][ps[0]['id']]['runes'] if e['rune']!=r['puzzle']['rooms'][ps[0]['id']]['target'])
        ps[0].update(x=wrong['x'],y=wrong['y']);w._tick_puzzle(r);self.assertEqual(r['strainMistakes'],0)
        target=next(e for e in r['puzzle']['rooms'][ps[0]['id']]['runes'] if e['rune']==r['puzzle']['rooms'][ps[0]['id']]['target'])
        ps[0].update(x=target['x'],y=target['y']);w._tick_puzzle(r)
        self.assertTrue(r['adventure']['locked']);self.assertEqual(len(r['enemies']),1)

    def test_bridge_requires_kit_and_is_idempotent(self):
        w,r,ps=party();adventure.enter(w,r,'bridge','north');p=ps[0]
        with self.assertRaisesRegex(ValueError,'repair kit'):interact(w,r,p,'repair')
        r['adventure']['claimed'].append('repair_kit');interact(w,r,p,'repair');money=r['runes']
        interact(w,r,p,'repair');self.assertEqual(r['runes'],money)
        self.assertFalse(next(e for e in adventure.exits(r) if e['id']=='road')['locked'])

    def test_duplicate_dialogue_requests_cannot_duplicate_rewards_or_puzzle(self):
        w,r,ps=party();adventure.enter(w,r,'clearing','west');kill(w,r,ps[0]);interact(w,r,ps[0],'hunter',False)
        d=ps[0]['dialogue'].copy();payload=dict(action='dialogueNext',id=d['id'],page=d['page'])
        w.action(r['code'],ps[0]['id'],payload);money=r['runes']
        with self.assertRaises(ValueError):w.action(r['code'],ps[0]['id'],payload)
        self.assertEqual(r['runes'],money)

    def test_save_restart_and_old_checkpoint_coexist_without_modification(self):
        from test_support import rest_at_bed
        with tempfile.TemporaryDirectory() as directory:
            # A real version-one Gauntlet checkpoint remains readable and unchanged.
            old=GameWorld(storage_dir=directory);code,pid=old.create_room('Legacy')
            old.action(code,pid,{'action':'class','class':'Knight'});old.action(code,pid,{'action':'loadout','abilities':[a[0] for a in ABILITY_SETS['Knight'][::2]]})
            old.action(code,pid,{'action':'start'});old._enter_town(old.rooms[code]);rest_at_bed(old,old.rooms[code])
            path=Path(directory)/'checkpoints'/(code+'.json');original=path.read_bytes()
            w,r,ps=party(storage_dir=directory);p=ps[0]
            inn=next(h for h in r['townLayout'] if h['service']=='innkeeper');bed=next(b for b in r['innRooms'] if not b['locked'])
            p.update(townInterior=inn['id'],innFloor=2,x=bed['x'],y=bed['y'])
            w.action(r['code'],p['id'],dict(action='interact'));p.update(townInterior=None)
            travel(w,r,'road');w._damage_enemy(r,p,r['enemies'][0],99999)
            survivors=len(r['enemies'])
            r['adventure']['claimed'].append('repair_kit');r['adventure']['bridge']=True;r['adventure']['quests']['bridge']='complete'
            r['runes']=100;adventure.save(w,r)
            restored=GameWorld(storage_dir=directory);rr=restored.rooms[r['code']];rp=rr['players'][p['id']]
            self.assertEqual(rr['adventure']['current'],'home');self.assertTrue(rr['adventure']['bridge'])
            self.assertEqual(rp['innFloor'],2);self.assertEqual(rr['runes'],100)
            self.assertFalse(rp['connected']);self.assertEqual(path.read_bytes(),original)
            self.assertIn(code,restored.rooms);self.assertEqual(restored.rooms[code]['phase'],'town')
            restored.state(rr['code'],rp['id']);self.assertEqual(rp['townInterior'],inn['id'])
            self.assertEqual(rp['innFloor'],2)
            self.assertEqual([rp['x'],rp['y']],[bed['x'],bed['y']+65])
            rp.update(townInterior=None,innFloor=1)
            travel(restored,rr,'road');self.assertEqual(len(rr['enemies']),survivors)
            self.assertEqual(rr['adventure']['quests']['bridge'],'complete')

    def test_personal_progress_and_completed_revive_are_saved_without_rest(self):
        with tempfile.TemporaryDirectory() as directory:
            w,r,ps=party(('Druid','Knight'),storage_dir=directory);p,ally=ps
            staff=w._make_item('sage_wand');p['inventory'].append(staff)
            w.action(r['code'],p['id'],dict(action='equipItem',item=staff['id'],slot=0))
            p.update(abilities=['thornshot','fire_wolf','nature_golem'],classChangeUsed=True,
                     trainingKnown=True,skillPoints=2,skillRanks={'vitality':1,'power':1,'focus':0})
            # Model a pre-tree record: its equipped skills become legacy grants.
            p.pop('heroProgress',None);p.pop('adventureLoadout',None)
            travel(w,r,'road');ally.update(status='downed',hp=0)
            w._restore_ally(r,p,ally,.3)
            restarted=GameWorld(storage_dir=directory);rr=restarted.rooms[r['code']];rp=rr['players'][p['id']]
            self.assertEqual(rp['toolSlots'][0]['id'],staff['id'])
            self.assertEqual(rp['weapon']['id'],staff['id'])
            self.assertEqual(rp['abilities'],['thornshot','fire_wolf','nature_golem'])
            self.assertTrue(rp['classChangeUsed']);self.assertTrue(rp['trainingKnown'])
            self.assertEqual(rp['heroProgress']['legacyPoints'],2);self.assertEqual(rp['skillRanks']['power'],1)
            totals={row['name']:row for row in restarted.run_stats(rr['code'],rp['id'])}
            self.assertEqual(totals[p['name']]['revives'],1)

    def test_companion_consumption_is_saved_immediately(self):
        import companion_ai
        with tempfile.TemporaryDirectory() as directory:
            w,r,ps=party(storage_dir=directory,companion=True);travel(w,r,'road')
            bot=next(p for p in r['players'].values() if p.get('bot'))
            bottle=w._make_item('mana_draught');now=time.monotonic()
            bot.update(mana=0,inventory=[bottle],abilityCooldowns={aid:now+100 for aid in bot['abilities']})
            companion_ai.tick(w,r,now,ABILITY_SETS)
            self.assertFalse(bot['inventory'])
            restart=GameWorld(storage_dir=directory)
            self.assertFalse(restart.rooms[r['code']]['players'][bot['id']]['inventory'])

    def test_rewards_stay_claimed_after_disk_recovery(self):
        with tempfile.TemporaryDirectory() as directory:
            w,r,ps=party(storage_dir=directory);p=ps[0]
            travel(w,r,'road');travel(w,r,'crossroads');travel(w,r,'camp')
            kill(w,r,p);interact(w,r,p,'kit');travel(w,r,'bridge');interact(w,r,p,'repair')
            money=r['runes'];items=copy.deepcopy(p['inventory'])
            restarted=GameWorld(storage_dir=directory);rr=restarted.rooms[r['code']];rp=rr['players'][p['id']]
            restarted.state(rr['code'],rp['id']);travel(restarted,rr,'road');travel(restarted,rr,'bridge')
            interact(restarted,rr,rp,'repair')
            self.assertFalse(adventure.reward(restarted,rr,'bridge',25,'warding_tonic'))
            self.assertEqual(rr['runes'],money);self.assertEqual(rp['inventory'],items)
            travel(restarted,rr,'camp');self.assertFalse(rr['enemies'])
            self.assertNotIn('kit',[f['id'] for f in adventure.features(rr)])

    def test_wipe_once_keeps_completed_objectives_and_saved_progress(self):
        with tempfile.TemporaryDirectory() as directory:
            w,r,ps=party(storage_dir=directory);p=ps[0]
            travel(w,r,'road');kill(w,r,p);r['adventure']['bridge']=True;r['adventure']['quests']['bridge']='complete'
            r['runes']=100;p.update(status='downed',hp=0)
            self.assertTrue(w._check_party_wipe(r));self.assertEqual(r['runes'],60)
            self.assertFalse(w._check_party_wipe(r));self.assertEqual(r['runes'],60)
            self.assertEqual(r['adventure']['wipeCount'],1);self.assertTrue(r['adventure']['bridge'])
            restart=GameWorld(storage_dir=directory);rr=restart.rooms[r['code']]
            self.assertEqual(rr['runes'],60);self.assertEqual(rr['adventure']['wipeCount'],1)
            restart.state(rr['code'],p['id']);travel(restart,rr,'road');self.assertFalse(rr['enemies'])

    def test_restart_mid_boss_does_not_lock_village_and_guardian_can_resume(self):
        with tempfile.TemporaryDirectory() as directory:
            w,r,ps=party(storage_dir=directory);adventure.enter(w,r,'shrine','west');adventure.spawn_guardian(w,r)
            restarted=GameWorld(storage_dir=directory);rr=restarted.rooms[r['code']]
            self.assertFalse(rr['adventure']['locked'])
            restarted.state(rr['code'],ps[0]['id']);travel(restarted,rr,'road')
            adventure.enter(restarted,rr,'shrine','west')
            self.assertTrue(rr['adventure']['locked']);self.assertEqual(len(rr['enemies']),1)

    def test_gauntlet_remains_default_and_wave_completion_works(self):
        w=GameWorld();c,p=w.create_room('Normal')
        w.action(c,p,{'action':'class','class':'Knight'});w.action(c,p,{'action':'loadout','abilities':[a[0] for a in ABILITY_SETS['Knight'][::2]]})
        w.action(c,p,{'action':'start'});r=w.rooms[c]
        self.assertEqual(r['mode'],'gauntlet');self.assertIsNone(w.state(c,p)['adventure'])
        kill(w,r,r['players'][p]);self.assertTrue(r['waveStartsAt']);self.assertEqual(r['stageWave'],2)


if __name__=='__main__':unittest.main()

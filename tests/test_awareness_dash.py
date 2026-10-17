import time
import unittest
from unittest.mock import patch
import adventure
import enemy_awareness as awareness
import enemy_roles
import combat_environment as terrain
from test_adventure import party,travel


class AwarenessDashTests(unittest.TestCase):
    def encounter(self,heroes=('Rogue',)):
        w,r,ps=party(heroes);travel(w,r,'road');r['environment']={}
        e=r['enemies'][0];e.update(x=500,y=400,homeX=500,homeY=400,aggroRadius=170,leashRadius=245)
        for p in ps:p.update(x=530,y=400)
        return w,r,ps,e

    def test_hidden_taunt_never_acquired_then_detects_after_expiry(self):
        w,r,ps,e=self.encounter();p=ps[0];now=time.monotonic();p.update(invisibleUntil=now+5,tauntUntil=now+20)
        self.assertIsNone(awareness.choose(w,r,e,now));self.assertNotIn('lastKnown',e)
        self.assertIsNone(awareness.choose(w,r,e,now+6))
        self.assertIs(awareness.choose(w,r,e,now+6.3),p);self.assertEqual(e['awarenessCue'],'!')

    def test_loss_search_return_and_visible_teammate(self):
        w,r,ps,e=self.encounter(('Rogue','Knight'));p,ally=ps;now=time.monotonic()
        awareness.choose(w,r,e,now);awareness.choose(w,r,e,now+.3)
        p.update(invisibleUntil=now+20,x=680,y=470);ally['connected']=False
        self.assertIsNone(awareness.choose(w,r,e,now+.4));self.assertEqual(e['lastKnown'],[530,400]);self.assertEqual(e['awareness'],'searching')
        awareness.choose(w,r,e,now+4);self.assertIn(e['awareness'],('returning','unaware'))
        ally['connected']=True;awareness.choose(w,r,e,now+4.1)
        self.assertIs(awareness.choose(w,r,e,now+4.5),ally)

    def test_los_and_committed_shot_not_new_attack(self):
        w,r,ps,e=self.encounter();p=ps[0];now=time.monotonic()
        with patch.object(terrain,'line_clear',return_value=False):self.assertIsNone(awareness.choose(w,r,e,now))
        e.update(combatRole='ranged',awareness='alert',lastKnown=[530,400],roleAttack=dict(kind='ranged',targetId=p['id'],x=530,y=400,releaseAt=now,startedAt=now-1))
        p.update(invisibleUntil=now+10,x=600,y=470)
        target=awareness.choose(w,r,e,now);enemy_roles.tick(w,r,e,target,now,.05)
        shot=r['projectiles'][-1];self.assertEqual(shot['vy'],0);self.assertEqual(shot['trackUntil'],0)
        enemy_roles.tick(w,r,e,target,now+3,.05);self.assertNotIn('roleAttack',e)

    def test_incidental_projectiles_still_hit_hidden_hero(self):
        w,r,ps,e=self.encounter();p=ps[0];now=time.monotonic();p['invisibleUntil']=now+20
        w._launch_projectile(r,side='enemy',owner_id=e['id'],target_id=p['id'],x=500,y=400,damage=4,color='#fff',attack_class='Archer',speed=300)
        shot=r['projectiles'][-1];shot.update(lastTick=now-.1,vx=300,vy=0);hp=p['hp']
        w._tick_projectiles(r,now);self.assertLess(p['hp'],hp)

    def test_bleed_and_summons_do_not_reveal_hidden_owner_coordinates(self):
        w,r,ps,e=self.encounter();p=ps[0];now=time.monotonic()
        e.update(hp=1000,maxHp=1000,lastKnown=[530,400],awareness='searching',searchUntil=now+3)
        p.update(invisibleUntil=now+10,x=670,y=460)
        w._damage_enemy(r,p,e,1,direct=False)
        w._damage_enemy(r,p,e,1,summon_id='an-existing-summon')
        self.assertEqual(e['lastKnown'],[530,400]);self.assertEqual(e['awareness'],'searching')

    def test_exploration_dash_roots_dialogue_and_village_collision(self):
        w,r,ps=party();p=ps[0];p.update(x=480,y=400,dx=1,dy=0)
        w.action(r['code'],p['id'],dict(action='dash'));self.assertGreater(p['x'],480)
        self.assertGreater(p['dashCooldownUntil'],time.monotonic())
        with self.assertRaisesRegex(ValueError,'recharges'):w.action(r['code'],p['id'],dict(action='dash'))
        travel(w,r,'road');p.update(rootUntil=time.monotonic()+10,dashCooldownUntil=0)
        with self.assertRaisesRegex(ValueError,'rooted'):w.action(r['code'],p['id'],dict(action='dash'))
        p.update(rootUntil=0,dialogue={'id':'test'})
        with self.assertRaisesRegex(ValueError,'conversation'):w.action(r['code'],p['id'],dict(action='dash'))
        p['dialogue']=None;r['phase']='town';p.update(x=480,y=400)
        with patch.object(w,'_town_walkable',side_effect=lambda room,x,y:x<=510):w.action(r['code'],p['id'],dict(action='dash'))
        self.assertLessEqual(p['x'],510)

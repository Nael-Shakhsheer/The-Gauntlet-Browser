"""Presentation metadata must follow actual resolution without changing combat."""
import time
import unittest
from unittest.mock import patch
import ability_animations as animations
import ability_visuals as visuals
import adventure,ascension,hero_skills,region_content,skill_casts
from test_expansion import start


class VisualContractTests(unittest.TestCase):
    def setup_combat(self,hero='Knight'):
        w,r,ps=start((hero,'Healer' if hero!='Healer' else 'Knight'));p,q=ps
        adventure.enter(w,r,'road','north');e=r['enemies'][0];r['environment']={'barriers':[],'obstacles':[],'zones':[]}
        p.update(x=400,y=300,mana=100,status='alive');q.update(x=430,y=300,status='alive')
        p['magicRunes']['ascended']=True
        e.update(x=500,y=300,hp=10000,maxHp=10000);r['enemies']=[e]
        return w,r,p,q,e

    def test_all_signature_commitments_and_effect_copy_release(self):
        for hero in ascension.SPECS:
            with self.subTest(hero=hero):
                w,r,p,q,e=self.setup_combat(hero);a=ascension.ability(p)
                if hero=='Healer':q.update(status='downed',hp=0)
                ascension.cast(w,r,p,a);motion=p['abilityAnimation'];effect=next(c for c in r['effects'] if c.get('id')==motion['id'])
                self.assertEqual(motion['abilityId'],a['id']);self.assertFalse(motion['released']);self.assertEqual(effect['releaseAt'],.6)
                self.assertEqual(motion['visual']['family'],visuals.ASCENDED[hero])
                due=r['ascensionCasts'][0]['releaseAt'];hp=e['hp'];ascension.tick(w,r,due-.01);self.assertEqual(e['hp'],hp)
                ascension.tick(w,r,due+.01);self.assertTrue(motion['released']);self.assertTrue(effect['released'])
                self.assertAlmostEqual(motion['releaseAt'],.61,places=2)
                if hero=='Healer':self.assertEqual(effect['recipientIds'],[q['id']]);self.assertEqual(q['status'],'alive')
                if hero=='Archer':self.assertEqual(motion['visual']['shape'],'line');self.assertEqual(motion['visual']['width'],38)

    def test_cancelled_commitment_never_releases_either_copy(self):
        w,r,p,q,e=self.setup_combat('Wizard');ascension.cast(w,r,p,ascension.ability(p));c=r['ascensionCasts'][0]
        r['environment']['barriers']=[dict(x=445,y=0,width=20,height=540,blocksShots=True,material='stone')]
        ascension.tick(w,r,c['releaseAt']+.01)
        records=[p['abilityAnimation']]+[e for e in r['effects'] if e.get('type')=='ability_cast']
        self.assertTrue(all(m['cancelled'] and not m['released'] for m in records));self.assertEqual(e['hp'],10000)

    def test_new_skill_keeps_actual_id_and_zone_clock(self):
        w,r,p,q,e=self.setup_combat();a=hero_skills.catalog(p)['rally_banner'];skill_casts.cast(w,r,p,a)
        self.assertEqual(p['abilityAnimation']['abilityId'],'rally_banner');z=r['skillZones'][0]
        self.assertTrue(z['id']);self.assertEqual(z['duration'],6);self.assertEqual(z['radius'],150)
        public=w.state(r['code'],p['id'])['skillZones'][0];self.assertIn('remaining',public);self.assertEqual(public['ownerId'],p['id'])

    def test_basic_preparation_is_only_existing_recharge(self):
        w,r,p,q,e=self.setup_combat();p['attacking']=True;now=time.monotonic()
        aid=p['abilities'][0];p['abilityCooldowns'][aid]=now+.12
        self.assertGreater(animations.preparation(r,p,now),0)
        p['attacking']=False;self.assertEqual(animations.preparation(r,p,now),0)
        p['attacking']=True;p['abilityCooldowns'][aid]=now-.1;self.assertEqual(animations.preparation(r,p,now),0)

    def test_shrine_art_state_is_authoritative(self):
        w,r,ps=start();adventure.enter(w,r,'brook','east')
        f=next(f for f in region_content.features(r) if f['kind']=='travel_shrine');self.assertFalse(f['active'])
        region_content.shrine_state(r)['active'].append('brook')
        self.assertTrue(next(f for f in region_content.features(r) if f['kind']=='travel_shrine')['active'])

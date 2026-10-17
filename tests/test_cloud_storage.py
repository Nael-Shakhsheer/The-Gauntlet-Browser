"""Mocked Supabase contract tests. Not live Postgres or hosted recovery proof."""
import copy
import tempfile
import unittest
import uuid
from unittest.mock import patch
import adventure
from adventure_recovery import Recovery
from cloud_storage import Supabase
from cloud_storage import public_key
from game import GameWorld
from test_adventure import party


class FakeTransactions:
    def __init__(self):self.worlds={};self.members={};self.receipts={}
    def rpc(self,name,**p):
        actor=p['p_actor'];wid=p.get('p_world')
        if name=='gauntlet_claim_world':
            if wid not in self.worlds:
                if p['p_character']!=p['p_creator']:raise ValueError('Creator must link first')
                self.worlds[wid]=dict(record=copy.deepcopy(p['p_record']),owner=actor,revision=1,savedAt='2026-10-12T12:00:00Z')
            w=self.worlds[wid]
            if p['p_character'] not in w['record']['characterIds']:raise ValueError('Invalid character')
            if p['p_character']==p['p_creator'] and w['owner']!=actor:raise ValueError('Owner mismatch')
            old=self.members.get((wid,actor))
            if old and old!=p['p_character']:raise ValueError('Already linked another character')
            if any(c==p['p_character'] and u!=actor for (w,u),c in self.members.items() if w==wid):raise ValueError('Character already claimed')
            self.members[wid,actor]=p['p_character'];return {k:w[k] for k in ('revision','savedAt')}|{'owner':w['owner']==actor}
        if name=='gauntlet_list_worlds':return [dict(worldId=w,**data) for w,data in self.worlds.items() if (w,actor) in self.members]
        if (wid,actor) not in self.members:raise ValueError('Membership required')
        w=self.worlds[wid]
        if name=='gauntlet_load_world':return copy.deepcopy(w)|dict(character=self.members[wid,actor])
        if name=='gauntlet_save_world':
            if self.members[wid,actor]!=p['p_character']:raise ValueError('Wrong character')
            if (wid,p['p_request']) in self.receipts:return self.receipts[wid,p['p_request']]
            if w['revision']!=p['p_expected']:raise ValueError('Cloud revision conflict. Remote preserved.')
            w.update(record=copy.deepcopy(p['p_record']),revision=w['revision']+1,savedAt='2026-10-12T12:01:00Z')
            result={k:w[k] for k in ('revision','savedAt')};self.receipts[wid,p['p_request']]=result;return result
        raise AssertionError(name)


class CloudContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.provider=Supabase(self.tmp.name);self.fake=FakeTransactions()
        self.provider.rpc=self.fake.rpc;self.provider.actor=lambda token:str(uuid.uuid5(uuid.NAMESPACE_DNS,token)) if token in ('owner','guest','outsider') else (_ for _ in ()).throw(ValueError('Invalid account token'))
        self.w,self.r,self.ps=party(('Knight','Druid'),storage_dir=self.tmp.name)
        self.recovery=Recovery(self.w)

    def claim(self,index,token):return self.provider.claim(self.w,self.recovery.session(self.r['code'],self.ps[index]['id']),token)

    def test_no_config_keeps_local_only_and_hides_secrets(self):
        self.assertFalse(self.provider.public_config()['configured']);self.assertNotIn('secret',self.provider.public_config())
        self.assertEqual(self.w.adventure_summary(self.r,self.ps[0])['storage']['type'],'local')
        self.assertFalse(public_key('sb_secret_private'));self.assertTrue(public_key('sb_publishable_public'))
        import base64,json
        secret='x.'+base64.urlsafe_b64encode(json.dumps({'role':'service_role'}).encode()).decode()+'.x'
        self.assertFalse(public_key(secret))

    def test_forged_room_code_or_public_player_id_cannot_claim(self):
        payload=dict(room=self.r['code'],player=self.ps[0]['id'])
        with self.assertRaises(ValueError):self.provider.claim(self.w,payload,'outsider')
        with self.assertRaises(ValueError):self.provider.claim(self.w,{**payload,'recovery':'invented'},'owner')
        self.assertFalse(self.fake.worlds)

    def test_owner_first_guest_membership_host_change_never_transfers_owner(self):
        with self.assertRaises(ValueError):self.claim(1,'guest')
        self.assertTrue(self.claim(0,'owner')['owner']);self.assertFalse(self.claim(1,'guest')['owner'])
        owner=self.fake.worlds[self.r['adventure']['worldId']]['owner'];self.r['host']=self.ps[1]['id']
        self.claim(1,'guest');self.assertEqual(self.fake.worlds[self.r['adventure']['worldId']]['owner'],owner)
        with self.assertRaises(ValueError):self.claim(0,'outsider')

    def test_unverified_token_cannot_link_and_client_actor_ignored(self):
        with self.assertRaises(ValueError):self.claim(0,'forged-jwt')
        payload=self.recovery.session(self.r['code'],self.ps[0]['id'])|{'userId':'attacker','owner':'attacker'}
        self.provider.claim(self.w,payload,'owner')
        self.assertEqual(self.fake.worlds[self.r['adventure']['worldId']]['owner'],self.provider.actor('owner'))

    def test_confirmed_cloud_time_retry_and_revision_conflict_preserve_remote(self):
        self.claim(0,'owner');wid=self.r['adventure']['worldId'];record=adventure.snapshot(self.r)
        self.provider.sync(wid,record);confirmed=self.provider.status(wid)['cloudSavedAt']
        self.provider.bindings[wid]['revision']=1;self.provider.sync(wid,record)  # lost acknowledgement, identical request
        self.assertEqual(self.provider.bindings[wid]['revision'],2)
        self.provider.bindings[wid]['revision']=1;self.r['runes']+=10
        with self.assertRaises(ValueError):self.provider.sync(wid,adventure.snapshot(self.r))
        self.assertEqual(self.provider.status(wid)['cloudSavedAt'],confirmed);self.assertEqual(self.fake.worlds[wid]['revision'],2)

    def test_cloud_load_membership_character_bound_and_live_world_not_overwritten(self):
        self.claim(0,'owner');self.claim(1,'guest');wid=self.r['adventure']['worldId'];self.r['runes']=789
        with self.assertRaises(ValueError):self.provider.load(self.recovery,'outsider',wid)
        session=self.provider.load(self.recovery,'guest',wid)
        self.assertEqual(session['player'],self.ps[1]['id']);self.assertEqual(self.r['runes'],789)

    def test_new_server_recovery_preserves_world_character_and_pending_claims(self):
        adventure.reward(self.w,self.r,'shrine',35,'class_weapon');self.claim(0,'owner');self.claim(1,'guest');wid=self.r['adventure']['worldId']
        with tempfile.TemporaryDirectory() as other:
            fresh=GameWorld(storage_dir=other);s=Recovery(fresh);session=self.provider.load(s,'guest',wid)
            rr=fresh.rooms[session['room']];p=rr['players'][session['player']]
            self.assertEqual(rr['adventure']['worldId'],wid);self.assertEqual(p['characterId'],self.ps[1]['characterId']);self.assertEqual(p['class'],'Druid')
            self.assertIn('shrine',p['pendingRewards']);self.assertEqual(rr['adventure']['current'],'home')

    def test_cloud_failure_leaves_local_confirmed_status_and_record_intact(self):
        self.claim(0,'owner');wid=self.r['adventure']['worldId'];before=self.w.storage.adventure_paths[wid].read_bytes()
        with patch.object(self.provider,'rpc',side_effect=ValueError('Network failure')):
            with self.assertRaises(ValueError):self.provider.sync(wid,adventure.snapshot(self.r))
        self.assertEqual(before,self.w.storage.adventure_paths[wid].read_bytes());self.assertTrue(self.r['adventure']['savedAt'])


if __name__=='__main__':unittest.main()

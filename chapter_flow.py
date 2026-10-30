"""Shared assignments, collected evidence and explicit village turn-ins.

Old woodland results are never revoked. Evidence may arrive early, but only an
accepted assignment becomes ready, and only a deliberate report completes it.
"""
import copy
import campaign_quests

# key, title, hub, practical assignment, evidence required
DEFINITIONS=(
 ('hunter','The Missing Hunter','home','Follow the Southern road tracks, defeat the clearing guards and rescue the hunter.',('hunter_rescued',)),
 ('bridge','A Road Worth Keeping','home','Recover the camp kit and repair the crossing. Return with the supply route open.',('bridge_repaired',)),
 ('water','Water Without Light','home','Inspect the marked brook outlet and the damaged mill wheel; report what the water carries.',('brook_outlet','mill_wheel')),
 ('shrine','Restore the Woodland Mechanism','home','Restore the overgrown shrine: solve its clues and defeat the guardian.',('shrine_restored',)),
 ('watch','The Broken Watch','home','Inspect the burned watch register and the network seal on the ruins approach.',('watch_register','network_seal')),
 ('ruins','Beneath the Old Stones','home','Defeat the Minotaur King and inspect the pumping register exposed in the ruins.',('minotaur_defeated','pumping_register')),
 ('border','The Grain Road','home','Accept the road to Dunmere. The border trail opens; report to its village runner.',('dunmere_arrival',)),
 ('failed_harvest','The Harvest That Never Came','dunmere','Inspect the dry ditch, rooted crops and empty granary. Return to compare the evidence.',('dry_ditch','rooted_crop','empty_granary')),
 ('irrigation','Water for the Living','dunmere','Clear the mill approach, remove both channel blockages and operate the sluice.',('channel_west','channel_east','sluice_open')),
 ('mill_cellar','Under the Mill','dunmere','Enter the mill cellar, defeat the Blighted Overseer and recover its additive ledger.',('overseer_defeated','additive_ledger')),
 ('chapter_outcome','A Harvest Worth Saving','dunmere','Inspect the restored field and deliver the ledger to the village runner. Resolve the local supply crisis.',('field_restored',)),
)
ORIGINAL_ORDER=[d[0] for d in DEFINITIONS]
MAIN_ORDER=ORIGINAL_ORDER+[d[0] for d in campaign_quests.MAIN]
DEFINITIONS=(*DEFINITIONS,*campaign_quests.MAIN,*campaign_quests.SIDE)
ORDER=[d[0] for d in DEFINITIONS]
SPECS={d[0]:dict(id=d[0],title=d[1],hub=d[2],objective=d[3],requires=list(d[4])) for d in DEFINITIONS}
for key,*_ in campaign_quests.SIDE:SPECS[key]['optional']=True
STATUSES={'unavailable','offered','accepted','ready-to-turn-in','complete'}
EVIDENCE={e for spec in SPECS.values() for e in spec['requires']}
MAGIC_SOURCES={'hunter':('report:hunter',1),'bridge':('report:bridge',1),'shrine':('report:shrine',1),
 'ruins':('report:woodland_boss',2),'failed_harvest':('report:failed_harvest',1),
 'irrigation':('report:irrigation',2),'mill_cellar':('report:mill_cellar',2),'chapter_outcome':('report:chapter_outcome',2)}
MAGIC_SOURCES.update(campaign_quests.MAGIC)
REPORTS={
 'hunter':'The hunter is recovering in Oakvale. He saw cloudy water before the watch burned. The supply bridge must reopen before another grain wagon can pass.',
 'bridge':'The repaired crossing shortens the supply road. Workers can reach the camp again, but no grain is arriving. Inspect the brook and the stopped mill wheel.',
 'water':'The pale residue predates the dragon strike. The shrine once regulated this spring; restore its mechanism to learn what changed.',
 'shrine':'The shrine is green again. Its guardian no longer poisons the glade. Compare the burned watch register with the network seal beyond Deepwood.',
 'watch':'The watch, shrine and ruins are one spring network. The dragon broke its seal after creatures began fleeing. Secure the Minotaur’s boundary and recover the pumping register.',
 'ruins':'Oakvale’s woodland is secured. Dunmere drew more water than the spring could supply. Accept the Grain Road assignment to carry the register south.',
 'border':'Dunmere received Oakvale’s register. The farmers suspect drought. Compare the ditch, failed crop and empty granary before deciding what to repair.',
 'failed_harvest':'The three sites show roots and an unusual additive, rather than drought alone. Clear the mill’s two channels and reopen the sluice.',
 'irrigation':'One irrigation strip runs again and green shoots survive. The mill cellar holds the missing delivery records; open its pump chamber after clearing the approach.',
 'mill_cellar':'The Overseer is defeated and the field hatch is open. The ledger shows the steward concealed the additive’s risks. Inspect the restored field before the final report.',
 'chapter_outcome':'Dunmere’s immediate mill crisis is resolved. Water reaches a living strip and the harmful additive is withdrawn. Speak to Tovin about tracing the material to the pumping works. Ashen Ridge remains beyond the repaired area.'}
REPORTS.update(campaign_quests.REPORTS)


def ensure(room,legacy=None):
    a=room['adventure'];s=a.get('chapter')
    if s is None:
        old=bool(legacy) if legacy is not None else True
        s=a['chapter']=dict(version=1,legacy=old,stages={k:'unavailable' for k in ORDER},evidence=[],turnedIn=[])
        if old:
            q=a['quests']
            for key,condition in [('hunter',q['hunter']=='complete'),('bridge',a['bridge']),('shrine',q['shrine']=='complete')]:
                if condition:s['evidence'].append({'hunter':'hunter_rescued','bridge':'bridge_repaired','shrine':'shrine_restored'}[key]);s['stages'][key]='complete';s['turnedIn'].append(key)
            if a['bossComplete']:
                # A finished old chapter qualifies for its new personal receipts
                # without replaying old shared currency/equipment payouts.
                for key in ORDER[:6]:
                    s['stages'][key]='complete'
                    if key not in s['turnedIn']:s['turnedIn'].append(key)
                    for fact in SPECS[key]['requires']:
                        if fact not in s['evidence']:s['evidence'].append(fact)
        reconcile(room)
    if s.get('version')!=1:raise ValueError('Unsupported chapter progress; original preserved.')
    for key in ORDER:s['stages'].setdefault(key,'unavailable')
    s.setdefault('choices',{})
    return s


def reconcile(room):
    a=room['adventure'];s=a['chapter'];q=a['quests']
    facts={'hunter_rescued':q['hunter']=='complete','bridge_repaired':a['bridge'],'shrine_restored':q['shrine']=='complete','minotaur_defeated':a['bossComplete'],
           'dunmere_arrival':'dunmere' in a['visited']}
    for fact,done in facts.items():
        if done and fact not in s['evidence']:s['evidence'].append(fact)
    for key in ORDER:
        if s['stages'][key]=='accepted' and all(f in s['evidence'] for f in SPECS[key]['requires']):s['stages'][key]='ready-to-turn-in'
    if not __import__('opening').active(room):
        next_key=next((k for k in MAIN_ORDER if s['stages'][k]!='complete'),None)
        if next_key and s['stages'][next_key]=='unavailable':s['stages'][next_key]='offered'
        campaign_quests.reconcile(room)


def evidence(room,key):
    s=ensure(room)
    if key not in EVIDENCE:raise ValueError('Unknown chapter evidence.')
    if key in s['evidence']:return False
    s['evidence'].append(key);reconcile(room);return True


def require(room,key):
    s=ensure(room);reconcile(room)
    if s['legacy'] and key in ('hunter','bridge','shrine','ruins'):return
    if s['stages'][key] not in ('accepted','ready-to-turn-in','complete'):
        spec=SPECS[key];raise ValueError('Accept “'+spec['title']+'” from its village contact first. Journal shows the assignment and collected evidence.')


def available_rewards(room):
    s=ensure(room)
    return {source:amount for key,(source,amount) in MAGIC_SOURCES.items() if key in s['turnedIn']}


def menu(room,player):
    s=ensure(room);reconcile(room);hub=room['adventure']['current']
    rows=[];points=None
    for k in ORDER:
        status=s['stages'][k]
        if status=='unavailable':continue
        actionable=False
        if status in ('offered','ready-to-turn-in') and hub in campaign_quests.action_hubs(k,action_hub(k,status)):
            if points is None:points=__import__('adventure').features(room)
            actionable=bool(campaign_quests.contact(room,player,k,points))
        rows.append(dict(**SPECS[k],status=status,outcome=REPORTS[k] if status=='complete' else None,
            found=[f for f in SPECS[k]['requires'] if f in s['evidence']],
            contact=campaign_quests.NAMES.get(campaign_quests.CONTACTS.get(k,['runner'])[0],'Village Runner'),actionable=actionable))
    return rows


def action_hub(key,status):
    return 'dunmere' if key=='border' and status in ('accepted','ready-to-turn-in','complete') else SPECS[key]['hub']


def action(world,room,player,payload):
    import adventure,progression
    if isinstance(payload.get('quest'),str) and payload['quest'] in __import__('campaign_content').QUESTS:
        return __import__('campaign_progress').quest_action(world,room,player,payload)
    if player.get('bot') or not player.get('connected',True) or player['status']!='alive' or player.get('townInterior') or progression.locked(room,player):raise ValueError('Finish the conversation and report outside to the village runner.')
    key=payload.get('quest');s=ensure(room);reconcile(room)
    if key not in SPECS or room['adventure']['current'] not in campaign_quests.action_hubs(key,action_hub(key,s['stages'][key])):raise ValueError('That assignment belongs to a different village.')
    if not campaign_quests.contact(room,player,key):raise ValueError('Speak to the assignment’s contact or village runner to accept or report it.')
    status=s['stages'][key]
    before=copy.deepcopy(room['adventure']);old_runes=room['runes']
    personal={pid:copy.deepcopy(p) for pid,p in room['players'].items()}
    transient={key:copy.deepcopy(room.get(key)) for key in ('_feedback','chat','privateNotices')}
    if payload['action']=='chapterAccept':
        if status in ('accepted','ready-to-turn-in','complete'):return
        if status!='offered':raise ValueError('Finish and report the previous assignment first.')
        if key not in ('hunter','bridge','shrine','ruins'):s['legacy']=False
        s['stages'][key]='accepted';reconcile(room)
        chart={'bridge':['camp','bridge'],'water':['brook','mill_trail'],'watch':['yard','hollow','watch','network'],
               'border':['border','dunmere'],'failed_harvest':['fields'],'irrigation':['mill'],'mill_cellar':['cellar'],
               'upstream':['eastern_threshold','irrigation_channels','farmstead'],'steward':['pump_exterior'],
               'sluice_route':['sluice_entry'],'pumping_finale':['pump_chamber'],'root_sump':['farmstead']}.get(key,[])
        adventure.reveal(room,*chart)
    elif payload['action']=='chapterReport':
        if status=='complete':return
        if status!='ready-to-turn-in':raise ValueError('Complete the accepted assignment first. Collected evidence is kept in Journal.')
        s['stages'][key]='complete'
        if key not in s['turnedIn']:s['turnedIn'].append(key)
        reconcile(room)
        __import__('magic_runes').reconcile_reports(room)
        campaign_quests.reported(world,room,key)
    else:raise ValueError('Unknown assignment action.')
    if not adventure.save(world,room) and world.storage:
        room['adventure'].clear();room['adventure'].update(before);room['runes']=old_runes
        for pid,p in room['players'].items():
            p.clear();p.update(personal[pid])
        for key,value in transient.items():
            if value is None:room.pop(key,None)
            else:room[key]=value
        raise ValueError('Assignment update was not committed because storage failed. Progress and personal reward receipts are unchanged; retry after checking storage.')
    message=('Assignment accepted: '+SPECS[key]['title']+'. '+SPECS[key]['objective']) if payload['action']=='chapterAccept' else REPORTS[key]
    if payload['action']=='chapterReport' and key in MAGIC_SOURCES:
        message+=' Each character received '+str(MAGIC_SOURCES[key][1])+' personal Magic Rune'+('s' if MAGIC_SOURCES[key][1]>1 else '')+'; late members reconcile the same report once.'
    adventure.announce(world,room,message)


def validate(s):
    if s is None:return
    required={'version','legacy','stages','evidence','turnedIn'}
    if not isinstance(s,dict) or not required<=set(s) or set(s)-required-{'choices'} or s.get('version')!=1 or type(s['legacy']) is not bool:raise ValueError('Unsupported chapter record.')
    if not isinstance(s['stages'],dict) or not set(ORIGINAL_ORDER)<=set(s['stages'])<=set(ORDER) or any(v not in STATUSES for v in s['stages'].values()):raise ValueError('Invalid assignment stages.')
    for key,allowed in [('evidence',EVIDENCE),('turnedIn',set(ORDER))]:
        if not isinstance(s[key],list) or any(not isinstance(k,str) or k not in allowed for k in s[key]) or len(set(s[key]))!=len(s[key]):raise ValueError('Invalid chapter receipts.')
    if any(s['stages'].get(k)!='complete' for k in s['turnedIn']):raise ValueError('Turn-in receipt without completion.')
    choices=s.get('choices',{})
    if not isinstance(choices,dict) or set(choices)-{'seeds','relief'} or any(v not in ({'oakvale','dunmere'} if k=='seeds' else {'workers','farmers'}) for k,v in choices.items()):raise ValueError('Invalid settlement choices.')
    for key,fact in [('seeds','seeds_committed'),('relief','relief_committed')]:
        if (key in choices)!=(fact in s['evidence']):raise ValueError('Settlement choice and evidence disagree.')

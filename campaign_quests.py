"""Campaign metadata and world consequences; chapter_flow owns every quest state."""
import copy
import math
import time

MAIN=(
 ('upstream','What the Water Carries','dunmere','Trace the irrigation sample and farmstead records. Bring both findings to Tovin.',('upstream_sample','farm_record')),
 ('steward','The Steward’s Account','dunmere','Read the station account and agree how to help the affected workers or farmers.',('steward_account','relief_committed')),
 ('sluice_route','Below the Dry Canal','dunmere','Restore or isolate both tunnel mechanisms and reach the pumping chamber.',('valve_west','valve_east','chamber_reached')),
 ('pumping_finale','Water Within Reach','dunmere','Defeat the Harvest Warden, restore the main intake and report the limited recovery.',('warden_defeated','intake_restored')),
)
SIDE=(
 ('fire','A Place at the Fire','home','Speak to Sella and Orren, clear the workers’ approach and establish shelter. Report to Sella.',('worker_sella','worker_orren','shelter_lit')),
 ('letters','Letters That Never Arrived','home','Recover the road, brook and timber-camp letters; deliver all three together to Edda.',('letter_road','letter_brook','letter_yard')),
 ('seeds','The Last Dry Seeds','home','Recover the sealed seed supply and choose Oakvale’s reserve or Dunmere’s caravan. Report to Sella.',('seed_supply','seeds_committed')),
 ('root_sump','The Roots That Remain','dunmere','Accept Tovin’s optional challenge and clear the sealed root sump at the farmstead.',('sump_cleared',)),
)
MAGIC={k:('report:'+k,n) for k,n in [('fire',1),('letters',1),('seeds',1),('upstream',2),('steward',1),('sluice_route',2),('pumping_finale',2),('root_sump',1)]}
REPORTS={
 'fire':'Sella and Orren reach Oakvale. Their shelter and a cooking fire now protect the timber route; they are helping the village stores.',
 'letters':'Edda delivered the three letters. The missing grain had already separated families before the dragon arrived; the inn now keeps a noticeboard for travellers.',
 'seeds':'The sealed seeds are safe with the chosen settlement. The same personal reward is yours either way; a small planted reserve will appear there.',
 'upstream':'Tovin traced the same pale material through the channel and abandoned farm. The station account may explain why it entered the water.',
 'steward':'The steward hid the additive’s risks to keep the last harvest alive. Relief is committed to your chosen group; both routes keep the repair possible.',
 'sluice_route':'Both tunnel mechanisms are secured. The marked dry alcove holds an optional reserve; the eastern chamber contains the source of the roots.',
 'pumping_finale':'The intake runs at a safe rate. A second strip in Dunmere recovers and affected people receive relief. Most fields remain damaged. Ilyan brings a city dispatch to Dunmere: Aurelian’s trade roads are under attack. The root sump remains optional.',
 'root_sump':'The finite root sump is quiet. Farmers can use its dry store again. The pumping route and both villages remain open.',
}
CONTACTS={
 'water':['apprentice'],'watch':['recovered'],
 **{k:['tovin'] for k in ('failed_harvest','irrigation','mill_cellar','chapter_outcome','upstream','steward','sluice_route','pumping_finale','root_sump')},
 'fire':['sella'],'letters':['edda'],'seeds':['sella'],
}
NAMES={'sella':'Sella · stranded worker','orren':'Orren · timber carrier','edda':'Edda · innkeeper',
       'apprentice':'Nera · millwright apprentice','tovin':'Tovin · millwright','recovered':'Corin · recovered hunter'}
PORTRAITS={'sella':'Villager03','orren':'Villager06','edda':'Innkeeper','apprentice':'Villager05','tovin':'Villager07','recovered':'Villager04'}
FINDS={
 'road':[('letter_road','Weathered letter',180,355,'Mira wrote that the grain wagon never reached her family. She asks Edda to keep a room for her son.')],
 'brook':[('letter_brook','Letter in a reed case',250,395,'Orren’s sister sent flour money and a warning: the additive made roots grow through the sacks.')],
 'yard':[('letter_yard','Undelivered camp letter',400,430,'A carrier promised to bring seed before the frost. The letter was never loaded onto the missing wagon.')],
}


def state(room):return __import__('chapter_flow').ensure(room)
def done(room,key):return state(room)['stages'].get(key)=='complete'


def reconcile(room):
    s=room['adventure']['chapter'];visited=room['adventure']['visited']
    for key,available in [('fire','yard' in visited),('letters',bool(set(s['evidence'])&{'letter_road','letter_brook','letter_yard'}) or 'road' in visited),
                          ('seeds','yard' in visited),('root_sump',s['stages'].get('pumping_finale')=='complete')]:
        if available and s['stages'][key]=='unavailable':s['stages'][key]='offered'


def npc_position(room,key,x,y):
    import town_layout
    a=room['adventure'];hub=a['current'];cache=a.setdefault('homeNpcs',{});identity=hub+':campaign:'+key
    def visible(cx,cy):return all(not(abs(cx-h['x'])<100 and h['y']-128<cy<h['y']+70) and math.dist((cx,cy),(h['x'],h['y']+47))>78 for h in room['townLayout'])
    if identity not in cache or not visible(*cache[identity]):
        occupied=[v for k,v in cache.items() if k.startswith(hub+':') and k!=identity]
        portal=__import__('village_portals').shrine(room)
        candidates=[(cx,cy) for cy in range(110,461,35) for cx in range(100,881,35)
            if town_layout.clear(room['townLayout'],cx,cy,18) and math.dist((cx,cy),(portal['x'],portal['y']))>85
            and all(math.dist((cx,cy),v)>65 for v in occupied)]
        if not candidates:raise ValueError('No accessible campaign NPC position in this village.')
        preferred=[p for p in candidates if visible(*p)]
        cache[identity]=list(min(preferred or candidates,key=lambda p:math.dist(p,(x,y))))
    return cache[identity]


def features(room):
    import adventure
    a=room['adventure'];here=a['current'];s=state(room);result=[]
    for key,name,x,y,text in FINDS.get(here,[]):
        x,y=adventure.point(room,x,y);result.append(dict(id=key,name=name,x=x,y=y,kind='clue',description=text))
    if here=='yard':
        for key,x,y in [('sella',460,370),('orren',355,350)]:
            if done(room,'fire'):continue
            x,y=adventure.point(room,x,y);result.append(dict(id=key,name=NAMES[key],x=x,y=y,kind='talk',portrait=PORTRAITS[key]))
        for key,name,x,y in [('shelter_lit','Establish the workers’ shelter',480,430),('seed_supply','Open the sealed seed supply',800,405)]:
            x,y=adventure.point(room,x,y);result.append(dict(id=key,name=name,x=x,y=y,kind='mechanism'))
    if here in ('home','dunmere'):
        npcs=[('edda',290,360),('apprentice',370,300)] if here=='home' else [('tovin',330,300)]
        if here=='home' and done(room,'fire'):npcs += [('sella',260,420),('orren',180,300)]
        for key,x,y in npcs:
            x,y=npc_position(room,key,x,y);result.append(dict(id=key,name=NAMES[key],x=x,y=y,kind='talk',portrait=PORTRAITS[key]))
    return result


def contact(room,p,key,points=None):
    allowed={'runner',*CONTACTS.get(key,[])}
    return min((f for f in (points if points is not None else __import__('adventure').features(room)) if f['id'] in allowed and
        math.dist((p['x'],p['y']),(f['x'],f['y']))<=78),key=lambda f:(f['id']=='runner',math.dist((p['x'],p['y']),(f['x'],f['y']))),default=None) if not p.get('townInterior') else None


def action_hubs(key,default):
    # Sella travels home; her unfinished seed request remains available there.
    return {'home','yard'} if key in ('fire','seeds') else {default}


def npc_text(room,key):
    s=state(room);facts=set(s['evidence']);choices=s.get('choices',{})
    if key=='sella':
        return ('Orren and I are helping the stores now. Thank you for giving us a safe fire.' if done(room,'fire') else
                'We carried the last grain wagon. Orren is hurt and the approach is unsafe. Speak to us both, clear the marked approach, then use the shelter supplies.')+(
                ' The sealed seed supply can stay in Oakvale or travel to Dunmere. Neither settlement will refuse you.' if not done(room,'seeds') else
                ' The seeds went to '+('Oakvale’s reserve.' if choices.get('seeds')=='oakvale' else 'Dunmere’s caravan.'))
    if key=='orren':return 'I carried letters and seed, not weapons. Sella knows where the sealed supply was left. A fire and a clear approach are enough; we can make our own way home.' if not done(room,'fire') else 'We arrived safely. I am repairing supply crates while Sella tends the stores.'
    if key=='edda':return ('The letters have reached their families. Our noticeboard helps travellers find one another.' if done(room,'letters') else 'Three carriers left letters on the road, at the brook and in the timber camp. Bring them together; each tells us who the missing grain hurt.')+(' The workers brought new stores.' if done(room,'fire') else ' Our meals are smaller, but nobody is turned away.')
    if key=='apprentice':return 'Compare the brook outlet with the old wheel before blaming the dragon. I can interpret those findings here; you need not repeat the whole account to the runner.'
    if key=='recovered':return 'The creatures fled before the watch burned. Bring me the watch and seal observations; I can help interpret them. The runner still coordinates the roads.'
    if key=='tovin':
        if done(room,'pumping_finale'):return 'The intake is safe and one more strip is green. '+('Workers received clean shelters and masks.' if choices.get('relief')=='workers' else 'Farmers received the safe water reserve.')+' Ilyan has a dispatch from Aurelian. Reopening the grain road matters beyond Dunmere; speak to him here. The root sump remains optional.'
        if done(room,'chapter_outcome'):return 'The additive ledger points upstream. Inspect the irrigation sample and abandoned farm records together. The steward feared another failed harvest; his station account may explain what he concealed.'
        return 'The innkeeper can describe the shortages; I can read the water evidence. Compare all three field sites before reporting, then we can reopen the mill safely.'
    return 'We are keeping the road open.'


def talk(world,room,p,key):
    import progression,chapter_flow
    if key in ('sella','orren') and room['adventure']['current']=='yard':chapter_flow.evidence(room,'worker_'+key)
    progression.start_dialogue(p,'adventure_contact')
    d=p['dialogue'];d.update(contactId=key,contactTitle=NAMES.get(key,key),contactPortrait=PORTRAITS.get(key,'Villager02'),
        baseReaction=npc_text(room,key),reaction=npc_text(room,key),settlementChoices=choices(room,key))
    rows=chapter_flow.menu(room,p)
    d['serviceChoices']=__import__('settlement_events').services(room,p,key)
    d['runnerActions']=[a for a,status in [('accept','offered'),('report','ready-to-turn-in')] if any(q['status']==status and q['actionable'] for q in rows)]


def interact(world,room,p,point):
    import adventure,chapter_flow,progression
    key=point['id'];s=state(room)
    if key in NAMES:
        talk(world,room,p,key);adventure.save(world,room);return True
    found=next((row for rows in FINDS.values() for row in rows if row[0]==key),None)
    if found:
        chapter_flow.evidence(room,key);progression.inspect(p,found[1],found[4]+' Deliver the three letters together to Edda in Oakvale.')
    elif key=='seed_supply':
        chapter_flow.evidence(room,key);progression.inspect(p,'Sealed dry seeds','The wax seal kept these seeds viable. Sella can arrange a reserve for Oakvale or a caravan to Dunmere. Your personal reward is the same either way.')
    elif key=='shelter_lit':
        chapter_flow.require(room,'fire')
        if not all(k in s['evidence'] for k in ('worker_sella','worker_orren')):raise ValueError('Speak to both Sella and Orren before arranging the shelter.')
        if any(e.get('group','').startswith('workers-approach') for e in room['enemies']):raise ValueError('Clear the named workers’ approach before lighting the shelter.')
        chapter_flow.evidence(room,key);progression.inspect(p,'A place at the fire','A small cooking fire and dry shelter are ready. Sella and Orren can reach Oakvale once you report the arrangement.')
    else:return False
    adventure.save(world,room);return True


def choices(room,key):
    s=state(room)
    if key=='sella' and s['stages']['seeds'] in ('accepted','ready-to-turn-in') and 'seed_supply' in s['evidence'] and 'seeds' not in s.get('choices',{}):
        return [('seed_oakvale','Keep the seeds in Oakvale'),('seed_dunmere','Send the seeds to Dunmere')]
    if key=='tovin' and s['stages']['steward'] in ('accepted','ready-to-turn-in') and 'steward_account' in s['evidence'] and 'relief' not in s.get('choices',{}):
        return [('relief_workers','Prioritize the affected workers'),('relief_farmers','Prioritize the affected farmers')]
    return []


def choose(world,room,p,payload):
    import chapter_flow,adventure,progression
    if p.get('bot') or not p.get('connected',True) or p['status']!='alive':raise ValueError('Only a connected living hunter can choose a settlement outcome.')
    choice=payload.get('choice');field,value=('seeds',choice.removeprefix('seed_')) if isinstance(choice,str) and choice.startswith('seed_') else ('relief',str(choice).removeprefix('relief_'))
    key='seeds' if field=='seeds' else 'steward';s=state(room)
    valid={'seeds':{'oakvale','dunmere'},'relief':{'workers','farmers'}}
    if value not in valid[field]:raise ValueError('Choose one of the current settlement outcomes.')
    if field in s.get('choices',{}):return
    point=contact(room,p,key)
    if not point or (choice not in dict(choices(room,point['id']))):raise ValueError('Review this choice with Sella or Tovin after collecting the evidence.')
    humans=world._voting_players(room);cohort=sorted(x['id'] for x in humans)
    if any(x['status']!='alive' or x.get('townInterior') or math.dist((x['x'],x['y']),(point['x'],point['y']))>150 for x in humans):raise ValueError('Gather the connected party near this speaker before choosing. Offline hunters and companions do not vote.')
    ballot=room.setdefault('_campaignVotes',{}).get(field)
    if not ballot or ballot['cohort']!=cohort or time.monotonic()-ballot['createdAt']>90:ballot=room['_campaignVotes'][field]=dict(cohort=cohort,votes={},createdAt=time.monotonic())
    ballot['votes'][p['id']]=value
    if len(ballot['votes'])<len(humans):adventure.announce(world,room,'Settlement choice: '+str(len(ballot['votes']))+'/'+str(len(humans))+' votes. No outcome committed yet.');return
    counts={v:list(ballot['votes'].values()).count(v) for v in valid[field]}
    ordered=sorted(counts,key=counts.get,reverse=True)
    if counts[ordered[0]]==counts[ordered[1]]:
        room['_campaignVotes'].pop(field,None);adventure.announce(world,room,'The settlement vote is tied. Nothing changed; discuss and choose again.');return
    before=copy.deepcopy(s);s.setdefault('choices',{})[field]=ordered[0]
    chapter_flow.evidence(room,'seeds_committed' if field=='seeds' else 'relief_committed')
    if not adventure.save(world,room) and world.storage:
        room['adventure']['chapter']=before;room['_campaignVotes'].pop(field,None);raise ValueError('The choice was not saved. No outcome committed; vote again after storage recovers.')
    room['_campaignVotes'].pop(field,None);adventure.announce(world,room,'Settlement outcome agreed: '+ordered[0]+'. Rewards are equal for either choice.')


def reported(world,room,key):
    if key not in {k for k,*_ in SIDE}|{k for k,*_ in MAIN}:return
    import adventure
    reward='story:'+key
    amount={'upstream':14,'steward':0,'sluice_route':12,'pumping_finale':35,'root_sump':18}.get(key,10)
    adventure.reward(world,room,reward,amount,'story_choice')
    if key=='fire':adventure.announce(world,room,'Sella and Orren are now in Oakvale. Their cooking fire stays lit at the yard.')
    if key=='seeds':adventure.announce(world,room,'A small planted reserve will appear in '+('Oakvale.' if state(room)['choices']['seeds']=='oakvale' else 'Dunmere.'))
    if key=='upstream':adventure.announce(world,room,'Workers reopen the maintenance causeway: Eastern threshold ↔ pumping station. The direct route avoids the farmstead loop.')


def world_view(room):
    s=state(room)
    return dict(workers=done(room,'fire'),letters=done(room,'letters'),seedDestination=s.get('choices',{}).get('seeds') if done(room,'seeds') else None,
        relief=s.get('choices',{}).get('relief'),pumpingRestored=done(room,'pumping_finale'),shelter='shelter_lit' in s['evidence'])

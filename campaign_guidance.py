"""Derived next actions and optional recaps. Never grants or accepts anything."""
from collections import deque
import chapter_flow as chapter
import campaign_quests as quests


def action(room, player, key):
    import adventure
    state=chapter.ensure(room);status=state['stages'][key];facts=set(state['evidence'])
    spec=chapter.SPECS[key];contact=quests.NAMES.get(quests.CONTACTS.get(key,['runner'])[0],'Village Runner')
    if status in ('offered','ready-to-turn-in'):
        hubs=quests.action_hubs(key,chapter.action_hub(key,status))
        target=room['adventure']['current'] if room['adventure']['current'] in hubs else chapter.action_hub(key,status)
        if key in ('fire','seeds') and not quests.done(room,'fire'):target='yard'
        return target,('Report to ' if status=='ready-to-turn-in' else 'Accept from ')+contact+' · '+adventure.area_name(room,target)+'.',contact
    steps={
      'water':[('brook_outlet','brook','Inspect the pale brook outlet.'),('mill_wheel','mill_trail','Inspect the stopped mill wheel.')],
      'watch':[('watch_register','watch','Read the burned watch register.'),('network_seal','network','Inspect the network seal.')],
      'failed_harvest':[('dry_ditch','fields','Inspect the dry ditch.'),('rooted_crop','fields','Inspect the rooted crop.'),('empty_granary','fields','Inspect the empty granary.')],
      'upstream':[('upstream_sample','irrigation_channels','Take a sample from the contaminated channel.'),('farm_record','farmstead','Read the abandoned farm records.')],
      'steward':[('steward_account','pump_exterior','Read the steward’s account outside the pumping station.'),('relief_committed','dunmere','Speak to Tovin in Dunmere and choose relief for the workers or farmers.')],
      'sluice_route':[('valve_west','sluice_entry','Restore the clean western intake.'),('valve_east','sluice_gallery','Isolate the tainted eastern channel.'),('chamber_reached','pump_chamber','Explore the pumping heart.')],
    }
    for fact,area,text in steps.get(key,[]):
        if fact not in facts:return area,text,contact
    return None,None,contact


def route(room, origin, target, *, known_only=True):
    import adventure,dungeons,region_content
    known=room['adventure']['discovered'];queue=deque([(origin,[])]);seen=set()
    while queue:
        here,path=queue.popleft()
        if here==target:return path
        if here in seen:continue
        seen.add(here)
        for other,_,_ in adventure.AREAS[here]['exits']:
            if (known_only and other not in known) or dungeons.closed(room,here,other) or region_content.blocked(room,here,other) or __import__('campaign_expansion').closed(room,here,other):continue
            if {here,other}=={'road','bridge'} and not room['adventure']['bridge']:continue
            queue.append((other,path+[other]))
    return None


def enrich(room,player,tracked):
    import adventure,region_content
    result=dict(tracked);key=result['id'];state=chapter.ensure(room)
    if not state['legacy'] and key in chapter.SPECS and state['stages'][key]!='complete':
        target,text,contact=action(room,player,key)
        result.update(contact=contact,status=state['stages'][key],optional=bool(chapter.SPECS[key].get('optional')))
        if target and target in room['adventure']['discovered']:
            path=route(room,room['adventure']['current'],target)
            result.update(area=target,nextExit=path[0] if path else None,nextStep=text)
    # Suggest an earned/known waystone near the destination, never undiscovered land.
    result['travelPoint']=None
    target=result.get('area')
    if target:
        points=[(k,name+' village') for k,name in region_content.HUBS.items() if k in room['adventure']['visited']]
        points += [(v['area'],v['name']) for k,v in region_content.SHRINES.items() if k in region_content.shrine_state(room)['active']]
        options=[(len(path),name,area) for area,name in points if (path:=route(room,area,target)) is not None and len(path)<=2]
        if options:
            _,name,area=min(options);result['travelPoint']=dict(area=area,name=name)
    return result


def recap(room,player,tracked):
    import adventure
    state=chapter.ensure(room);main=[key for key in state['turnedIn'] if key in chapter.MAIN_ORDER]
    last=chapter.REPORTS[main[-1]] if main else 'The last grain caravan reached Oakvale. The missing deliveries link the woodland watch to Dunmere.'
    extension=room['adventure'].get('campaign',{})
    completed=[k for k in extension.get('reported',[]) if not __import__('campaign_content').QUESTS[k]['optional']]
    if completed:last='Completed: '+__import__('campaign_content').QUESTS[completed[-1]]['title']+'. '+('The dragon is defeated. The main campaign is finished; visits and optional stories remain.' if 'ending:campaign' in extension.get('facts',[]) else 'World changes and rewards remain saved; follow the tracked next step.')
    return dict(lastEvent=last,objective=dict(tracked),location=adventure.area_name(room,tracked['area']) if tracked.get('area') else 'Follow the known woodland trails',
        choices=[('Seeds: '+state['choices']['seeds'])] if 'seeds' in state['choices'] else [])


def journal(room,player,rows):
    result=[]
    for q in rows:
        if q['id'] in __import__('campaign_content').QUESTS:
            import campaign_expansion
            target=q['hub'];objective=q['outcome'] or q['objective']
            if q['status']=='accepted':
                missing=next((f for f in q['requires'] if f not in q['found']),None)
                if q['id']=='cinder_dragon':target,objective=campaign_expansion.cinder_step(room)
                elif missing:target,objective=campaign_expansion.objective_location(missing),campaign_expansion.instruction(missing)
            elif q['status'] in ('offered','ready-to-turn-in'):
                objective=('Accept from ' if q['status']=='offered' else 'Report to ')+q['contact']+' · '+__import__('adventure').area_name(room,q['hub'])+'.'
                if q['id']=='cinder_dragon' and q['status']=='offered':objective='Inspect the foothill pursuit marker to begin the final ascent. Four sanctuaries provide recovery and safe skill management.'
            if target not in room['adventure']['discovered']:target=None
            result.append(dict(id=q['id'],title=q['title'],status=q['status'],optional=q['optional'],objective=objective,contact=q['contact'],area=target,visibility='completed' if q['status']=='complete' else 'active'))
            continue
        target,text,_=action(room,player,q['id']) if q['status']!='complete' else (None,None,None)
        result.append(dict(id=q['id'],title=q['title'],status=q['status'],optional=bool(q.get('optional')),
            objective=q['outcome'] or text or q['objective'],contact=q['contact'],area=target,
            visibility='completed' if q['status']=='complete' else 'active'))
    return result

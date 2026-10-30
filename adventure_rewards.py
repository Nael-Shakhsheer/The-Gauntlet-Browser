"""Automatic personal rewards, with compatible receipts for older choices."""
import copy

ACTIVITIES={'dungeon:cave_survey','dungeon:cave','dungeon:tower','shrine','region','dungeon:sluice_survey'}
ACTIVITIES.update('story:'+k for k,*_ in (*__import__('campaign_quests').MAIN,*__import__('campaign_quests').SIDE))
ACTIVITIES.update('event:'+key for key in __import__('settlement_events').EVENTS)
ACTIVITIES.update('campaign:'+key for key in __import__('campaign_content').QUESTS)
ACTIVITIES.update(r['receipt'] for r in __import__('campaign_content').ENCOUNTER_REWARDS.values())


def options(key,hero):
    from game import CLASS_WEAPONS
    if key.startswith('campaign:'):return __import__('campaign_equipment').reward_options(key.removeprefix('campaign:'),hero)
    if key=='encounter:ravine_keeper':return ['cinder_heatward','phoenix_flask']
    if key=='encounter:summit_warden':return __import__('campaign_equipment').reward_options('cinder_dragon',hero)
    if key=='event:workshop':return ['pack_whistle' if hero=='Druid' else 'pilgrim_standard','summoners_staff' if hero=='Druid' else 'pursuit_blade']
    if key=='event:caravan':return ['forked_lens','rescuers_cuirass']
    if key in ('event:reserve','event:relief','event:channel_cache','event:lookout_cache','event:oath_trial'):return ['warding_tonic','mana_draught']
    choices={'story:fire':['healing_draught','warding_tonic'],'story:letters':['mana_draught','phoenix_flask'],
      'story:seeds':['oakguard_vest','stormguard_charm'],'story:upstream':['mana_draught','rescuers_cuirass'],
      'story:steward':['healing_draught','mana_draught'],'story:sluice_route':['stormguard_charm','phoenix_flask'],
      'story:pumping_finale':['aegis_of_dawn','starfall_blade'],
      'story:root_sump':['summoners_staff' if hero=='Druid' else 'arcane_conductor' if hero in ('Wizard','Archer','Cleric') else 'pursuit_blade','rescuers_cuirass']}
    if key in choices:return choices[key]
    if key=='dungeon:sluice_survey':return ['warding_tonic','phoenix_flask']
    if key=='dungeon:cave_survey':return ['warding_tonic','mana_draught']
    if key=='dungeon:cave':return ['phoenix_flask','stormguard_charm']
    if key=='shrine':return ['rescuers_cuirass','stormguard_charm']
    if key=='region':return ['aegis_of_dawn','starfall_blade']
    build={'Knight':'pursuit_blade','Wizard':'arcane_conductor','Archer':'arcane_conductor',
           'Cleric':'rescuers_cuirass','Rogue':'pursuit_blade','Druid':'summoners_staff',
           'Bard':'rescuers_cuirass','Healer':'rescuers_cuirass'}[hero]
    return [CLASS_WEAPONS[hero],build]


def offer(player,key,title):
    if key in player.setdefault('resolvedRewards',{}):return
    player.setdefault('pendingRewards',{}).setdefault(key,dict(title=title,options=options(key,player['class'])))


def deliver(world,room,p,key,title):
    if key in p.setdefault('resolvedRewards',{}):return None
    from game import ITEMS
    choices=p.get('pendingRewards',{}).get(key,{}).get('options') or options(key,p['class'])
    owned={i['key'] for i in p['inventory']+p['toolSlots']+p['utilitySlots'] if i}
    item=next((i for i in choices if i not in owned),choices[0])
    full=len(p['inventory'])>=__import__('pouch_storage').capacity(p)
    converted=ITEMS[item]['sell'] if full else 0
    if full:room['runes']+=converted
    else:p['inventory'].append(world._make_item(item))
    p['resolvedRewards'][key]=dict(item=item,delivery='sell' if full else 'pouch',soldRunes=converted,replaced=None)
    p.setdefault('pendingRewards',{}).pop(key,None)
    return dict(id=p['id'],name=p['name'],item=ITEMS[item]['name'],convertedRunes=converted)


def settle(world,room):
    """Migrate earned pending choices inside the next confirmed save transaction."""
    campaign_reports=room['adventure'].get('campaign',{}).get('reported',[])
    earned=[('campaign:'+key,__import__('campaign_content').QUESTS[key]['title']) for key in campaign_reports]
    earned += [(spec['receipt'],key.replace('_',' ').title()) for key,spec in __import__('campaign_content').ENCOUNTER_REWARDS.items() if spec['receipt'] in room['adventure']['claimed']]
    if not any(p.get('pendingRewards') or any(k not in p.get('resolvedRewards',{}) for k,_ in earned) for p in room['players'].values()):return None
    before=dict(players=copy.deepcopy(room['players']),runes=room['runes'],history=copy.deepcopy(room['adventure'].get('rewardHistory',[])))
    for p in room['players'].values():
        for key,title in earned:
            if key not in p.get('resolvedRewards',{}):deliver(world,room,p,key,title)
        for key,row in list(p.get('pendingRewards',{}).items()):
            recipient=deliver(world,room,p,key,row['title'])
            if recipient:
                for receipt in room['adventure'].get('rewardHistory',[]):
                    if receipt['id']==key:receipt['recipients'].append(recipient)
    return before


def rollback(room,before):
    for pid,old in before['players'].items():room['players'][pid].clear();room['players'][pid].update(old)
    room['runes']=before['runes'];room['adventure']['rewardHistory']=before['history']


def validate(p):
    from game import ITEMS
    for field in ('pendingRewards','resolvedRewards'):
        rows=p.get(field,{})
        if not isinstance(rows,dict) or any(k not in ACTIVITIES for k in rows):raise ValueError('Unsupported reward choice.')
    for key,row in p.get('pendingRewards',{}).items():
        if not isinstance(row,dict) or not isinstance(row.get('title'),str) or not 1<=len(row.get('options',[]))<=2 or any(k not in ITEMS for k in row['options']):raise ValueError('Invalid pending reward.')
        # A prior class change may leave an earned choice for the original hero.
        allowed=set().union(*(options(key,h) for h in __import__('game').CLASSES))
        if not set(row['options'])<=allowed:raise ValueError('Unsupported reward options.')
    if set(p.get('pendingRewards',{})) & set(p.get('resolvedRewards',{})):raise ValueError('Reward cannot be pending and claimed.')


def claim(world,room,p,payload):
    from game import ITEMS
    import adventure
    key=str(payload.get('reward',''));item=str(payload.get('item',''))
    if key in p.setdefault('resolvedRewards',{}):return  # Retry does not pay again.
    pending=p.setdefault('pendingRewards',{}).get(key)
    if not pending or item not in pending['options']:raise ValueError('That reward is unavailable.')
    before=copy.deepcopy(p);old_runes=room['runes'];history=copy.deepcopy(room['adventure'].get('rewardHistory',[]))
    delivery=payload.get('delivery','pouch');sold=0;replaced=None
    if delivery=='sell':sold=ITEMS[item]['sell'];room['runes']+=sold
    elif delivery=='pouch':
        if len(p['inventory'])>=__import__('pouch_storage').capacity(p):
            replaced=next((i for i in p['inventory'] if i['id']==payload.get('replace')),None)
            if not replaced:raise ValueError('Pouch full. Choose an item to sell and replace, or sell this reward for shared Runes.')
            p['inventory'].remove(replaced);room['runes']+=replaced['sell']
        p['inventory'].append(world._make_item(item))
    else:raise ValueError('Unknown reward delivery.')
    result=dict(item=item,delivery=delivery,soldRunes=sold,replaced=replaced['key'] if replaced else None)
    p['resolvedRewards'][key]=result;del p['pendingRewards'][key]
    for receipt in room['adventure'].get('rewardHistory',[]):
        if receipt['id']==key:
            receipt['recipients'].append(dict(name=p['name'],item=ITEMS[item]['name'],convertedRunes=sold,replaced=ITEMS[replaced['key']]['name'] if replaced else None))
    message=p['name']+' chose '+ITEMS[item]['name']+ (f' · sold for {sold} shared Runes.' if sold else ' · added to pouch.')
    if replaced:message+=' Sold '+replaced['name']+f' for {replaced["sell"]} shared Runes to make room.'
    if not adventure.save(world,room) and world.storage:
        p.clear();p.update(before);room['runes']=old_runes;room['adventure']['rewardHistory']=history
        raise ValueError('Reward was not committed because storage failed. Your choice, pouch and shared Runes are unchanged.')
    adventure.announce(world,room,message)


def view(world,p):
    result=[]
    for key,row in p.get('pendingRewards',{}).items():
        choices=[]
        for item in row['options']:
            candidate=world._make_item(item);candidate.pop('id',None)
            candidate['alreadyOwned']=any(i and i['key']==item for i in p['inventory']+p['toolSlots'])
            choices.append(candidate)
        result.append(dict(id=key,title=row['title'],options=choices))
    return result

"""Stable new-region item IDs. Existing effect families provide real tradeoffs."""
import copy
ITEMS={
 'city_duelist_edge':dict(name='Aurelian Duelist Edge',kind='weapon',damage=7,effect='pursuit',effectLabel='Dash follow-up / direct damage -15%',description='+7 damage. Direct damage is reduced15%; the next direct ability within2s after a dash gains60% damage under existing pursuit rules.'),
 'city_rescue_plate':dict(name='Evacuation Plate',kind='armor',armor=2,effect='rescuer',effectLabel='Rescue protection / light armor',description='Only 2 ordinary armor; grants the existing protective rescue effect while reviving.'),
 'city_signal_focus':dict(name='Militia Signal Focus',kind='weapon',damage=4,effect='conductor',effectLabel='Projectile chain / weaker first hit',description='+4 damage. Projectiles chain using the conductor rules, trading away initial projectile damage.'),
 'veil_root_standard':dict(name='Rootsong Standard',kind='armor',armor=1,effect='pilgrim',effectLabel='Mobile fields / shorter duration',description='Support fields follow their caster but expire 40% sooner; only 1 armor.'),
 'veil_bond_staff':dict(name='Living Bond Staff',kind='weapon',damage=4,effect='summoner',effectLabel='Durable summons / less direct damage',description='+4 damage. Existing summoner tradeoff improves summon health and reduces direct damage.'),
 'veil_echo_lens':dict(name='Essence Echo Lens',kind='weapon',damage=4,effect='forked',effectLabel='Arc chains / weaker first hit',description='+4 damage. Arc Bolt gains the existing forked-lens jumps and range but loses first-hit damage.'),
 'cinder_pursuit_blade':dict(name='Crownfire Pursuit Blade',kind='weapon',damage=11,effect='pursuit',effectLabel='Dash follow-up / direct damage -15%',description='+11 damage. Direct damage is reduced15%; one follow-up within2s after a dash gains60% damage under existing pursuit rules.'),
 'cinder_shelter_plate':dict(name='Ash Shelter Plate',kind='armor',armor=5,effect='rescuer',effectLabel='Revive safely / lower ordinary armor',description='5 armor instead of the finest heavy plate; rescue protection supports dangerous revives.'),
 'cinder_pack_focus':dict(name='Ember Pack Focus',kind='weapon',damage=7,effect='pack',effectLabel='Directed summons / owner damage -25%',description='+7 damage. Summons follow your selected visible target under pack-whistle rules; owner direct damage is reduced 25%.'),
 'city_field_dressing':dict(name='City Field Dressing',kind='heal',heal=55,slot='utility',description='Restore55 HP. A marked infirmary supply; one use.'),
 'veil_essence_vial':dict(name='Rootsong Essence Vial',kind='mana',mana=60,slot='utility',description='Restore60 mana. One use; no cooldown reset.'),
 'cinder_heatward':dict(name='Cinder Heatward',kind='ward',factor=.5,duration=18,slot='utility',description='Take50% less damage for18 seconds. One use; no immunity to marked attacks.'),
}
for key,item in ITEMS.items():
    item.setdefault('slot','tool');item.update(rarity='Rare' if key.startswith(('city_','veil_')) else 'Epic',
        price=40 if key.startswith('city_') else 48 if key.startswith('veil_') else 64,
        sell=20 if key.startswith('city_') else 24 if key.startswith('veil_') else 32,
        color='#d1b979' if key.startswith('city_') else '#8cc7a7' if key.startswith('veil_') else '#df9b65')

def reward_key(quest):
    if quest.startswith('city_'):return 'city_field_dressing' if quest in ('city_medicine','city_infirmary','city_rescue') else 'city_signal_focus' if quest in ('city_commanders','city_terrace') else 'city_rescue_plate'
    if quest.startswith('veil_'):return 'veil_bond_staff' if quest=='veil_archmage' else 'veil_root_standard' if quest=='veil_siphons' else 'veil_essence_vial'
    return 'cinder_shelter_plate' if quest=='cinder_dragon' else 'healing_draught'

def reward_options(quest,hero):
    if quest in ('city_rescue','city_infirmary','city_medicine'):return ['city_field_dressing','mana_draught']
    if quest.startswith('city_'):
        preferred='city_duelist_edge' if hero in ('Knight','Rogue') else 'city_rescue_plate' if hero in ('Healer','Bard','Cleric') else 'city_signal_focus'
        return [preferred,'city_rescue_plate' if preferred!='city_rescue_plate' else 'city_signal_focus']
    if quest.startswith('veil_'):
        preferred='veil_bond_staff' if hero=='Druid' else 'veil_echo_lens' if hero=='Wizard' else 'veil_root_standard' if hero in ('Knight','Cleric','Bard','Healer') else 'veil_essence_vial'
        return [preferred,'veil_essence_vial' if preferred!='veil_essence_vial' else 'veil_root_standard']
    return ['cinder_pack_focus' if hero=='Druid' else 'cinder_pursuit_blade' if hero in ('Knight','Rogue','Archer') else 'cinder_shelter_plate','cinder_heatward'] if quest=='cinder_dragon' else ['healing_draught','mana_draught']

def manifest():return {k:dict(id=k,**copy.deepcopy(v),artFamily='item-'+k,artStatus='awaiting-sprite-chat') for k,v in ITEMS.items()}

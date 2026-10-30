"""Presentation contracts derived from existing authoritative ability shapes.

No damage, range, target, collision or recharge rule is changed here.
"""
import math

CAMPAIGN_FAMILIES={
 'formation_break':'sweep','oath_link':'ward','citadel_fall':'fracture',
 'ember_seam':'fire','prism_fracture':'frost','star_corridor':'lightning',
 'pinning_line':'arrow','snare_exchange':'trap','arrow_corridor':'arrow',
 'purging_salve':'mixture','sealed_vessel':'seal','lustral_front':'cleanse',
 'feint_cut':'cut','shadow_anchor':'shadow','nightfall_execution':'cut',
 'bramble_lane':'root','renewal_exchange':'growth','pack_reckoning':'growth',
 'syncopated_break':'resonance','countermelody':'voice','concordant_finale':'resonance',
 'judgment_ray':'heal','lifeline_surge':'rescue','dawn_deluge':'heal',
}
FAMILIES={
 'shield_bash':'shield','cleaving_arc':'sweep','iron_wall':'ward','challenge':'voice',
 'guardian_cry':'herald','earthshaker':'fracture','arc_burst':'arcane','frost_lance':'frost',
 'spell_surge':'arcane','blink':'phase','team_aegis':'ward','arcane_cataclysm':'arcane',
 'piercing_volley':'arrow','snare_shot':'root','eagle_eye':'mark','quickstep':'wind',
 'rain_of_arrows':'arrow','deadeye':'arrow','radiant_flask':'mixture','sanctified_throw':'mixture',
 'splash_mend':'heal','blessed_vial':'seal','sanctuary_rain':'heal','cleansing_splash':'cleanse',
 'backstab':'cut','fan_of_blades':'cut','vanish':'shadow','shadowstep':'shadow',
 'death_bloom':'cut','execution':'cut','briar_burst':'root','thornshot':'thorn',
 'lightning_bird':'lightning','fire_wolf':'fire','ice_bear':'frost','nature_golem':'growth',
 'discord_note':'resonance','quickstring':'resonance','battle_anthem':'resonance','fleet_rhythm':'wind',
 'grand_crescendo':'resonance','rallying_chord':'heal','life_spark':'heal','healing_ray':'heal',
 'major_mend':'heal','quick_revival':'rescue','miracle':'heal','mass_revival':'rescue'}
KINDS={'rush':'shield','banner':'herald','parry':'shield','barrier':'ward','triage':'heal',
 'beacon':'rescue','root_burst':'root','rift':'rift','phase':'phase','trap':'trap','sidestep':'arrow',
 'mark':'mark','sunburst':'mixture','draft':'mixture','hallowed':'seal','smoke':'shadow',
 'venom':'poison','crosscut':'cut','spring':'growth','call':'growth','refrain':'resonance',
 'echo':'resonance','cadence':'resonance','mercy_lance':'heal','repulse':'rescue'}
ASCENDED={'Knight':'herald','Wizard':'lightning','Archer':'astral','Cleric':'seal',
 'Rogue':'shadow','Druid':'growth','Bard':'resonance','Healer':'rescue'}

def describe(ability,player,origin,target):
    kind=ability['kind'];hero=player['class']
    if kind=='campaign_skill':
        shape={'line':'line','circle':'circle','target':'circle','field':'zone','move':'movement','allies':'recipients','ally':'recipients','self':'point'}[ability['shape']]
        mechanic=ability['mechanic'];reach=ability['range']
        radius=ability.get('radius',reach if shape in ('line','circle') else 110 if mechanic=='root' else 115 if mechanic=='arc' else 110 if mechanic=='arrows' else 95 if mechanic=='burn' else 100 if ability['shape']=='target' else 0)
        # Width matches campaign_skills.cast's authoritative lane, including its
        # existing rank/modifier selection. This packet has no gameplay effect.
        import hero_skills
        width=ability.get('width',100 if mechanic in ('ward','mend') else 90 if mechanic=='interrupt' else 55 if mechanic=='judgment' else 65 if mechanic=='push' else 70 if hero_skills.rank(player,'prism_fracture') else 50)
        dx,dy=target[0]-origin[0],target[1]-origin[1];length=max(.001,math.hypot(dx,dy))
        if mechanic=='execute':shape='target';radius=0
        if mechanic in ('vessel','lifeline'):radius=90
        if mechanic=='conceal':radius=100
        if mechanic=='trap':radius=90
        return dict(campaign=True,abilityId=ability['id'],family=CAMPAIGN_FAMILIES[ability['id']],shape=shape,
                    center=list(target if ability['shape'] in ('target','field','ally') else origin),radius=radius,
                    origin=list(origin),range=reach,width=width,direction=[dx/length,dy/length],los=True)
    family=ASCENDED[hero] if kind.startswith('ascend_') else KINDS.get(kind,FAMILIES.get(ability['id'],'arcane'))
    shape='point';center=list(target);radius=0
    if kind=='area':shape='circle';center=list(origin);radius=ability['range']
    elif kind in ('root_burst','sunburst'):shape='circle';radius=95 if kind=='root_burst' else 100
    elif kind in ('smoke','refrain','rush','crosscut','repulse'):
        shape='circle';center=[player['x'],player['y']];radius=90 if kind=='rush' else 95 if kind=='crosscut' else ability['range']
    elif kind in ('team_heal','team_revive','revive','triage','barrier','team_ward','team_speed','team_damage','cadence','draft'):shape='recipients'
    elif kind in ('blink','phase','sidestep','dash_strike'):shape='movement';center=[player['x'],player['y']]
    elif kind in ('banner','beacon','rift','trap','hallowed','spring'):shape='zone'
    elif kind=='summon':shape='summon';center=[player['x'],player['y']]
    return dict(family=family,shape=shape,center=center,radius=radius,origin=list(origin),range=ability.get('range',0),los=kind in KINDS)

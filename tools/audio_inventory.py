"""Regenerate the event-to-cue manifest from the current ability roster."""
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

ROOT=Path(__file__).resolve().parents[1]
scratch=ROOT/'.test-tmp';scratch.mkdir(exist_ok=True)
import run_storage
with tempfile.TemporaryDirectory(prefix='audio-inventory-',dir=scratch) as directory:
    original=run_storage.RunStorage.__init__
    with patch.object(run_storage.RunStorage,'__init__',lambda self,_path:original(self,directory)):
        from game import ABILITY_SETS,ability_record
        import hero_skills,ascension
records=[]
for hero,abilities in ABILITY_SETS.items():
    for item in abilities:
        ability=ability_record(item)
        name='frost-launch' if ability['id']=='frost_lance' else hero.lower()+'-'+ability['attackType']
        records.append(dict(hero=hero,id=ability['id'],name=ability['name'],category=ability['attackType'],kind=ability['kind'],
            acceptedCue=name,variants=[name+'-1',name+'-2'] if ability['attackType']=='light' else [],
            impactCue='frost-impact' if ability['id']=='frost_lance' else 'actual material/element; audio-routing.js',
            timing='Accepted cast after validation; impact only on real damage. Healing/ward/rescue/summon events describe actual recipients.',
            sustained='No repeated cast tone; periodic actual impacts/restoration are coalesced.'))
events={
    'ability':'class-category; frost_lance → frost-launch',
    'hit':'class-impact; Ice → ice-impact; summon hits quieter and globally coalesced',
    'hurt':'hurt; fully blocked → hit-barrier', 'heal':'heal','ward':'ward','down':'down','revive':'revive','dash':'dash',
    'windup':'enemy-windup; boss → boss-warning; targets of ordinary windups have warning priority',
    'release':'enemy-release (basic attack resolution, or windup enters charge/recovery; cancellation stays silent)',
    'boss_phase':'boss-warning','summon':'summon-fire/ice/storm/nature','summon_attack':'quiet druid-light',
    'material':'wood-impact for crates; stone-impact for rocks','loot':'loot; Epic/Legendary → discovery','curse':'curse',
    'equip':'equip','purchase':'purchase','quest':'clear; region → boss-complete','repair':'repair','restore':'restore',
    'discovery':'discovery','complete':'clear; guardian/final floor → boss-complete','wave':'interact',
    'encounter':'boss-warning','travel':'interact (live observed travel only)','rest':'restore'}
known={(r['hero'],r['id']) for r in records}
for hero,nodes in hero_skills.TREES.items():
    for n in nodes:
        if n['type']!='ability':continue
        a=n['ability']
        if (hero,a['id']) in known:continue
        records.append(dict(hero=hero,id=a['id'],name=a['name'],category=a['attackType'],kind=a['kind'],
            acceptedCue=hero.lower()+'-'+a['attackType'],source='Adventure skill tree'))
    a=ascension.ability({'class':hero})
    records.append(dict(hero=hero,id=a['id'],name=a['name'],category='special',kind=a['kind'],source='Ascension',
        acceptedCue=hero.lower()+'-special (quiet commitment)',releaseCue='ascended-'+hero.lower(),
        transformedLightCue='ascended-'+hero.lower()+'-light',transformationCue='ascend-'+hero.lower(),releaseDelaySeconds=.6))
events.update(projectile_launch='Actual launch only: physical/element family, hostile variants, class-specific transformed variants',
    projectile_impact='Confirmed collision only: elemental impact or physical flesh/metal/wood/stone/barrier; suppress duplicate hit sample',
    hit='Quiet material/element variants; 200ms per owner; DOT 500ms shared bucket; significant is presentation metadata, not a new critical rule',
    blocked='hit-barrier (no punishing hurt cue)',enemy_defeat='defeat-soft coalesced 320ms; boss drives victory music',
    summon_attack='Silent: actual launch/impact is sufficient',material='hit-wood / hit-stone, coalesced with projectile cover impact',
    conversation_open='conversation-open UI',conversation_close='conversation-close UI',inspect='inspect UI',
    door='door UI',stairs='stairs UI',mechanism='mechanism UI',skill_learn='skill-learn UI',loadout='equip UI',sell='purchase UI',
    rune_gain='rune-gain UI',rune_spend='rune-spend UI',quest_accept='quest-accept UI',quest_progress='quest-progress UI',quest_report='quest-report shared notification; one outcome per cause',
    shrine_activate='shrine-activate positional world cue; combines attunement outcome',portal_charge='portal-charge UI accepted channel; not arrival',portal_arrive='portal-travel live arrival only',
    ascension='One-time class transformation, positional for teammates',ascended_release='Class-specific cue at actual signature resolution')
document=dict(version=2,source='Authoritative presentation events; not gameplay inputs',
    transport=dict(limit=128,ttlSeconds=3,maximumAudibleAgeSeconds=.75,baselineGapMilliseconds=750,
                   stableIdentity='scene epoch + increasing integer event ID',privateEvents='loot/equipment/purchases',saved=False),
    abilities=records,events=events,atmosphere=dict(village='quiet filtered procedural bed + amb-village',woodland='bed + amb-woodland',underground='bed + amb-chamber',tower='bed + amb-tower',boss='bed + amb-boss',dry='Dunmere/fields/mill bed + amb-dry/creak',landmarks='nearest supported magical/water/fire feature, never a loop per prop'),
    music=json.loads((ROOT/'static/music/manifest.json').read_text()),
    projectileFamilies=['arrow','blade','fire','frost','lightning','arcane','sacred','nature','mixture','tonal','shadow','stone'],
    unsupported=['No crossbow or separate physical-bolt mechanic exists; no invented crossbow cues.','No supported critical-hit flag; significant means actual direct damage above a presentation threshold.'],
    mix=dict(defaults=dict(master=1,music=.16,effects=.4,ambience=.12,ui=.3),settingsVersion=3,
        maxEffectsVoices=10,ordinaryConcurrency=3,impactsConcurrency=2,summonConcurrency=1,periodicConcurrency=1,
        decodedEffectsBytes=8*1024*1024,decodedMusicBytes=32*1024*1024,cachedTracks=2,
        masterMute='Stops effects, procedural beds, current/fading score; no queued combat replay'),
    gaps=['Variants distinguish class/category, not every ability with its own exclusive timbre.',
          'No continuous burn/bleed/summon hum: actual damage is intentionally coalesced.',
          'Flesh is the fallback for unarmored actors; explicit armor/structures/cover define other materials, not fabricated anatomy.',
          'Entrance/floor/chamber/exit changes share a quiet transition cue; no voice announcements.',
          'A small original synthesized score is integrated; no acoustic performances or realistic environmental recordings.',
          'Human headphone/speaker listening and physical mobile audio-policy/performance review remain outstanding.'])
(ROOT/'art/audio/event-manifest.json').write_text(json.dumps(document,indent=2)+'\n',encoding='utf-8')
metrics=json.loads((ROOT/'art/audio/metrics.json').read_text())
summary=dict(files=len(metrics),totalBytes=sum(m['bytes'] for m in metrics.values()),
    durationSeconds=[min(m['seconds'] for m in metrics.values()),max(m['seconds'] for m in metrics.values())],
    peak=[min(m['peak'] for m in metrics.values()),max(m['peak'] for m in metrics.values())],
    rmsDBFS=[min(m['rmsDBFS'] for m in metrics.values()),max(m['rmsDBFS'] for m in metrics.values())],
    clippedSamples=sum(m['clippedSamples'] for m in metrics.values()),
    nonzeroBoundaries=sum(any(m['edgeSamples']) for m in metrics.values()),abilities=len(records))
(ROOT/'art/audio/summary-metrics.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary))

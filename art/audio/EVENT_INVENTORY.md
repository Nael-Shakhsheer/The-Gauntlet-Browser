# Feedback audit — 2026-10-11

Historical first pass. The current October 16 routing audit and limitations are
in [OVERHAUL_2026-10-16.md](OVERHAUL_2026-10-16.md). The regenerated
`event-manifest.json` now covers the current roster, skill tree and Ascension.

`event-manifest.json` is the complete 48-ability roster and runtime cue mapping.
Regenerate it with `python tools/audio_inventory.py`. Sound parameters, seeds,
export fingerprints and measurements are separate reproducible manifests.

## Findings and implementation

The old pass shared one Special and Ultimate across the roster, grouped Knight
and Rogue Light, inferred hits/status/chests from snapshots and notices, and
identified scenes mostly by room/player/stage. It could miss between-poll events,
duplicate heal/cast/impact feedback, and carry IDs across same-stage Adventure
travel. Audio listener distance also needed explicit independence from map zoom.

| Event | Confirmed source and cue | Visual information / restraint |
| --- | --- | --- |
| Every hero Light/Special/Ultimate | Validated `_cast_ability`, class/category family; frost launch override | Existing cast pose and directional art; optional particle budget |
| Cast acceptance / launch | One accepted cue after validation, before resolution; not from input, animation timestamps or buttons | Existing launches remain synchronized with actual projectiles |
| Actual hero hit | `_damage_enemy`, class impact; ice projectile and summon override | Brief class/element ticks at the struck target |
| Ongoing damage / hazards | Actual damage events, coalesced per owner / pack | Existing hazard outlines remain essential; no perpetual cast hum |
| Enemy windup | 20 Hz server transition of stable pending-attack token | Existing windup progress, zones, committed facing |
| Enemy release | Actual basic attack or pending attack entering charge/recovery; cancelled windups do not release | Existing release art, recovery pose and exposure labels |
| Boss transition / ambush | Phase increase / actual ambush effect, stable warning | Existing labels and readable warning artwork |
| Damage / wards | Actual HP damage, protected impact; wards recorded at resolution | Existing damage tint plus short ward outline |
| Healing | Actual heal resolution; transition fallback for passive/legacy restoration | Small recipient plus; healing between damage ticks is retained |
| Down / revive | Authoritative down / `_restore_ally`; fixed consistent down and rescue cues | Downed sprites, party health and revive targets remain visible |
| Summon arrival / attack | Actual companion creation and attack; affinity emergence, quiet globally coalesced attacks/hits | Existing emergence and attack art; shared decorative particle budget |
| Dash | Accepted dash after validation, one dash cue | Existing dash remains; rejected cooldown input is silent |
| Loot / equipment / purchase | Successful chest resolution, equip and purchase, private events; rarity-dependent loot cue | Brief rarity label / existing pouch and receipts |
| Quest / bridge / shrine / discoveries | Once-only reward receipt; clear / repair / restore / discovery | Small readable confirmation, existing objective state remains authoritative |
| Dungeon entrance / chamber / floor / exit | Actual Adventure `enter`, one quiet live travel cue | Existing area heading, dungeon status, stairs and map |
| Dungeon start / wave | Accepted bell / seal; wave counter transition | Existing sealed-exit and wave countdown information |
| Dungeon floor / guardian completion | One explicit completion; final boss has reserved longer cue; reward emissions do not duplicate it | Small CLEARED mark; permanent route/quest messages remain |
| Inn bed | Accepted rest in both modes | Existing checkpoint text; no save cue from merely talking to innkeeper |
| Cover | Actual damage to cover; wood/stone impact | Small material ticks; scenery stays stable |

## Family identities

Knight uses filtered weight/metal; Rogue short filtered blade noise; Archer a
falling bow release; Wizard arcane triangle charge/discharge and frost; Druid
filtered elemental texture and four summon emergence cues; Cleric sine bottle
pitch and splash-shaped envelopes; Bard restrained tonal pitch jumps; Healer
rising restorative tones. Light has three deterministic variants per class.
Special/Ultimate share each class's family with their own envelope/pitch profile.
This distinguishes classes and categories, not all 48 choices with exclusive
sounds. Warning, down and rescue cues do not randomize.

## Event contract and limits

`feedback.py` retains at most 128 events for three seconds in memory, resetting
its random epoch when the Adventure area/dungeon location/stage changes. IDs
increase within the epoch. Public snapshots include relative age and a cursor;
private events are filtered without changing that cursor. Checkpoints exclude
this stream. No extra gameplay request produces an audio event.

The client consumes each fresh ID once, including while muted. First snapshots,
new identities, reconnect gaps over 750 ms, refresh and hidden-tab return form a
silent baseline. Events older than 750 ms are discarded. Live observed travel
may play its fresh transition cue, never combat from the abandoned scene.
Events during loading/autoplay restriction are not queued for late playback.

Low-priority effects occupy at most six voices, local abilities eight and
critical danger/rescue ten. Replacement fades before the new voice begins.
Pack/summon cues share rate buckets; critical per-player cues are independent.
Quadratic attenuation reaches silence at 800 world units; pan is limited to
±0.65. The listener always uses the local hero's authoritative world position.
Visual feedback is bounded to 24 marks / 64 optional ticks (24 reduced), and
the existing choreography has its own shared 64-particle budget (20 reduced).
Essential actor labels and danger zones draw above optional feedback.

## Remaining gaps and review

No authored realistic environmental recordings were available. Atmosphere uses
a very quiet seeded, filtered procedural bed and sparse Bfxr accents, with a
separate bus. There is no music soundtrack. Nearest supported landmarks get one
quiet accent, not identical loops per prop. Asset failures and mute do not remove
visual warnings.

Elemental enemy body materials are not separately authored. Mana/buff expiration,
every dialogue advancement, every scenery prop and persistent hazard loops are
intentionally not sonified. Dungeon entrance/floor/exit cues share a restrained
transition family. Simple windup/recovery transitions are sampled at the fixed
server tick; no gameplay timings were changed.

Browser playback and visual review were performed, but this agent has no audio
listening tool. Actual headphone/speaker listening is **not completed**. Use
`preview.html` and `mixed-combat.wav` to review timbre, fatigue, balance and
warning recognition. The mix is an authored reference using actual exports at
approximate pre-compressor game gains, not a live multiplayer recording. Physical
phone speakers, Bluetooth, device autoplay policies and four physical players
remain untested. Automated measurements cannot resolve those gaps.

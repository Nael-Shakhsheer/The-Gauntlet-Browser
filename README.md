# The Gauntlet

## October 16 GitHub source release

This release includes the current Adventure expansion, opening battle, skills and
Ascension, travel shrines/Soul Transport Crystal, enemy awareness and outdoor
respawns, themed interface/artwork, audio/music and demand-loading improvements.
Validation: **364 Python tests and 26 client suites passed**, plus static JS syntax
checks. Private saves, credentials and large artwork sources are not included.
Render auto-deploy is off; updating GitHub does not deploy the hosted game.

## October 16: Adventure systems update

This local update adds enemy awareness, exploration dash, NPC response choices,
map-based transport, personal Soul Transport Crystals, controlled outdoor
respawns, cottage recovery and the eastern approach beyond Dunmere. It supersedes
the older finite-enemy and free trail-recall descriptions below. Existing saves,
Gauntlet checkpoints, artwork, audio, following camera and mobile landscape
requirement are preserved. The source release above includes this work; hosting
is updated separately.

- **Vanish:** enemies investigate, detect, search the last known position for
  three seconds, then return to their territory. Brief `!` / `?` cues replace
  permanent alert clutter. Invisible heroes cannot be acquired through taunt or
  homing. Successful offensive casts break concealment; ongoing bleed and summons
  do not reveal their hidden owner. Previously committed attacks retain their
  aim, and incidental projectiles/hazards can still hurt a hidden hero.
- **Dash:** Space or the Dash button works on Adventure trails, village exteriors
  and dungeon corridors. Roots, downing, conversations, menus, collision, seals
  and recharge still apply. Gauntlet retains its existing combat dash rule.
- **Conversations:** choose questions, encouraging/skeptical replies, accept or
  postpone an assignment, return to the main topic or leave. Personal attitudes
  are saved separately from shared quest decisions. The runner's assignment
  panel separates Available, Active / Ready and Completed work.
- **Early skills:** ordinary skills can be learned/equipped in Oakvale or Dunmere
  after closing conversations. Ascension alone requires reporting Dunmere's
  conclusion **and 15 currently unspent personal Magic Runes**. Already Ascended
  older characters keep their progress.
- **Travel:** use the compact **Crystal 20/20** button, Menu → Travel map, or a
  village/attuned shrine. Select a known point on the map or use Previous/Next,
  inspect availability and method, then confirm. Wheel/buttons zoom; scroll/swipe
  pans. Standing at an activated shrine enables free shrine travel. Elsewhere,
  each connected human needs a full personal crystal. Discovered inactive shrines
  explain their locks; future-region scenery is not a destination.
- **Crystal:** every Adventure character starts with 20/20 souls, separate from
  inventory and skills. A successful crystal trip spends all 20 from each
  participating human. Ordinary/elite/boss kills grant 1/3/5 souls, once per enemy
  life, capped at 20. Living connected humans within 450 world pixels share credit;
  recently participating downed heroes qualify for 30 seconds. Support heroes and
  companion kills count; offline players do not. Gathering/confirmation precedes
  a three-second channel. Movement, damage or nearby enemies interrupt it.
  Cancelled/rejected/failed-save trips spend nothing; travel never heals or resets
  cooldowns, and cannot escape sealed encounters or the unfinished opening.
- **Outdoor respawns:** a completely defeated ordinary group becomes eligible
  after 600 seconds. The two-second check only restores groups in unoccupied
  areas; partial fights never reset. Epoch times and generations survive restart.
  Old cleared groups get a future timer when revisited, not an instant respawn.
  Quest guards, bosses, opening fights and cleared dungeon waves remain cleared.
  Repeat kills grant one shared Rune each, capped at six per group/cycle, and can
  recharge crystals. They never repeat unique treasure, Magic Runes or milestones.
- **Cottage:** speak to **Mara** inside a village cottage. Treatment costs **5
  shared ordinary Runes** for that living character's HP and mana. Both already
  full costs nothing. It does not change cooldowns, crystal charge or the inn bed.
  Repeated requests and failed saves cannot double-charge the party.
- **Rewards:** confirmed acquisitions queue concise icon/name/rarity/delivery
  notices. Pending choices and full-pouch conversions are labeled accurately.
  Personal Magic Runes show the updated personal balance and a restrained effect
  with the existing fanfare, respecting mute/reduced effects.
- **Dying land:** the upper east trail from Dunmere's fields reaches the authored
  Eastern threshold, with dry ground, sparse vegetation, abandoned farm scenery
  and a journal clue. The lower east hatch still leads to the cellar. Ashen Ridge
  remains an explicit future lead, not a playable new biome.

Versioned additive records retain conversation choices, crystal receipts,
respawn generations and cottage transactions through normal saves and portable
export/import. Awareness/search cues stay transient. Automatic Adventure saves
and bed recovery retain their existing limits; Render's free filesystem is still
temporary, and real cloud storage remains unconfigured.

Validation: **364 Python tests passed, 0 failures/errors/skips; 26 client suites
and 29 JavaScript syntax checks passed.** Actual ordinary-stat browser review
covered fresh Rogue learning/combat/travel, NPC choices, runner tabs, free shrine
travel with an empty crystal, cottage treatment and walking Dunmere → fields →
Eastern threshold at desktop and 844×390 landscape. Late story access used an
explicit helper-completed fixture; it was not an earned campaign playthrough.
See [the systems validation report](reports/ADVENTURE_SYSTEMS_VALIDATION_2026-10-16.md)
for screenshots, measurements and remaining human/device/listening checks.

**Activated locally:** http://127.0.0.1:8000/ — refresh existing tabs. Server
`d5b02b1d62ad`, client `c08b45d73dbd`, protocol2. Eight save files were hash-verified
in a backup before startup. [Activation record](reports/SYSTEMS_ACTIVATION_2026-10-16.json).

## October 16: audio, music and feedback

The Bxfr bank now contains 198 reproducible Bfxr effects, quieter material hits,
actual projectile launch/collision families, accepted interaction/rune/Ascension
outcomes and bounded crowd mixing. Ten original synthesized musical arrangements
cover menu, Oakvale, Dunmere, exploration, dungeon, combat, boss, victory and the
Last Caravan. Music crossfades; menus keep the world running.

Menu → Controls & settings → Sound settings offers master, music, effects,
ambience and UI volumes, cue previews, master mute and reduced shake/decoration.
Old audio preferences migrate. Browser gestures activate sound; missing assets
never block play. Refresh the game page after updating.

Open [the local audio review](art/audio/review.html) for playable tracks and mixed
references. [Build/source workflow](art/audio/WORKFLOW.md),
[routing audit](art/audio/OVERHAUL_2026-10-16.md) and
[validation report](reports/AUDIO_OVERHAUL_VALIDATION_2026-10-16.md) document exact
coverage and limits. Actual human listening and physical-device testing remain
open; metrics and browser playback do not prove comfort. This is a small original
synthesized score and stylized ambience, not realistic recordings or a complete
soundtrack. Existing Bfxr vendor licenses are preserved.

A browser client with a Python authoritative game server. Choose the existing **Gauntlet** stage campaign or the **Adventure** woodland prototype. Both support room codes, parties of up to four, unique classes, mana, chat, combat, shops, equipment and inn beds. Gauntlet keeps its three-from-six pre-run loadout; Adventure starts with a basic attack and an active skill, with hero progression unlocked during play. Equipped weapons and armor affect combat and appear on player sprites.

## October 16: completion and performance audit

The recent Adventure expansion remains playable locally. The detailed
[completion checklist](reports/COMPLETION_AUDIT_2026-10-16.md) separates verified
behavior, helper fixtures and outstanding human/device checks. It includes
screenshots, exact test results, size inventories and reproducible measurements.

The menu now demand-loads hero/enemy/region/attack artwork. Observed initial static
loading fell from169 requests /28.95MB to47 /3.31MB in the controlled October15
sample. A later combined art/audio build measured51 /3.43MB. Repeated state responses reuse
only matching immutable catalogs and revisioned skill UI, reducing the sampled
responses by57–67%; movement, enemies, cooldowns and interactions stay live.
Authoring assets, saves, backups, rebuild scripts and licenses were preserved.
Playable packaging excludes development reports/previews and private config/logs.
These are download/serialization improvements, not a certified FPS gain.

The latest local build and save-backup count are recorded in the systems section
above. Saved worlds and Gauntlet checkpoints remain compatible.
Settings → Technical details shows the served build plus
bounded local timing/resource readings; no save contents or player names collected.

Validation:334 Python tests passed,0 failures/errors/skips;21 client suites and27
JavaScript parse checks passed. Actual fresh ordinary-stat browser review covered
Oakvale, road combat/retreat, camera, atlas, Rootwater entry/interior map and retreat
at desktop1366×768 and landscape844×390. Recovered an interrupted browser check;
wheel zoom125→188% worked, travel retained89/150HP, and the narrow dungeon chart
now sits beside its notes. A full cave/boss clear is not claimed. Earlier
opening/Brook/late-fixture evidence is labeled in the report.
Full earned chapter pacing, physical phone controls, human multiplayer and audio
comfort remain unverified. Save writes still cost roughly31–39ms in local samples;
durability protections were retained. Nothing was published or deployed.

## October 15: The Last Caravan, Dunmere and Ascension

This local build adds a playable opening, a longer sequential woodland chapter,
three travel shrines and Dunmere's first complete local quest chain. Existing
Adventure progress, Rootwater, Briarwatch, the repaired bridge, Gauntlet and its
checkpoints are retained. The details here supersede older starting-location and
flexible-main-quest descriptions below. Nothing has been published or deployed.

Open **http://127.0.0.1:8000/** with `python server.py` running from this project.
Refresh an existing browser tab for the updated client. Choose **New Adventure**
for a separate character/world and **The Last Caravan** opening; repeat players
can select **Skip introduction** in setup. **Continue** preserves an existing
world and never forces old/imported characters through the new introduction.

The opening is a controllable road defense: hold attack, use your starter active,
then gather at the marked safe muster when withdrawal opens. Friendly guards
provide bounded support; the dragon/watch event stays in the background. Failed
opening attempts retry locally without the ordinary wipe penalty. Restart resumes
the next unfinished opening encounter; durable facts prevent repeated starter
points/rewards. An ordinary Healer+Cleric browser run took approximately 96 seconds.

After arrival, speak to the **Village Runner** to accept the missing-hunter
assignment. The journal shows offered, accepted, ready-to-report and completed
steps. Return to the runner for each substantial report and next assignment:
hunter → bridge → water evidence → shrine → burned watch/network → Minotaur ruins
→ border road. Evidence found early is remembered, but unaccepted objectives do
not silently finish themselves. The border assignment starts in Oakvale and is
reported in Dunmere. Optional Rootwater/Briarwatch exploration remains available.

The woodland now includes the Clouded brook, old mill trail, logging yard and
stranded camp, Deepwood hollow, burned watch, old network approach and border road.
Paths form loops and preserve the existing river/bridge restrictions. Larger areas
keep the following camera and room overview control. Named packs remain territorial;
ordinary groups now use the controlled respawn rules above. Danger depends on location, not boundary crossings or
village visits. Map fog, known objectives, discovered shrines and dungeon interior
maps remain separate; scroll/swipe to pan a zoomed atlas, or use Fit and +/−.

**Brook, Deepwood and Watch travel shrines** each require clearing their named
guards and deliberate attunement; Watch also requires reading its register.
Attunement permanently unlocks the world destination and grants each character
one personal Magic Rune once. Late players can claim their own attunement.
Use an active shrine or village portal for free destinations; the personal crystal
allows charged travel from an eligible trail. The existing 3-second channel requires gathered
connected humans and cancels on movement, damage or nearby danger. Companions and
offline players do not block it. Sealed fights and the unfinished introduction
block travel. Travel does not heal, reset recharge or move the recovery bed.

**Dunmere is playable:** village services, central portal and upstairs inn beds;
three failed-field clues; two irrigation channels and a sluice; ruined-mill approach;
and an underground cellar with the Blighted Overseer and additive ledger. The
accepted cellar encounter clearly seals its exits. Defeat unlocks a permanent
hatch back to the fields. Report findings to the Dunmere runner for the local
outcome and next lead. A restored green strip, changed dialogue and routes remain
saved. The pumping works and Ashen Ridge are future leads, not additional playable
regions in this version. Ordinary approach retreat remains available.

Objects and signs now have concise inspection panels without human portraits or
invented player replies. Approaching a sign only shows its E/touch prompt; reading
and discovery require deliberate interaction. NPC conversations retain portraits.
Whole overlapping decorative objects fade smoothly instead of cutting a rectangle
around the hero. Actors, attacks, warnings and interaction markers remain clear.
Gauntlet arenas have sparse perimeter decoration and especially clear boss space;
server-owned cover, collision and projectile blocking are unchanged.

### Personal Magic Runes and Ascension

**Magic Runes belong to each Adventure character. Shared shop Runes are unchanged.**
Open **Skills → Personal Magic Runes** to inspect receipts and purchase previews;
make permanent purchases safely in either village after closing conversations.
The finite source ledger is in `MAGIC_RUNE_LEDGER.md`, recorded before rewards
were implemented:

| Source group | Guaranteed Magic Runes per character |
| --- | ---: |
| Three travel shrine attunements | 3 |
| Hunter, bridge and shrine reports | 3 |
| Woodland finale report | 2 |
| Dunmere field, irrigation, cellar and conclusion reports | 7 |
| Total guaranteed | **15** |
| Optional concealed spring casket in Deepwood | **+1** |

Health or mana costs 1 rune per rank and adds 5% of the class's unmodified base maximum,
up to 5 ranks each, with upward integer rounding. Bonuses add rather than compound;
the preview shows exact totals. Purchases preserve resource proportions, downing
and recharge. **Ascension requires reporting Dunmere's conclusion and consumes
15 currently unspent Magic Runes.** Only 16 exist
in this playable chapter including the optional cache: buying more than one stat
rank prevents Ascension here. The confirmation explains this permanent tradeoff;
ordinary skill respec does not refund Magic Runes.

Ascension grants 10% of base maximum HP/mana, 8% damage, a visible restrained gold
identifier, a functional class signature and two automatic passives. The signature
is unlocked separately from equipment: equip it in an available active slot in
Skills. Existing Hold / Q / R / F / X controls and gradual slot unlocks remain.
All signatures have mana costs, normal cooldowns and a readable 0.6-second commitment.

| Hero | Signature | Passive identities |
| --- | --- | --- |
| Knight | Citadel Oath: committed strike, party barrier/protection | Barrier defense; damage against controlled foes |
| Wizard | Astral Convergence: targeted cluster damage/root | Control combinations; limited mana return on casts |
| Archer | Horizon Arrow: narrow piercing line blocked by walls | Long-distance damage; dash barrier |
| Cleric | Dawn Mixture: sacred splash, healing, cleansing/barrier | Weaken enemies; protect allies with healing consumables |
| Rogue | Shadow Circuit: collision-safe lunge/strike/concealment | Dash concealment; mana from bleeding kills |
| Druid | Elder Accord: roots and summon healing/empowerment | More durable summons; limited healing from summon hits |
| Bard | Harmonic March: interrupt and party movement/protection | Barriers from casts; limited mana from direct hits |
| Healer | Second Dawn: rescue or emergency heal with barrier | Low-health protection; safer rescues |

Guild class changes keep the purchased Ascended state and select the new class's
kit. Old-class signatures/passives do not carry over; existing ability/slot
cooldowns and summon 8/15-second death recharge remain protected. Gauntlet retains
its classic progression.

### Saving and verification for this expansion

Adventure still saves progression automatically after storage confirms success;
inn beds in either village select the recovery point. Restart/wipe returns to the
saved bed or home gate, preserving completed objectives, defeated groups, shrine
activation, claims, chapter reports and purchased progression. An unfinished
sealed encounter restarts coherently; partial boss damage is not a saved shortcut.
The ordinary 40% shared-Rune wipe penalty applies once; opening retries are exempt.
Portable save v2 uses additive versioned records and validates imports before
restoring copies. Old completed woodland worlds retain their result and receive
the border assignment without replay. Eligible new personal receipts reconcile
once; previously awarded equipment/shop payouts are not reclaimed or duplicated.
Keep browser recovery data and use **Menu → Save files → Export backup**.

Existing local/cloud configuration is unchanged. No real hosted cloud recovery
was activated or certified in this pass. Render free disk remains temporary;
export a backup before relying on it. Private saves were not used for tests.

Final checks: **330 Python passed, 0 failures/errors/skips; 19 client suites passed,
0 failures; 23 JavaScript syntax checks passed.** Browser reviews covered ordinary
opening/Brook combat, earned rune purchase, distinct mode switching, object panels,
atlas, desktop 1366×768 and landscape 844×390. Dunmere/Ascension/restart UI checks used
a labeled helper-completed world; the full accept/interact/report chain and all 8
Ascended kits have automated coverage. Twelve starter opening probes and 9 ordinary
shop-kit encounter probes are functional evidence, not final human balance tests.
Human multiplayer, physical-phone controls, full chapter balance and perceptual
audio listening remain outstanding. See
`reports/WOODLAND_EXPANSION_VALIDATION_2026-10-15.md` for screenshots, raw results,
backup/activation details and reproducible commands.

## October 14 controls, new games and Adventure skills

The main menu separates **New Adventure**, **New Gauntlet run**, **Continue**,
**Join a party** and **Settings**. New Adventure creates a distinct world and
character; it does not replace an existing Adventure. Remembered-world cards show
hero, location and last confirmed save. **Menu → Main menu** leaves the session;
**Change mode / new run** leaves it and opens setup for another run. Continue keeps
the original world. Gauntlet sessions still require an upstairs inn bed checkpoint
for recovery after a server restart. Shared run settings remain host-controlled.

New/join responses retain the private recovery proof. Private creation receipts
make ambiguous creation retries safe; if a restart makes an unconfirmed request
unrecoverable, review Continue before making another request. A room code alone
does not recover somebody else's character. A new Adventure party member can join
in Oakvale with an unused hero; an existing member uses Continue. Closing setup
while a response is pending preserves the returned identity without switching the
current session. Keep browser site data or export a portable Adventure backup.

Movement now sends a changed direction or release immediately, cancels superseded
input requests, and rejects late input from old scenes/sessions. The server still
owns collision, roots, dialogue locks, downing, dash and encounter boundaries.
Input retries use a short timeout and a server deadman stop. Simulation scheduling
targets a 50ms interval instead of adding work time to each interval. Duplicate
interaction saves were removed; atomic disk writes and save protections remain.
Nearby interaction prompts come from server eligibility, show the exact action
and rejection reason, and prioritize rescuing a downed ally over a nearby trail.
Opening menus releases held movement, attack and revive input.

Rootwater's mouth is on the **Southern road's lower east edge**, about 78% down
the area. Follow the cave sign and approach the mouth for **Enter Rootwater
passage**. The atlas identifies this entrance. No hunter, bridge or shrine quest
is required to enter; the cave boss still seals its encounter. Gather connected
human players at the entrance; offline players and companions do not block travel.

Adventure's top tools are **Map / Journal / Skills**. Save management, settings,
party code and leaving are under **Menu**. Combat abilities sit beside health and
mana; long menus scroll within the viewport. Mobile gameplay still requires
landscape, and its movement pad remains available. Successful save notices expire;
failures remain visible. Menus do not pause a connected party's combat.

All eight heroes have three branches and **15 functional nodes each**: their six
existing abilities, three new actives, three two-rank ability modifiers and three
passives. Knight emphasizes defense/weapon mastery/leadership; Healer emphasizes
direct healing/prevention/rescue. Cleric uses sacred projectiles, protection and
mixtures. The other five have class-specific control, movement, summons and
support options. Nodes show actual effects, next rank, prerequisite, point cost
and equipped status. Existing icons and animation/audio systems are reused.

| Adventure action | Default control | Availability |
| --- | --- | --- |
| Basic attack | Hold left mouse / attack button | Starter |
| Active 1 | Q / tap icon | Starter |
| Active 2 | R / tap icon | Explore Southern road |
| Active 3 | F / tap icon | Complete one woodland quest |
| Ultimate | X / tap icon | Unlock and equip an Ultimate |
| Dash / interact or held rescue | Space / E, or touch controls | Existing rules |

Learn and equip in **either village**, after closing conversations. Inspect Skills
anywhere. The chapter awards a finite **20 points** per character: arrival 2,
road 1, inn 1, hunter/bridge/shrine 2 each, surveyor alcove 1, cave 2, tower floors
1 and 2 one each, tower completion 2, woodland finale 3. Each milestone pays once;
there is no XP farming. New characters receive the same two starter arrival points;
finishing or skipping the caravan does not pay them again.
Unlocking and equipping are separate. Respec is free at home, refunds learned
nodes and retains milestones, earlier training benefits, HP, mana and recharge.
Ability and action-slot recharge carry across swaps, travel, saves and recovery.
Live summons are dismissed with their existing after-death recharge when changing
loadout. First Ultimate equipment begins with the existing 15-second charge rule.
Companions use the same finite progression budget and choose skills at home.

Older Adventure equipped abilities remain available without paying again;
Vitality/Power/Focus benefits and unused earlier training credit are preserved,
with the old inn award reconciled once against the new milestone. Guild class
changes rebuild that hero's tree without duplicating milestone points and retain
slot recharge. Portable version-2 saves add validated hero-progress version 1 and
five-slot loadouts; older saves remain supported. Gauntlet's Q/X controls and
pre-run choices are unchanged.

Validation on October 13–14: **300 Python tests passed, 0 failures/errors/skips**;
**19 client suites passed**, 0 failures, and **21 static JavaScript files parsed**.
All storage and browser fixtures were disposable. Ordinary-stat Knight and Healer
browser checks covered separate worlds/Continue, Gauntlet mode selection, skills,
Southern road, the Rootwater entrance pack, retreat, reload and server-restart
recovery. Desktop 1366×768 and landscape 844×390 were reviewed, including a
helper-completed fixture for the maximum five-action HUD. Mean simulation interval
changed from 57.3ms to 50ms; a local ordinary-combat sample had 19ms p95 input
acknowledgement. Background browser scheduling and different workloads prevent an
FPS before/after claim. Human multiplayer, physical-phone feel and full balance
playthroughs for all eight trees remain outstanding. Details, raw measurements,
build fingerprints and screenshots: `reports/ADVENTURE_CONTROL_VALIDATION_2026-10-14.md`.

**Menu → Technical details** provides bounded anonymous client/server timings.
The main menu shows discreet Python/client build identifiers and the host address.
This update is local only; it has not been published to GitHub or deployed to
Render. Existing local/cloud storage configuration and limitations are unchanged.

Dungeon artwork (2026-10-13): Rootwater and Briarwatch now have illustrated,
discovery-gated maps, dedicated floor art, stone walls, entrances, stairs, bells,
seals, survey markers and supply/cache sprites. Village portal usage displays
charging, departure, arrival and interruption effects, with a reduced-motion
variant. Refresh the browser to load the art. Exact prompts, selected sources,
export metadata and the rebuild process are retained in
`art/dungeon-portal/WORKFLOW.md`.

Asset cleanup (2026-10-13): village art loads on first use rather than downloading
every region and interior at startup. Obsolete sprite exports and authoring
catalogs are preserved in `art/unused-runtime-sprites/`, outside the served
assets and runtime packages; its manifest records their original paths and
checksums. Full source/art packages retain them. Active terrain fallbacks and
saved games remain. Refresh the browser after updating client files.

## October 13 visibility, movement and dungeon maps

Foreground trees, roofs, portal shrines and large characters now become translucent
only where they cover a hero. The local hero remains opaque; names, rescue markers
and combat warnings stay above scenery. Artwork and collision footprints are retained.

Continuous walking now uses corrections capped at eight percent of normal movement speed,
avoiding polling corrections that momentarily cancel or reverse a walking frame.
Short polling gaps keep predicting movement within a 200–350ms horizon; a longer
lost connection stops prediction. Roots, downing, doors, obstacles and teleport
corrections remain authoritative. These October 14 values supersede the earlier
one-quarter correction cap and longer prediction window.

In **Map → Dungeon maps**, wheel up/down over a diagram zooms around the pointer.
Use **+/−/Fit** on touch, then swipe to pan. Scroll outside a diagram (or down at
Fit) to reach the other dungeon card. Zoom/pan persist through ordinary panel updates,
and fit sizing ignores scrollbar changes to prevent shaking. Refresh the browser
to use these client changes; a server restart is unnecessary.

Validation: **282 Python tests passed**, 0 failures/errors/skips, and **19 client
suites passed**, plus static JavaScript syntax checks. The sandbox-only Python run
had one socket-permission error; the full rerun with localhost access passed.
Disposable browser worlds verified portal overlap, held/released village movement,
desktop wheel zoom, Fit and scrolling to both maps at 844×390 landscape. The dungeon
map fixture was pre-completed by helpers; this was interface review, not dungeon
balance playtesting. Human multiplayer movement feel and physical-phone checks remain.

## October 13 recovery and village update

Villages now shuffle buildings, services and paths around a clear central portal
shrine. In Adventure, **Crystal / Travel map** selects discovered villages and
activated shrines. Connected players gather, confirm and stand still for three
seconds. Movement, damage or nearby enemies interrupt it; sealed encounters cannot
be escaped. Free travel requires gathering at a shrine; trail travel costs each
human a full crystal. HP, recharge, encounter and quest progress carry across the
trip. Companions/offline players do not block it. Oakvale and Dunmere are playable
villages; Gauntlet keeps ordinary travel.

**Menu → Save files** gives each character three recovery entries:

1. Current Adventure: the latest confirmed automatic save.
2. Adventure Backup: the previous confirmed local save, rotated automatically.
3. Gauntlet Checkpoint: the latest wave-mode inn bed checkpoint remembered here.

Adventure snapshots include the party to keep its world consistent. Their files
are in `data/adventures/` and `data/adventure-backups/`; wave checkpoints stay in
`data/checkpoints/`. Backup recovery shows a preview and creates a **separate
world**; original saves and previously remembered worlds are kept. Keep browser
site data/private recovery identity, and export a portable backup for transfers.
Successful save notices disappear after a few seconds. Failed saves stay visible
and never advance the confirmed time. Existing saves and inn beds remain compatible.
Rolling backups are local files, not a newly activated cloud backup service.
Render's free filesystem remains temporary.

Movement correction and ice friction are smoother, and roots/interaction locks
stop client prediction. Monster attacks now select the matching imported wind-up,
movement and release strips; elemental enemy projectiles retain their correct
effects even when their attack kit shares a hero label. Existing artwork is reused.

### Isolated regression tests

From the project folder, run:

```text
python -B tools/run_tests.py
python -B tools/run_tests.py --temp-root "path-to-a-writable-test-folder" --report reports/test-results.json
```

The default root is `.test-tmp/`. On a restricted/synced Windows folder, choose a
writable folder outside OneDrive. The runner redirects only its process's
TEMP/TMP/TMPDIR and test storage, restores settings and removes disposable fixture
directories afterwards. Never point tests at private `data/`. It checks locked
atomic replacement and reports socket restrictions; restricted socket tests are
not counted as passing. Use `--pattern test_town_layout.py` for focused layouts.
Python needs no additional packages. Run each `tests/test_*.cjs` with Node; the two
canvas image suites require `@napi-rs/canvas` on Node's module search path.

October 13 final checks: **282 Python passed, 0 failed, 0 errors, 0 skipped**;
**17 client suites passed**, with all client syntax checks passing. The historical
27-error cleanup run was not reproduced across 10,000 deterministic old-generator
seeds. A road-width mismatch was fixed, full accessibility validation was added,
and an authored fallback uses the same checks. The cleanup/lazy loading remain.
An earlier OneDrive temporary-folder run had intermittent Windows replacement
errors; final isolated writable-folder/socket runs were clean. Actual browser
review covered desktop and narrow landscape, portal travel and separate-copy
backup recovery. Human multiplayer and physical-device movement feel remain to
be tested. Details: `reports/VALIDATION_2026-10-13.md`.

## Run locally

After the October 8 storage cleanup, original visual art, import ZIPs and older
releases are stored in the sibling
`../The-Gauntlet-Complete-Backup-2026-10-08.zip`. Visual source/workflow paths under
`art/` referenced below are inside its `The-Gauntlet/art/` folder; extract those
folders when editing the original artwork. Runtime sprites and sounds remain
in `static/`, and `art/audio/` remains available for audio rebuilding. The game
runs without extracting the backup. OneDrive cloud sync of the backup has not
been verified. New October 9–10 authoring sources are available locally in
`art/ability-icons/`, `art/ability-animations/`, `art/projectile-animations/` and
`art/adventure-sprites/`, `art/pixel-ui/` and `art/village-redesign/`; their
`WORKFLOW.md` files retain prompts and rebuilds. The village redesign sources
were created October 11.

Requires Python 3.10 or newer. No third-party Python packages are required.

Run: python server.py

Open http://127.0.0.1:8000 on the host computer. Do not open `static/index.html` directly; a `file://` page cannot reach the Python API. For another device on the same Wi-Fi, open http://<host-computer-LAN-IP>:8000 and enter the room code.

## Woodland chapter quality pass — October 12

Adventure is still the existing woodland chapter, with its three quests, both
dungeons, restored routes, shops and optional discoveries. **Menu → Save files**
opens recovery details and **Export backup**. A temporary save notice also opens
these details. The main
menu's **Continue saved run** opens a list of this browser's Adventure identities
and its Gauntlet resume identity. It shows the Adventure name, character/gear and
training progress, completed objectives, visited locations, shared Runes, last
confirmed save time, recovery location and storage status. A failed write shows
**Save failed**; it never advances the confirmed time/revision. Leaving a session
does not delete Adventure characters or transfer world ownership to its new host.
An OS-released record lock and revision comparison also prevent a second local
server from silently overwriting newer progress; export/import a separate copy
when a conflict is shown.

**Import Adventure backup** accepts a portable v2 JSON or an older internal v1
Adventure record. It validates size, types, known locations/dungeons, abilities,
equipment and claims, then shows a summary and character selector. Confirmation
creates a **separate world** and fresh private recovery identities. Original
worlds/files remain intact; confirmation retries do not create another copy.
Existing item effects are reconstructed from their known definitions. Unsupported
records are rejected and preserved. Portable exports contain progression for the
whole party but exclude session/recovery proofs, account IDs, secrets, chat and
private telemetry. Treat an export as a copy of your party's game progress.
The creator can share a **private character recovery link** for other imported
hunters from Continue; a public room code cannot claim their existing equipment.

New local saves use persistent world UUIDs in `data/adventures/`; older room-code
files remain readable and are updated at their original path. Temporary room
codes and session hosts do not define world ownership. Existing browser recovery
and Gauntlet checkpoints remain compatible. New sessions require a private proof
for state/actions as well as a player ID; old browser sessions retain their
existing recovery behavior. Keep browser site data or an export. Recovered worlds
return to the inn bed/home gate, with interrupted sealed encounters restarted in
full and completed waves/quests/claims preserved. Export captures current live
progress even if disk saving has failed. Inn beds choose recovery, not a separate
manual Adventure save slot; the current and rolling backup entries above are
automatic. Render free disks are still temporary.

### Personal rewards

New completions offer two personal choices in **Journal**, with equipped-slot
comparisons and an already-owned indicator. Choices stay pending across travel,
disconnects, wipes, exports and restart. When the pouch is full, choose a pouch
item to sell and replace, or sell the reward for shared Runes. The receipt names
the hunter, selected item and any sale. Retrying a resolved choice cannot pay
again. Previously awarded rewards are neither reclaimed nor replaced.

| Activity | New personal choice | Shared completion Runes |
|---|---|---:|
| Surveyor alcove | Warding Tonic / Mana Draught | 16 |
| Rootwater guardian | Phoenix Flask / Stormguard Charm | 40 |
| Shrine | Rescuer's Cuirass / Stormguard Charm | 35 |
| Briarwatch summit | Your class weapon / suitable build item | 40 |
| Woodland finale | Aegis of Dawn / Starfall Blade | 70 |

The finale's existing legendary tools improve armor or attack damage for every
hero. Entrance supplies and early-floor tonics remain automatic one-time gifts.
Rootwater now has fixed survey markings, dry-shelf hints, root stains and concise
room notes. Its packs, corridors, optional branch, boss seal and far route remain.
Briarwatch floor one pairs frontline pressure with ranged guards; floor two uses
trap lanes and chargers; the summit caps guards at two, with an opening before
they attack. Opening windups are staggered. Existing HP, damage, ability rules,
three-second wave breaks and persistent kill IDs are unchanged. Village completion
dialogue points to unfinished Journal activities, Ashen ridge and backup/continue
actions. Ashen ridge is a story lead, not a playable new biome.

### Optional Supabase storage: prepared, not activated here

Local disk saving needs no external configuration or Python dependency. Optional
cloud code is in `cloud_storage.py`, using `RunStorage` as the local-first
abstraction. Configure an owned Supabase project, apply
`migrations/001_adventure_cloud.sql`, enable email/password Auth and provision
accounts there, then set the three server environment variables in `.env.example`.
Python does **not** automatically read `.env`. Never put the service-role key in
client code, exports or source control. Only the URL and public anon key are sent
to the browser. [Supabase function privileges](https://supabase.com/docs/guides/database/functions)
explain the service-role-only RPC permissions in the migration.

Continue → **Account and cloud recovery** supports sign-in with an existing
Supabase Auth account. The creator links first; guests link only their current
character using a private existing-session proof. Legacy sessions without that
proof can export/import a separate world first. The creator owns the world;
changing session host never transfers it. Accounts recover their world-bound
character, not equipment into another world. Python verifies the access token
with Auth; RPC transactions verify membership, immutable identity, revisions and
idempotent request receipts. Client-supplied account IDs are never trusted.

Cloud replication runs outside the simulation lock, keeps an exact retry journal
through lost acknowledgements/restart and stops on a revision conflict instead of
overwriting remote progress. Local saves continue independently. Cloud status is
confirmed only after the provider acknowledges a transaction. Account tokens stay
in page memory; sign in again when expired. Active-world reconnect joins the party
without replacing live progress. On a conflict, export local progress and recover
the remote snapshot as a separate copy through the storage API. No automatic merge
is implemented. **No Supabase URL/keys/migration or real cloud recovery were
configured/verified in this workspace.** Contract tests use an explicitly mocked
provider; SQL still needs execution and live ownership/recovery verification in
the configured project. No private saves were uploaded and no service purchased.

### Repeatable ordinary-stat review

`python -B tools/chapter_probe.py --matrix` runs disposable, deterministic
encounters with normal class HP, class weapon + Oakguard, one heal/mana/ward,
zero training ranks, normal resources and the real opening/carrying cooldowns.
It records location duration, lineup/companion/difficulty, actual damage,
downings/wipes/revives, consumables, resources and remaining enemies. It has a
small navigation bot and isolated starting encounters, not human cooperation or
a whole geared campaign. `tools/adventure_preview.py --scene cave --ordinary-kit
--observations reports/my-cave-review.json` provides the same ordinary town kit
for browser review; add `--touch-controls` for landscape layout checks.
`--fast-combat` remains explicitly an accelerated functional fixture.
Observations omit names, accounts, world/session identities and chat. They are
opt-in on disposable test rooms, not tracking on real Adventures.

Effects retain stable scenery and reduced-motion support. Repeated Light cues
are quieter; low-priority voices yield around boss warnings and completed revives.
No audio assets were regenerated. **Perceptual listening remains outstanding**:
the available tools could inspect playback but could not listen. Use Sound settings
cue previews, `art/audio/preview.html`, and `tools/audio_preview.py --players 4`.
Listen to 60 seconds of held attacks, a crowded four-player wave, captain warning
under summon attacks, completed revive, headphones and phone speakers. Check
fatigue, warning recognition and comfortable effects/ambience volume; successful
playback and waveform measurements do not certify comfort.

Validation details and remaining human/physical-device/cloud checks are in
`reports/CHAPTER_QUALITY_VALIDATION_2026-10-12.md`. Ordinary browser review found and
fixed missing village reconstruction after import; the new regression requests
the recovered world's real public state before committing it. Human multiplayer
balance, physical-phone testing and live Supabase recovery remain outstanding.

## Regional village artwork — October 11

Woodland, ruins, cavern and frost villages now match the richer world design.
Their six building types, interiors and upstairs inn materials use replacement
pixel art, with six roof color variations. Trees and regional formations share
the world's scenery; gardens, wells, lamps and understory enrich courtyards.
Paths have rounded corners and restrained edges on the new ground textures.
Scenery, buildings, villagers and heroes draw in depth order, so canopies can
overlap characters. This is visual cover only. All seven village layouts,
services, doors, guest occupancy, bed checkpoints and Adventure saves retain
their existing behavior.

Refresh the browser to load the artwork. Sources/prompts and the repeatable
export process are in `art/village-redesign/WORKFLOW.md`; `preview.html` shows
regional/layout/interior authoring views.

## Adventure dungeons — local update, October 12

Choose **Adventure · woodland prototype** in the lobby and begin normally.
Two finite, authored dungeons now extend the existing woodland. They are
optional routes; the hunter, repair kit, shrine and old-ruins objectives retain
their own requirements. There is no new biome or repeatable reward farming.

| Dungeon | Entrance and unlocked destination | What happens |
| --- | --- | --- |
| **Rootwater passage**, underground, danger 4 (den 5) | Southern road's lower east trail → Hunter's clearing's lower west trail | Four connected cavern chambers: entrance supplies, two gallery packs, a northern Surveyor cache and a Cave Troll den. Ordinary chambers allow travel with enemies alive. Gather at the den seal and press E to awaken the boss; exits seal until it falls. |
| **Briarwatch tower**, tower, floor dangers 4 / 5 / 6 | Camp's east trail → Bridge's east bank | Three floors, five waves: two on each early floor, then a Minotaur Captain with guards. Floor 2 has warning traps and alternate lanes. Gather at each floor bell and press E. Waves seal the stairs, with a three-second break between waves. After clearing a floor, choose when to use its stairs. |

The ordinary cave route permits retreat to the road. Tower floors are safe to
leave before ringing the bell and after the entire floor is cleared; descend
through the cleared floors to camp. A three-second wave break is still part of
the sealed encounter. Active boss fights also seal exits. A party wipe returns
to the existing inn/home recovery point. Offline humans and companions never
block gathering, starting an encounter or travel. The companion still occupies
one of the existing four party slots. Simulation pauses without connected humans.

Entrance prompts identify type, danger, completion and retreat rules. **Map**
automatically opens a separate discovered chamber/floor diagram inside a dungeon;
use **Woodland atlas / Dungeon maps** to switch views. Unknown chambers and far
connections remain hidden until charted. **Journal → Track dungeon** selects a
personal goal and highlights its next usable exit. Floor/wave status stays in
the exploration HUD. Completed entrances gain a steady green pennant and check;
new passages appear on the atlas. The map's scrollbar sizing is now stable.

Both cave crates give shared Runes and a personal consumable. Early tower floors
give Runes and a Warding Tonic; dungeon completion gives 40 shared Runes and each
hero's existing class weapon. Named journal receipts show recipients and convert
full-pouch items to shared sale-value Runes. Each enemy's Rune payout, treasure,
floor and completion reward is recorded once. Reopened routes do not repair the
bridge, recover the hunter or restore the shrine. The tower descent lands on the
east bank; an unrepaired river crossing remains blocked. After the woodland's
Minotaur King is defeated, the journal and village conversation give an **Ashen
ridge** lead. That next region is not playable yet.

Dungeon stone walls/pillars, the camp tent's solid sides and ruins columns have
matching server collision, browser prediction and artwork. Tent/arch openings
stay usable. Walls block movement, dash, attacks, shots and splash
through walls. Actors stay visible above the wall art; dungeon rooms omit tall
cosmetic foreground dressing. Cave and tower floors reuse the existing cavern
and ruins materials, with authored paths and restrained, steady scenery.
Outdoor large-area cameras and mobile landscape gameplay are retained.
Travel keeps health, mana, ability and dash recharge. Summons are dismissed on
area/floor changes with their ordinary death recharge; re-entry grants no free
heal, cooldown reset or boss damage reset.

### Dungeon saving and interrupted attempts

Adventure's existing **v1** save format has an additive **v1 dungeon** section.
Existing Adventure records without it and Gauntlet checkpoints remain supported.
Unsupported records are left intact and reported in the server log.

Automatically saved permanent progress includes discovered entrances/chambers,
defeated ordinary enemies, completed waves/floors, claimed treasures/rewards,
boss completion and unlocked routes, alongside existing player/world progression.
Inn beds continue to choose recovery; they are not required to save those facts.
Completed floors/chambers stay cleared. An interrupted **active wave or unfinished
boss** restarts as a full encounter with its authored arena and stable enemy IDs;
partial bodies are discarded rather than merged with a fresh spawn. Completed
waves stay completed, and repeated kills do not pay Runes again. Recovery returns
to the inn/home, carrying remaining recharge conservatively; a live summon resumes
its normal death recharge. The existing 40% wipe loss applies once. Disconnects
do not count as deaths or clear an encounter. Free Render filesystem storage is
still temporary; no durable hosted saving is claimed.

Validation: **245 Python tests**, **15 client suites** and static JavaScript syntax
checks passed. Disposable rooms covered solo/full-party scaling, companions,
gathering, reconnect/host changes, paused simulation, walls/attacks, cooldowns,
revisits, one-time payouts, interrupted encounters, restart/wipe recovery and old
Adventure/Gauntlet compatibility. Actual browser review traversed the cave's
optional branch and far exit, completed all tower floors, retreated between
floors and revisited completed encounters. Desktop and 844×390 landscape map/HUD
checks used disposable high-HP/damage fixtures to test flow, not balance.
Human multiplayer balance and physical-phone playtesting remain outstanding.
See `reports/DUNGEON_VALIDATION_2026-10-12.md`. No GitHub/Render publication.

## Adventure woodland prototype — local update, October 10

Create a room, select **Mode → Adventure · woodland prototype**, choose a hero
and one ability in each category, then click **Begin Adventure**. The host may
choose Easy, Medium or Hard and add an NPC companion. Run length belongs to
Gauntlet; Adventure always uses this one region. Join the same room code before
starting for co-op. This update has not been published to GitHub or Render.

Oakvale is your home village, with the existing shops, Alchemy Lab, Guild,
interiors and upstairs inn beds. The runner explains the missing hunter and
the Southern road. Map and Journal remain accessible during exploration.
Use WASD/arrow keys or the touch pad, gather at a trail arrow and press
**E / Interact** to confirm travel. Every connected human must stand there and
confirm; companions and offline players do not vote. Walking away withdraws
confirmation. A returning player catches up to the party's current area.
The map shows only discovered or revealed locations, their connections, known
quest locations and the party's position. At phone width, swipe it sideways.

| Location | Local danger | What to find |
| --- | --- | --- |
| Oakvale | 0 | Shops, Guild, inn and recovered hunter |
| Southern road | 1 | Tracks pointing toward the missing hunter |
| Woodland crossroads | 2 | Automatic direction board revealing camp, clearing and shrine |
| Abandoned camp | 3 | Defeat the guards and recover the shared repair kit |
| Hunter's clearing | 3 | Defeat the wolves and speak to the injured hunter |
| Overgrown shrine | 4 | Exchange rune clues, then defeat the Stone Guardian |
| Broken / Restored bridge | 2 | East-bank workbench, physical crossing and ruins trail |
| Old ruins | 6 | Awaken and defeat the Labyrinth Minotaur King |

Routes work in both directions. Crossroads → camp → bridge → Southern road →
crossroads forms a loop once the bridge is repaired; the shortcut makes returning
to Oakvale much faster. Crossroads → clearing → shrine → crossroads is another
loop. Each area keeps its layout and environmental changes on return. Completely
defeated ordinary groups now use the controlled ten-minute respawn rules above;
unique guards and bosses stay defeated. Ordinary groups defend a bounded
territory, pursue nearby attackers and retreat when you escape it. Wilderness
trails stay open with enemies alive. Helping the hunter and opening the camp
chest require clearing their guards. Guardian fights explicitly seal the trails.

The three larger outdoor areas each contain three separated enemy territories,
with four ordinary enemies in a solo adventure. Camp uses two groups (three
guards); bridge uses two groups (two spiders). Co-op extras are shared across
territories rather than added to every pack. Arrival lanes remain clear. Previously
visited areas keep partially fought groups; only whole cleared ordinary groups respawn;
survivors in older large layouts spread out once, preserving their HP and rewards.
Original compact saved layouts retain their positions. This update passed 223
Python tests, including seeded four-player placement and save/revisit checks,
plus an actual disposable browser approach/retreat and whole-area review.

Completing the hunter quest brings him visibly home. Repairing the bridge fills
its missing boards and opens the direct road connection. Restoring the shrine
changes its altar and removes its poison. The shrine supports solo clues or
shared clues between connected human teammates; companions do not need to solve
it. Finish all three quests to reveal/open the old ruins. The final guardian
provides a completion dialogue, reward and village celebration; exploration,
shopping and resting remain available afterward. No class is required for any
essential objective.

Equipment stays personal and Runes remain shared. Rewards are claimed once:
hunter: 20 Runes and a Healing Draught per hero; camp repair kit: 8 Runes;
bridge repair: 25 Runes and a Warding Tonic per hero; shrine: 35 Runes and each
hero's class weapon; regional guardian: 70 Runes and suitable personal equipment.
Knight receives Moonsteel Sword; Wizard/Archer Arcane Conductor; Rogue Pursuit
Blade; Druid Summoner's Staff; Cleric/Bard/Healer Dragonbone Armor. Previously
claimed rewards and existing items stay as saved; they are not reissued.
Each defeated enemy also grants 3 Runes once. Full pouches receive an item's
sale value in shared Runes. The kit is a shared quest fact rather than a tool
slot requirement. Shops and the existing small inn training system are reused.
Danger depends on location, challenge and the present party at initial enemy
creation, including the companion. Returning to town or crossing a boundary
adds no stage scaling, route pressure or town pressure. Druid summons disappear
when changing areas; ability recharges otherwise carry across travel.

### Woodland exploration and navigation pass — October 10

Approach the crossroads signpost for a large automatic direction board. No E,
dialogue or movement lock is involved; walk away to dismiss it. Its two southern
paths distinguish left (camp) and right (shrine). Reading it reveals these trails
on the shared map once. The **illustrated woodland atlas** shows forests, river,
landmark sprites and winding trails. Fog covers uncharted territory. Select a
known landmark for details, use Your party / Tracked goal to focus it, and zoom
or Fit the view; scroll or swipe to pan. Bridge and shrine artwork change when
restored. Trail exit directions follow the real route graph; illustrated
distances remain approximate, and the direct shrine trail bends. Camp now lies
south of the crossroads and east of the bridge. Reciprocal entrances use distinct
arrival points. Routes use authored, softly blended paths extending beyond exits;
far labels are small, with details and closure reasons shown nearby.

The bridge's river is physical terrain. Walking, dash and companion/summon
detours cannot cross its broken gap or walk around the river. Reach the east-bank
workbench from camp with the repair kit. Repair opens only the board span: cross
west, then follow the **north trail to the Southern road**. The heading, map and
destination names become **Restored bridge**. Saved repair facts remain intact,
including old Adventure v1 caches, without paying the reward again.

In **Journal**, choose **Track goal** for one personal objective. The short next
step appears during exploration; its known location has a map star and its next
usable exit is highlighted. Locked shortcuts are not recommended. Journal
separates active, completed and unrevealed objectives. The old-ruins entry lists
the remaining woodland prerequisites, which may be completed in any order.
Saving details and named reward receipts are expandable sections.

Two optional finds are available without changing mandatory quests: a moss cache
on the Southern road's side path (12 shared Runes and a Healing Draught per hero),
and a scorched watch off the clearing trail (8 Runes and a Mana Draught per hero).
Each adds a journal discovery and pays once, including after restart/reconnect.
No large floating quest marker reveals them. A wagon, leaf waymarker and burned
watch distinguish the larger fields; quiet travel space remains. The watch and
hunter explain that the dragon has flown beyond this woodland, leaving an
awakened Minotaur King as this region's final threat.

Arrival and world-change notices are brief. Travel lists the connected humans
who still need to gather, confirm, finish a conversation or receive a revive.
Offline humans and companions do not block it. Reward receipts identify each
recipient/item and any full-pouch conversion into shared Runes. Objectives,
discovery/reward facts and personal tracked goals save automatically; inn beds
still select recovery. Free Render storage remains temporary.

Solid environmental sprites use a stable frame by default. Characters explicitly
keep their pose loops; decorative water, small flame highlights/occasional embers
and gentle shrine light use separate overlays with independent phases. Bridge
timber/ropes/banks, tent, logs, stones and ordinary exit markers stay steady.
`prefers-reduced-motion` disables these decorative overlays while preserving
character, combat, projectile and attack-warning animations. Short landscape
dialogues retain player-left/NPC-right portraits with legible text and controls.

Validation: **218 Python tests**, **12 JavaScript suites** and all static JS
syntax checks passed. Real PNG/canvas comparisons cover static silhouettes,
localized water/fire, reduced motion and matching bridge prediction. Disposable
server tests cover topology/arrivals, passive signs, tracking, one-time finds,
all eight hero rewards, full-pouch receipts, reconnects, old saves and completed
world states. Four localhost clients handled 2,290 requests in 20s with healthy
ticks and no captured errors. Browser review at 1280×800, 844×390 and 667×375
included blocked crossing → repair → walking across, fixed camp props over time,
both optional interactions, journal tracking/map and readable touch UI. These
checks are not human multiplayer or physical-phone playtesting. See
`reports/ADVENTURE_REVIEW_VALIDATION_2026-10-10.md` and the corresponding HTTP report.
Private saves were backed up and hash-verified before local activation; none
were used as test fixtures. No GitHub/Render publication was performed.

### Larger areas and landscape play — October 10

The new scenery pass gives woodland, ruins, cavern and frost calmer ground
materials and distinct foreground objects. Expanded areas contain tree/bush,
ruin, mushroom/crystal or snow/ice clusters inside the field. Walking behind
these objects covers the character visually; cosmetic scenery does not change
enemy detection, collision or projectile blocking. Health bars and combat
warnings remain above it. Adventure landmarks, the runner, hunter, shrine
Guardian and newer equipment have matching artwork. Regional village ground
uses the same materials; existing buildings and interiors keep their art.
Sources and previews are in `art/adventure-sprites/WORKFLOW.md` and its audit.

The Southern road (1800×900), Woodland crossroads (1920×1080) and Hunter's
clearing (1440×900) are larger outdoor areas with a camera that follows your
hero. Oakvale, camp, shrine, bridge, ruins and interiors keep their compact
960×540 layouts and remain fully visible. Scenery and characters keep their
proportions. Each browser follows its own player; camera changes do not move
the party or change combat ranges.

In a larger area, **hold V** or hold **Area view** to zoom out to the whole field.
Release to follow your hero again. A quick button tap previews it for **three
seconds** and returns automatically. Combat continues during the preview.
Target selection and enemy pings account for the camera. The button is hidden
in compact rooms, interiors and rune puzzles. V is reserved for this control.

Phone/tablet gameplay requires **landscape**: rotate your device 90 degrees.
Portrait shows a rotation prompt and releases movement, attacks and revive
inputs; the party's game continues. The lobby works in either orientation.
Returning to landscape restores controls without resuming previously held
inputs. Narrow mouse-controlled desktop windows do not require rotation.

Area dimensions save with the existing version 1 Adventure record. Previously
visited areas in older saves retain their original compact layouts and content;
newly created areas use the sizes above. Start a new Adventure to get all three
expanded areas. Old Gauntlet saves/stages keep their bounds and behavior.

Camera validation: **207 Python tests** and **ten JavaScript suites** passed.
The four-client, 20-second local check handled 2,450 requests, with movement
beyond the original bounds on all four clients, no captured simulation errors
and healthy ticks. See `reports/AREA_CAMERA_MULTIPLAYER_2026-10-10.json` and
`reports/AREA_CAMERA_VALIDATION_2026-10-10.md`. Actual browser checks covered
panning, timed/held overview, target selection, enemy pings, compact-room return,
portrait rotation blocking and 844×390 / 667×375 landscape touch layouts.
These are automated/browser fixtures, not human multiplayer or physical-phone
playtests.

### Adventure saves and defeat

Adventure uses separate atomic **version 1** records in
`data/adventures/<room-code>.json`, through `RunStorage.save_adventure`,
`load_adventures` and `delete_adventure`. Gauntlet's version 1 files in
`data/checkpoints/` remain compatible. Keep the entire private `data/` folder
when transferring saves; it is excluded from Git and portable release ZIPs.
Invalid/unsupported records are logged and preserved.

Area discovery, quest states, claimed reward IDs, defeated groups, environmental
changes, bridge/boss completion, shared Runes and personal progression save
automatically after transitions, objective/kill events and game actions that
change progression/items. Completed revives save their statistics too. A failed
write produces a visible save warning. Talking to the innkeeper teaches existing
training; it does **not** set the recovery location. **Rest at an unlocked bed
upstairs** to heal the party and choose its return point. Without a chosen bed,
the return point is Oakvale's gate.

A restart restores the latest saved world and progression **at that inn bed**,
not the exact combat session. Player positions, current HP/mana, active summons,
temporary buffs and unfinished puzzle attempts are not resumed. A saved unfinished
guardian can be faced again when you return to its area. A party wipe returns
everyone to the recovery point, restores health/mana and loses **40% of shared
Runes once**. Completed objectives, claimed rewards, personal equipment and
repaired routes survive. An unfinished guardian resets on a wipe. Ordinary
defeated groups remain defeated.

Main menu disconnects while retaining the save. Use Continue saved run from the
same browser and server address, keeping site data so it retains your hero's
identity. An invite code is not a substitute for that identity. Offline members
do not block travel, and a party with no connected humans pauses.

These are local disk saves. **Render's free filesystem remains temporary**;
sleep, restart or redeploy can remove hosted saves. The separate storage
interface is ready for a future durable provider; no hosted storage service or
credentials were added. This prototype has only been changed/tested locally.

### Adventure validation

All **201 Python tests** passed. Use `python -B -m unittest discover -s tests` for the regressions, including
`tests/test_adventure.py`. Coverage includes the full quest route in solo with a
companion and a three-human party, travel/revisits, disconnected gathering during
puzzles, reconnects, fixed danger, pursuit/retreat, reward replay, visible world
facts, disk recovery, personal progression, old Gauntlet saves, save failures and
one-time wipe penalties and immediate companion consumable persistence. Enemy roles stay fixed on revisits; corrupt records do
not install partially restored rooms. Test rooms/saves are disposable. Full-route server tests
place players and defeat fixtures directly; they do not measure human balance.

`python -B tools/multiplayer_probe.py --adventure --seconds 30 --report
reports/ADVENTURE_MULTIPLAYER_2026-10-10.json` exercises four HTTP clients through
road, crossroads, camp and guardian fixtures. The completed local check handled
3,442 requests, with continuing movement for all four clients, no captured
simulation errors, healthy ticks and localhost p95 response of 18.78 ms. Extra
fixture HP isolates reliability from balance; these are not hosted guarantees.

Actual browser checks covered creating/starting Adventure, fast ability choices,
the welcome conversation, movement, clues, travel with surviving enemies, Map,
Journal, the solo shrine puzzle and fighting its guardian with held attack.
Completed-world fixtures verified the recovered hunter, repaired routes, final
completion and full map/journal. Desktop (1280×800) and narrow (390×844) views were
checked. Narrow QA exposed the existing coarse-pointer pad through the isolated
preview helper and exercised held direction buttons, tap travel, journal and
horizontal map panning; this was not hardware touch emulation. All eight browser
regression scripts and JavaScript syntax checks passed. Physical-phone comfort,
human multiplayer cooperation, hosted latency and a longer balance audit still
need playtesting. The subsequent camera update above preserves aspect ratios
and requires landscape for phone gameplay.

`tools/adventure_preview.py --scene menu|road|shrine|bridge|complete --port 8002` runs
an isolated browser fixture server with temporary saves. `--touch-controls`
exposes its movement pad for narrow QA. It adds no fixture endpoint to the game.

## Deploy on Render (free public playtesting)

Play the hosted game: **https://the-gauntlet-d0pc.onrender.com**.
Manage the current service at
https://dashboard.render.com/web/srv-db4qi6o473hc738p6k70.

The repository includes `render.yaml` for a single free Python web service.
Sign in to Render, then use
[Deploy to Render](https://render.com/deploy?repo=https://github.com/Nael-Shakhsheer/The-Gauntlet)
to create the Blueprint. Review that the service uses the **Free** plan, then deploy.
Render assigns an HTTPS `onrender.com` URL; share that URL with players.
The service uses Python 3.13, `pip install -r requirements.txt` to build,
`python -u server.py` to start, `HOST=0.0.0.0`, Render's `PORT`, and `/healthz`.
Local defaults remain unchanged.

Automatic deploys are disabled to avoid interrupting parties on every commit.
To release a new build, publish it to GitHub main and use **Manual Deploy >
Deploy latest commit** on the Render service. Every redeploy resets live rooms.
Keep exactly one instance: rooms and the simulation run in that process's memory.

Free services sleep after 15 minutes without incoming traffic and may take about
a minute to wake. Their filesystem is temporary: inn checkpoints on Render are
lost on sleep, restart or redeploy. Local saves are not uploaded. This free setup
is for playtesting; durable online saves need separate persistent storage.
See [Render's free service limits](https://render.com/docs/free).

## Controls

Sound activates after a click, tap or keypress. **Sound settings**, under
**Controls & settings**, offers master (100%), music (16%), effects (40%),
ambience (12%), UI sounds (30%), master mute, category/cue previews,
Off/Reduced/Normal shake and reduced decorative effects. These are fresh-browser
defaults; older saved levels are preserved. Settings
persist per browser/site; existing volume/mute settings migrate automatically.
Device reduced motion also disables shake and reduces decoration. Visual danger
warnings and revive information remain available when muted or audio is unavailable.

The local Bxfr/Bfxr bank now has distinct class Light/Special/Ultimate families,
confirmed impacts and rescue/danger cues. Bounded server events prevent rejected
inputs from sounding successful and discard stale combat after travel, refresh,
reconnect or hidden-tab return. Quiet stylized atmosphere uses a separate bus;
it is a procedural bed with short accents. A separate small original synthesized
score provides ten arrangements; no realistic recordings or complete soundtrack
are claimed. No audio tools are needed to play. Rebuild instructions, current
audit and ability mappings are in `art/audio/WORKFLOW.md`,
`OVERHAUL_2026-10-16.md` and `event-manifest.json`. Open `art/audio/review.html`
for tracks, individual cues and 30/40/60-second references.
Actual headphone/speaker and physical-phone listening
review remains outstanding; browser playback and automated metrics were verified.

- Move: WASD by default, or arrow keys; touch movement pad on phones in landscape.
- Larger Adventure fields: hold V / Area view, or tap Area view for a three-second
  overview. Compact rooms do not scroll or show this button.
- Dash: Space or the Dash button during combat. Its five-second recharge shows
  a countdown and progress bar; dashing is unavailable while downed.
- Light attack: hold left click on the arena or hold the Attack button to repeat
  your equipped Light at its normal cooldown. A quick click/tap also works.
  Release, switch tabs, or open a dialog to stop. Movement and attack can be held together.
- Special: Q. Ultimate: X. Both keys can be changed from Controls & keybindings in the main menu.
- Light, Special and Ultimate now show distinct ability icons. A glowing red
  circle fills around each icon while recharging, then turns green when ready
  to use, with a green contour around the icon. Druid summons show Active until they die; low mana is labeled. All 48
  designs, exact prompts and rebuild steps are in `art/ability-icons/WORKFLOW.md`.
- Heroes now perform class-specific Light, Special and Ultimate casting poses.
  Druid summons start with a ground crouch and summoning circle; Archer Ultimates
  use a massive bow, and Bard Ultimates bring out a concert harp. Every Ultimate
  erupts in colored energy and displays its ability name for teammates. Enemy
  anticipation/release effects follow their real attacks, and all four summons
  have emergence and elemental attack effects. These visuals do not change cast
  costs, damage, cooldowns or movement. Sources, exact prompts, mirrored exports
  and a local animation viewer are in `art/ability-animations/WORKFLOW.md`.
- Projectiles have dedicated four-frame flight sprites: actual arrows, tumbling
  bottles, ice shards, thorns and moving elemental energy. Deadeye launches a
  much larger arrow and Rain of Arrows uses descending arrow sprites. Prompts,
  export steps and the 23-design viewer are in `art/projectile-animations/WORKFLOW.md`.
- Every hero's Ultimate has a 15-second cooldown, including when a combat stage
  starts. New waves do not restart that timer. Mana costs are unchanged.
- Equipped utilities: 1, 2, and 3 (the number row or numpad), or click/tap their HUD slots.
  All three appear below Help/Gather/Enemy. Tool 1 and Tool 2 flank the central
  ability controls; click either tool slot to open the pouch. Movement arrows
  appear on touch devices and are hidden for mouse/keyboard play.
- Revive: stand near a downed teammate and hold E or Revive. Downed allies have
  no expiry countdown; they stay revivable while someone is standing. Reviving
  takes 1.8 seconds, or 0.8 for Healers. Everyone down at once is still a party wipe.
- Druid: both Light choices fire projectiles. Choose Lightning Bird or Fire Wolf
  for Special, and Ice Bear or Nature Rock Golem for Ultimate. Each attacks the
  nearest enemy. Its ability stays locked while it lives, then recharges for
  8 seconds (Special) or 15 seconds (Ultimate) after death. Each new stage removes
  summons, makes Special ready, and starts Ultimate's 15-second cooldown.
  Summons persist between waves. Special summons deal 90% of the
  equipped Light's damage per hit; Ultimate summons deal twice that Light damage.
- Chat: use Party Chat beside the shared game view.
  Common English profanity, insults and harassment phrases are masked in chat
  and player names. Held Light attacks do not flood the chat with announcements.

## Exploring the run

- After clearing a stage and opening any treasure, connected human players gather at the top opening. Non-town transitions have a 50% chance of a fork; otherwise the party advances directly. Town arrivals are direct. At forks, humans walk along the left or right path to the screen edge to vote. A split party uses the human majority, with the host breaking a tie. NPC companions follow and never count toward votes or exit readiness; they still count toward combat difficulty.
- Town layouts shuffle each visit, including the Guild. Seven village arrangements,
  mirrored and shifted buildings, branching paths, lanes and loops give visits
  different shapes; consecutive visits use different arrangements. Enter the Inn,
  Store, Alchemy Lab, or Guild with E, then approach the NPC inside and press E.
  Return through the door. Connected human players gather at the village gate and
  vote with E to leave; the NPC companion is not required.
- The Guildmaster offers one class change per player per run. Your current hero and heroes taken by teammates are disabled. Pick a new hero, review its six shuffled class-specific skills, and choose one Light, one Special, and one Ultimate before confirming. Back out or press Escape to cancel without using the change. Checkpoint recovery keeps your new class and the used allowance.
- Open Pouch and press Expand to read descriptions for carried and equipped items. Equip items anywhere.
- The original 22 equipable items (13 tools and 9 utilities) have individual pixel-art
  icons in the pouch, equipment slots, shop, pending chest loot and utility bar.
  The full catalog and retained artwork are in `art/item-sprites/`. Refresh the
  browser after updating the client or sprites.
- All eight heroes use imported directional sheets, as do Wolf, Serpent Guard, Minotaur, Cave Troll, Cave Spider, Dragon, Chimera, and all four Druid summons. Troll minibosses and the Ancient Stone Behemoth share the troll sheet. Each new hero/summon sheet has idle, movement and general attack/cast animations in eight directions. Elemental enemies keep their colored glows.
- Enemies have three progressive anticipation poses for charge/pounce, heavy
  attacks and ranged/channel attacks, timed to their actual windup. Attack
  release frames also play for bosses. Eight directions use mirrored side views.
- Dracos use the original compact Dragon design. Final Dragons use a new,
  much larger fierce design with broad wings, a long armored body and snarling
  jaws, including idle, walk, attack and charge/breath/channel windup animations.
  Elemental glows and phase-two growth remain. Sources, exact prompts and rebuild
  instructions are retained in `art/dragon-lineage/WORKFLOW.md`.
- Breakable crates and rocks have intact, damaged and debris sprites in all four
  region palettes. Traps show warning and raised-spike states; poison, ice, boss
  hazards, projectiles and combat effects use animated pixel art. Danger outlines
  and aim lanes remain visible. Each existing curse has a distinct icon in the
  affected player's pouch. Sources, prompts, exports and rebuild instructions are
  retained in `art/combat-sprites/WORKFLOW.md`. Refresh the HTTP page for these
  client/sprite changes; no server restart is needed for this art pass.
- Each new run makes one 8% roll for an assassination ambush, with at most one occurrence even after checkpoint recovery. Ambushes bring stronger enemies from all four sides, scaled to party size.
- Canvas animation runs independently of multiplayer polling, interpolates movement, and caches battlefield scenery and elemental glows.
- Woodland, ruins, cavern and frost battlefields use matching pixel-art scenery,
  sampled at 480x270 and displayed without smoothing. The art also remains during
  treasure and stage exits. Retained sources, prompts and rebuild instructions
  are in `art/stage-fields/WORKFLOW.md`; refresh the browser after art changes.
- Fork screens have woodland, ruins, cavern and frost versions matching the
  area the party just left. Both branches retain that style until a route is
  chosen. Their textured paths follow the existing walking corridors. Sources,
  prompts and rebuild steps are retained in `art/fork-fields/WORKFLOW.md`.
- Villages now have woodland, ruins, cavern and frost art matching the area
  just left. All six buildings, their six roof colors, furnished interiors,
  upstairs rooms, beds, stairs and doors are themed. The injured hunter's road
  also matches that region. Shuffled layouts and save/interaction locations
  remain the same. See `art/village-art/WORKFLOW.md` for retained artwork and
  rebuild steps.
- Menus, hero selection, the HUD, shops, dialogs and pouch/equipment displays
  use matching timber, slate and brass styling, with actual hero portraits and
  item icons. Refresh the HTTP page after updating these static assets.

## Party tools and puzzles

- Teammate health and a Needs revive status remain visible during play. Help and
  Gather ping your location; Enemy arms a marker, then click/tap the foe to mark.
  Tap Cancel mark to back out. Pings last five seconds and have a short rate limit.
- Multiplayer totems hold another connected player's clue. Use Share clue or
  Chat, then stand on your answers together. Rune colors do not reveal individual
  correctness; a wrong complete group answer gives shared feedback. Solo totems
  describe your own answer. Disconnections reassign clues to the remaining party.
- Optional How to play is available on the main menu and under the in-game Menu.
  It explains movement, abilities, revives, clues, town services and saves.

## Gauntlet saved runs and connections

Resting at a bed in an unlocked upstairs inn room writes a party checkpoint to
`data/checkpoints/ROOM.json` using an atomic file replacement. Talking to the
innkeeper does not save. Purchases, equipment, training and Guild changes update
the save while you remain in that saved village. A later village needs its own
bed checkpoint. After restarting `server.py`, players return to the saved bed
with their classes, items, shared Runes and progression intact. Progress after
leaving that village is lost. Runs without a bed checkpoint stay only in memory.
Older saves made before this update remain valid and return to their saved town.

Main menu disconnects without deleting your run. Continue saved run restores
your identity in the same browser and server address; keep that site's browser
data. An invite code creates a new participant in a lobby, not a replacement for
your saved identity. If moving computers, copy `data/` as well as the source;
browser identity must also remain available to reconnect to an existing hero.

A connection is considered offline after 15 seconds without requests; stale
movement stops after two seconds. Offline heroes do not block exits, route votes,
chests or puzzles. Host control moves to a connected player. The world and combat
timers pause when nobody is connected. Rejoining heroes catch up to their party.
Checkpoint files stay local and are excluded from Git. Invalid saves are preserved
and logged rather than overwriting the remaining valid saves.

## Balance observations and next work

Menu → Run stats shows overall per-player totals, including current combat: damage
dealt, damage taken, revives, deaths and kills. Damage dealt includes summons;
damage taken is hero HP lost; kills credit the finishing attacker; deaths count
falling or a party wipe, and revives count each ally rescued. Totals survive stage
changes and checkpoint retries; disk recovery restores the totals saved at the inn.
Older checkpoints start these new counters when this update is loaded. JSON export
contains the same five counters and player labels. Local server
observations append to `data/balance.jsonl`: hero/summon damage, actual HP lost,
armor/ward prevention, summon spawns/deaths/uptime and individual survival times,
stage time, party size, Ultimate casts and opening-cooldown checks. Summon HP
absorbed is measured directly; it is not hypothetical damage prevented to a hero.
Stats are fetched on demand rather than included in every movement poll.

`python -B tools/balance_probe.py` reproduces 90 bot observations across stages
1 and 8, all eight solo heroes and 2–4-player parties. See
`reports/BALANCE_REPORT.md` and `reports/balance-probe.json` for methodology,
limitations and results. These simulations do not replace human playtests.
The saved thirteen-point roadmap is `IMPROVEMENT_BACKLOG.md`.

Checks: `python -B -m unittest discover -s tests -v`, `node --check static/app.js`,
`node --check static/coordination.js`, and `node tests/test_client_actions.cjs`.
The optional canvas regression script `tests/test_damage_flash.cjs` also needs
`@napi-rs/canvas` available to Node; the game itself needs no Node installation.
`node tests/test_town_sprites.cjs` checks the imported NPC and chest animation cells.

## Hunter story and training

A peaceful clearing appears once, after stage one or two, without consuming an
extra combat stage. Speak to the wounded hunter, who was injured by the dragon,
to accept the quest. Menu → Quest shows your objective. Solo and multiplayer
parties continue once all present humans accept and gather at the northern exit.

On the first village visit, a runner approaches and all movement pauses until
present players finish the welcome dialogue. Everyone must then speak to the
innkeeper and finish the training tutorial before the party can leave. Offline
players do not hold up these interactions.
Story dialogue appears in a compact panel near the bottom of the screen so the
world remains visible, including on phones.

Hunter training has three branches, each with three ranks at one point per rank:
Vitality (+4% base maximum HP), Power (+3% base attack damage), and Focus (+5%
mana regeneration). Each hero earns one point for the first inn tutorial and
one for each of the first two great bosses, once per run. Training applies for
that run, follows Guild class changes, and persists in bed checkpoints.

The inn's stairs lead to three guest rooms. Some are locked and occupied; their
doors block entry. Use an available bed to restore party HP/mana and set its
checkpoint. Stairs return to the ground floor.

All heroes regenerate 2 mana/second in combat and 6 outside combat, before Focus
bonuses. Enemies retarget living heroes or summons when an ally goes down;
downed heroes take no further hits during their rescue window. Druid idle/walk
animation is slower, and Ice Bear/Nature Golem art is larger than the Druid.
Character, NPC, enemy and summon ground shadows are circular.

The supplied town pack provides directional idle/walk/gesture animations for the
Merchant, Guildmaster, Alchemist, Innkeeper and eight villager designs. Villagers
remain decorative. The floating chest uses its closed loop until opened, then
its open loop while players finish choosing rewards.

## Towns, routes and enemy pressure

Non-town stage transitions roll once for a fork: 50% fork, 50% direct passage.
Scheduled towns always arrive directly; fork destinations are combat regions.
Villages generate different house arrangements, connected road layouts and tree
placements. Twelve decorative villagers appear outside, without interactions.
Inn checkpoints preserve the generated town and its visit count.

Every town visited eventually increases subsequent enemy waves: +25% health, +20% damage,
+10% movement speed and +12% attack frequency per visit. Half of that visit's
increase applies on the next combat stage and the full increase on the following
stage, added to the normal stage
scaling. Empowered enemies and miniboss squadrons also receive +15% health,
+12% damage/speed and +25% attack frequency; ranged elites approach more closely.
Town pressure does not increase again when returning to an existing checkpoint.

Click Tool 1/2 or Utility 1/2/3 on a pouch item to replace that slot directly.
The displaced item returns to the pouch, including when all ten spaces are full.
Tools can replace a different tool type. Unequipping still needs an empty space.
Cave Spider enemies now use the supplied eight-direction idle/walk/bite sheet.
The saved bot balance report predates this enemy-pressure update.


## Difficulty, companions and combat update

Before starting, the host independently chooses challenge and run length, and can add one NPC companion.
The companion occupies one of the four party slots and randomly selects an
available hero and one ability of each category when the run begins. It uses the
same health, mana, abilities, equipment, revive rules, stats and enemy scaling as
another player. It attacks nearby enemies, avoids marked danger, rescues allies,
opens treasure and follows party transitions. Human teammates can revive it.
In puzzles it reads its totem and shows your clue; use Share clue after reading
your own totem so it can choose its rune. When all humans disconnect the run
pauses, including the companion. Difficulty and companions persist at the inn.
These lobby options require a new run; old saves default to Medium / 25 stages.

| Challenge | Strength multiplier |
| --- | --- |
| Easy | 0.9x |
| Medium (default) | 1.25x |
| Hard | 1.6x |

Run length is Tester (9 stages), Short (20), Standard (25, default), or Long (30). Changing
challenge preserves the selected length. The final dragon occupies the last
stage of the chosen length. Older API clients that never specify a length keep
their former challenge-based default; the current browser always sends both.

Mode multipliers apply to the updated baseline: enemy HP and damage receive
+15% overall and an additional 5% per completed stage. The exact added factor is
`1.15 * mode_multiplier * (1 + 0.05 * (stage - 1))`, on top of existing stage,
party, town and elite scaling. Attack frequency also scales by the square root
of the mode multiplier. Bosses, puzzles, minibosses and town schedules fit the
chosen campaign length, with the final boss on its last stage.

Solo normal waves have 2–3 enemies from stage 13, 3–4 from 17, and five from 20.
Before stage 7, every party size has a 10% chance of a three-wave stage; otherwise
the stage has two waves. From stage 7 the usual party and late-stage rules apply.
Stages 13–16 have a 75% chance of three waves; stage 17 onward always has three.
Larger parties increase those numbers. Bosses and special encounters retain
their own compositions. Normal enemies periodically choose a pursuit goal and
move toward that fixed goal; they no longer strafe in response to player input.
Enemy shots turn gently toward their original target for the first 1.1 seconds,
then travel straight. Boss shots steer more slowly and show larger collision art.

Large bosses and single empowered minibosses have telegraphed attacks: slams,
lingering damage pools, large projectile volleys and committed charges. The
Labyrinth Minotaur King and Ancient Stone Behemoth move 2.5 times as fast as
before, throwing rocks and charging between slams. Boss stuns are shorter to
avoid permanent Shield Bash lock. The dragon must be defeated twice: its second
phase is visually larger, has a fresh HP pool 1.6 times its first-phase maximum,
+35% damage, +20% speed and +25% attack frequency, plus group meteor warnings.
Ground circles and charge corridors warn before damage; move out of them.

The compact pouch has ten spaces. Normal chest outcomes are 55% item, 25% only
shared Runes, and 20% healing, after the existing 12% curse check. Runes/healing
work with a full pouch. The stage exit is marked by an arrow.
The floating chest's open animation is personal: it opens on your screen only
after you open your share, including while choosing a replacement for a full pouch.
The balance probe now covers all eight heroes in solo and two- to four-player
lineups. Human playtesting is still needed; automated comparisons cannot prove
that every difficulty or loadout is equally balanced.

## Battlefield, roles and companion tactics

Combat stages include breakable crates/rocks that block movement and shots.
Your Light attacks can break cover when no visible foe is in range, and area
attacks also damage nearby cover. Traps warn for .75 seconds before firing and
rearm after four seconds. Poison damages living heroes, summons and enemies
once per second; terrain weakens enemies to 1 HP so hunters earn the final kill.
Frost stages can include ice that carries momentum after releasing movement.
Cover damage and terrain persist between waves, then reset for each new stage.

Enemy behavior distinguishes chargers, ranged attackers, ambushers, bruisers and
supports. Short labels and danger marks appear during attack wind-ups. Chargers commit to a rush, ambushers flank and lunge, ranged enemies
keep distance, bruisers announce area swings, and larger groups can include a
support that heals one wounded foe. Downed heroes remain excluded as targets.
Bosses show countdowns, attack lanes/fans or danger circles, then stop during a
visible recovery period. Stronger attack-rate scaling never shortens their wind-up.

NPC companions sidestep incoming shots, escape ground warnings and charge lanes,
alternate escape directions, retreat when a ranged hero is crowded and navigate
around cover. They keep attacking as they move; rescuing yields to immediate danger.
They use their normal hero movement speed and receive normal damage.

Summon damage per hit and death recharge stay as described above. Their health
and attack frequency are lower: Bird 40 HP / 1.15s; Wolf 65 / 1.15s; Bear 125 /
1.4s; Golem 170 / 1.8s. Temporary damage boosts expire on summons too. Repeated
stuns have a 1.8-second resistance window; normal foes are stunned for .6s.
Gentle Mend and Major Mend now heal one injured ally, as their descriptions say.

Detailed contribution logs include actual healing, ward protection credited to
the caster, boost assistance, summon damage/absorbed HP/survival and stage times.
The visible Run stats and its download retain the five overall totals. See
`reports/COMBAT_BALANCE_NOTES.md` and `reports/BALANCE_REPORT.md` for 198 matched
before/after simulations. Reproduce with `python -B tools/balance_probe.py
--before-tuning` and `python -B tools/balance_probe.py`.

Story conversations show your hero and response on the left and the NPC and
dialogue on the right, in compact boxes. Equipped utility icons flank the central
interaction prompt: slot 1 on the left, slots 2/3 on the right. Keys 1/2/3 still
work, as do clicking/tapping the icons. The guide now explains battlefield hazards.


## Deliberate combat, controls and Dracos (2026-10-07)

Normal stages now scatter one or two breakable cover objects and one terrain
zone across the field. They persist through waves. Occasional objective stages
ask you to destroy a summoning rift, defend a ward for 32 seconds against
reinforcements from different edges, or bait a charging sentinel into rocks
for a two-second recovery opening. They begin from stage 4 and avoid scheduled
bosses, minibosses, puzzles, towns and ambushes. Objective stages are one wave;
ward destruction ends the attempt and allows the existing checkpoint retry.

From stage 17, ordinary enemy groups can include Dracos: small dragons with
124 base HP, 7 base damage and 108–126 base movement speed, before regular
scaling. They alternate a gently tracking shot and a close-range bite. Their
1.25s base attack cadence increases DPS through frequency, while .35/.4s
wind-ups remain visible. Moving beyond 55 world units avoids the bite. Their
sprite uses the existing dragon sheets at a smaller scale. Objective
reinforcements and assassination ambushes do not multiply the Draco count.

Click/tap an enemy to prefer it, or use Tab to cycle targets. Clear target or
Escape returns to automatic selection. An out-of-range or blocked preference
falls back to an eligible enemy; this does not extend ability range or bypass
cover. The local hero and selected enemy have distinct markers. Ordinary
combat names and permanent role labels are reduced, while warnings and health
remain visible. The exit keeps its arrow without the rectangular overlay.

The local hero now predicts movement immediately between authoritative server
snapshots; collisions, damage and outcomes remain server-owned. Input requests
are coalesced and sequenced so stale directions cannot overwrite key release.
Other actors still interpolate. Prediction stops after 250ms without a fresh
snapshot. Opening dialogs, downing and transitions stop movement normally.

The compact pouch hides unused equipment slots; Expand shows every slot. A
separate curse sprite slot always shows active curse art, name and remaining
stages, or an empty placeholder. It does not consume one of ten item spaces.
The corrupted dash in chest notices is corrected. Leaving via Main menu now
explains that Continue needs the current server session, while only upstairs
inn-bed checkpoints survive a restart. It offers Keep playing before leaving.

See reports/DIFFICULTY_AUDIT.md for 81 generated campaign curves and the limits
of the historical run evidence, and reports/COMBAT_UPDATE_VALIDATION.md for
regression, protocol and browser checks. Physical-phone and human multiplayer
playtests are still required, including portrait camera/aspect comfort.


## Temporary Tester mode

Choose **Tester · 9 stages** under Run length before starting. It stays available
until the user asks to remove it, and works with Easy, Medium or Hard and an
optional NPC companion. Stage progression maps to the usual 25-stage campaign:
1/4/7/10/13/16/19/22/25. Enemy HP, damage, speed ramp, group sizes, wave counts,
terrain damage and objective HP use that accelerated progression.

Tester has a miniboss at stage 2, great bosses at 3 and 6, a town at 4, a puzzle
at 5, a random rift/ward/charger objective at 8, and the two-phase dragon at 9.
Ordinary late waves guarantee one Draco from Tester stage 7; normal campaigns
retain their stage-17 introduction. Story, inn training/beds, class choices,
15-second Ultimate cooldowns and human-only votes still work normally. The HUD
shows Tester stage progress. Bed checkpoints preserve the mode and schedule.


## Portable ZIP packaging

Run `python -B tools/package_game.py` to package code, runtime sprites, original
art, documentation and tests into `releases/`, with a file manifest, checksum
and archive verification. Add `--include-checkpoints` for a local transfer that
preserves your upstairs-bed saves. Unzip the The-Gauntlet folder, run
`python server.py` there, and open `http://127.0.0.1:8000/`. Python3.10 or later
is required; the game server uses the standard library.

ZIPs, Git metadata, Python caches and data backups are excluded from source
control. Checkpoints remain local and are never included in a GitHub commit.

Add `--runtime-only` for a smaller playable ZIP. The GitHub source includes the
Python server, complete browser client, all runtime sprites and sounds, tests,
and licensed audio rebuild sources. Large original visual-art projects and
reference screenshots remain in the full local source/art ZIP. Neither public
source nor the default playable ZIP contains your bed saves.

## Tactical abilities, equipment and boss identities (2026-10-07)

Druid Briar Bolt spreads damage within 65 world units and briefly roots groups;
Thornshot fires faster and deals more sustained damage to one enemy. Wizard Arc
Bolt jumps to two nearby enemies with decreasing damage; Frost Lance deals less
sustained damage but controls a single enemy. Cleric Radiant Flask splashes a
75-unit cluster; Sanctified Throw is a faster, stronger single-target projectile.
Roots resist repeated application and have shorter duration against bosses.

Archer Rain of Arrows commits to the chosen enemy's position at cast time, up to
380 world units away, then strikes a 110-unit radius after 0.65s. Enemies can
leave that area. Cover blocks target selection. Rogue Death Bloom now applies
five seconds of bleeding to enemies hit. Ability descriptions expose the actual
range, area, delay and effects.

Four additional shop/loot tools encourage different builds. Arcane Conductor
reduces direct projectile damage by 20% in exchange for an extra half-damage
jump. Rescuer's Cuirass has only +1 ordinary armor but protects a manual rescue
for up to two seconds, with an eight-second recharge. Summoner's Staff increases
Druid summon HP by 50% while reducing the Druid's direct damage by 25%. Pursuit
Blade reduces ordinary direct damage by 15% but rewards one damaging follow-up
within two seconds of Dash, Blink or Shadowstep. These effects do not stack with
duplicates. Swapping summon equipment preserves summon health percentage.
Pouch and shop comparisons show damage/armor deltas plus gained and lost effects
for each tool slot. New tools reuse existing item art with distinct border hues.

Great bosses have signature mechanics as well as their familiar attacks:

- Minotaur: bait a charge into cover for a three-second opening and +35% damage.
- Ancient Stone Behemoth: raises and shatters breakable cover.
- Serpent Matriarch: lays connected poison areas; a successful control stun during
  her wind-up interrupts the weave.
- Fire Dragon: commits burning lanes; Ice creates breakable lane barriers;
  Storm marks positions and punishes grouped allies. Dark constrains the arena
  with a ring and Arcane uses alternating cross/center strikes.

The boss tactic line explains each fight. Dragon armor and an armor-cracking
warning foreshadow the larger true form. Phase two strengthens the elemental
mechanic, with a brief transition recovery before attacks resume.

See `reports/TACTICAL_UPDATE_VALIDATION.md` and `reports/TACTICAL_LIGHT_PROBE.md`.
Automated measurements verify implementation and relative attack roles; they
do not replace human multiplayer or physical-phone balance tests.

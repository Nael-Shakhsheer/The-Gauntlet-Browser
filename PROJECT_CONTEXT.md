# The Gauntlet - project handoff

Last updated: **2026-10-16**.

## GitHub source release — October 16

This source release consolidates the current Adventure systems, woodland/Dunmere
story, opening battle, hero/Ascension progression, shrine/crystal travel,
awareness/respawns, UI/artwork, audio/music and performance improvements.
Publication is based on GitHub main `ee51514`, preserving its prior hosted fixes
and history rather than replacing it with the older local main branch.

The public snapshot includes runtime assets, code, tests, documentation and audio
rebuild sources. Private data/, credentials, logs, reports, release packages and
non-audio authoring artwork are excluded; local originals remain. The obsolete
26 runtime exports are removed from the public static tree. Existing unrelated
remote files are preserved. Full artwork sources remain local under art/.

Fresh checks before publication: 364 Python tests passed, zero failures/errors/
skips; all 26 JavaScript client suites passed and all static JavaScript syntax
checks passed. Snapshot files were hash-verified and scanned for common credential
patterns. These checks are not a new human multiplayer/balance/listening review.

Render auto-deploy is off in render.yaml. This is a GitHub source update; the
hosted game requires a separate deployment. No local game server restart or
private-save upload is part of this publication.

## Adventure systems pass — October 16 (latest)

Implemented the 12-part request in attachment
`4f09e856-3b76-40a2-94a8-7ef5216ca340`. Local development only; no GitHub/Render
publication. This section supersedes earlier finite-outdoor/free-recall behavior.
Do not redo the prior opening, woodland expansion, dungeon, UIv3, artwork, audio
or demand-loading work. Private saves were never fixtures.

- `enemy_awareness.py` owns transient unaware/investigating/alert/searching/
  returning states, range+LOS, last-known positions, three-second search and brief
  !/? cues. Adventure detection has .25s investigation; Gauntlet retains immediate
  acquisition. Hidden/downed/offline actors and invalid taunts cannot acquire or
  steer homing. Committed role/boss attacks retain recorded aim. Direct visible
  LOS hits can alert; bleed/summon damage cannot expose a hidden owner's position.
  Offensive casts break concealment; incidental hazards/projectiles still damage.
- `exploration_movement.py` replaces Adventure's combat-only dash gate with explicit
  eligibility. Roots, downing, dialogue/Guild/interiors, menus, cooldown, scene and
  collision checks remain. Village dash uses <=6px swept steps with actual town
  walkability; dungeon/river/cover uses existing terrain movement. Client matches
  eligibility and specific rejection reasons. Gauntlet combat dash unchanged.
- `dialogue_choices.py` adds server-validated ID/page/revision choices, region/
  practical questions, distinct attitudes, back/leave, available runner accept/
  report actions, and caretaker treatment. Action choices precede optional lore.
  Saved personal `dialogueDecisions` v1 is separate from shared sequential chapter
  facts. Object inspections stay plain. `static/chapter.js` uses existing journal
  state for Available / Active+Ready / Completed tabs, actionable default and
  retained focus/scroll. No second quest state model.
- `hero_skills.py` keeps woodland safe-hub learning/equipping and existing eight
  trees. All eight fresh heroes tested earning/spending starter points, equipping
  and casting in the road. `magic_runes.py` now explicitly requires turned-in
  `chapter_outcome` (Dunmere conclusion) plus15 current unspent Magic Runes for new
  Ascension; previously Ascended saves are grandfathered. Skills explains ordinary
  safety separately from Ascension. No ordinary XP/grind progression added.
- `soul_crystal.py` v1: permanent personal20-cap tool, initial20; ordinary1,
  eligible elite/mini-boss3, final boss5. Connected living humans within450px share
  credit; downed humans need recent participation<=30s. Companions can contribute
  kills; bots do not hold crystals. Stable origin→highest-generation receipts,
  bounded1024, reject duplicate/replayed lives. No per-soul sound/particles.
- `village_portals.py` and client travel UI now use discovered spatial map nodes,
  inactive reasons/current position, selection panel, Previous/Next keyboard/touch
  targets and existing wheel/zoom/pan. The compact crystal charge stays in the HUD;
  Menu also offers Travel map. Free method requires a source shrine; crystal
  method requires20 from EVERY connected human. Pending invitations wait while
  teammates approach, expose names/readiness and then channel3s. Offline/bots do
  not block. Movement/damage/locks/nearby enemies interrupt. Charge+area+landing
  commit through one confirmed save with whole-room rollback on failure; HP/CD/
  recovery stay unchanged. Legacy portalReturn facts preserved but arbitrary free
  trail-return destinations no longer exposed. Cached details avoid50ms button
  replacement that actual browser review caught. Old-server client mismatch gives
  a readable restart notice rather than a JS exception.
- `outdoor_respawns.py` v1:600s wall-clock due time after whole ordinary group dies,
  checked at most every2s and only in unoccupied areas. Partial groups never reset.
  Stable origin/lifeGeneration and templates persist. Old cleared authored groups
  reconstruct only known defeat receipts, with a FUTURE timer on first revisit.
  Exclude hunter wolves, camp guards, mill quest guards, shrine guards, bosses,
  opening, dungeon waves and hubs. Repeat generation payout1 ordinaryRune/kill,
  cap6/group/cycle; no unique loot/MagicRune/milestone duplication. Timing remains
  prototype balance, not human-certified recharge/ten-minute pacing.
- `cottage.py` v1 adds Mara,5 shared ordinaryRunes for personal living HP+mana.
  Fullbothfree; revision/request receipts, authoritative proximity and save-failure
  rollback prevent duplicate payment. No bed/CD/crystal/point changes. Existing
  innkeeper artwork reused; house/service labels identify cottage recovery.
- `acquisitions.py` publishes private item/pending/conversion/MagicRune notices
  after confirmed Adventure storage; transient restore baselines prevent replay.
  No steady-tick inventory deep-copy (focused regression). Client bounded24 queue,
  one3.2s toast, coalesced related audio and existing restrained rune effect with
  personal balance; muted/reduced settings respected. Shrine first attunement no
  longer immediately opens a map over the acquired-rune toast.
- `region_content.py` adds `eastern_threshold`1280×800 danger6, fields upper-east
  exit .32/reversewest arrival; cellar hatch remains lower-east .67. Two territories,
  authoritative shed footprint, existing granary art, sparse/bare scenery, cached
  dry ground and optional `east_landmark` clue. Future Ashen Ridge explicitly closed;
  not another completed biome. Irrigation retains green; fields/threshold foliage
  gets bounded straw palette cache; at most2 ground canvases (~4MiB), no art-pack
  regeneration. Restrained effects/following camera/mobilelandscape preserved.
- `adventure.py`/`save_portability.py`: additive validated personal/generation fields
  within existing Adventure worldv1 and portablev2. Old absent fields migrate;
  unsupported records retain existing rejection/preservation protections. Awareness,
  search clocks, UI/acquisition baselines and channels remain transient. Existing
  save slots/export/import, world/character identity and Gauntlet compatibility
  pass. Real cloud remains unconfigured; Render free disk remains temporary.

Validation: **364 Python passed /0 failures/errors/skips (76.855s); 26 client suites
and29 JS syntax checks passed.** Full isolated `tools/run_tests.py`; no private
fixtures. Old steering/retarget tests now explicitly remove random cover when
testing open-sightline behavior; LOS production checks were not weakened. Expected
injected disk errors in log verify rollback/confirmed-notification behavior.
Latest small old-server UI guard also reran systems/map-navigation suites+parse.
See `reports/ADVENTURE_SYSTEMS_VALIDATION_2026-10-16.md` and SYSTEMS_* raw results.

Actual ordinary-stat fresh Rogue UI: learned/equipped/cast woodland skill, road
walking/dash/combat, retained14/80HP through charged recall, response attitude/back/
accept and runner tabs. Late Dunmere access was helper-completed (normal Knight
stats, no gear), not earned: cottage full-resource free treatment, following camera,
fields→threshold walk, map selection, crystal depletion, restart recovery and free
shrine travel at0 charge with offline host. Final latest-server browser repeat
retained110/150HP across fields→threshold, reviewed imported granary/straw palette
at844×390 and found no console warnings/errors. Desktop1366×768 also reviewed.
Screenshots in `reports/screenshots/systems-*`. Human co-op, physical phone,
perceptual audio, earned whole chapter and long respawn/recharge balance remain
outstanding; clock-driven tests are labeled automated.

Final isolated comparable seeded benchmark (`COMPLETION_PERFORMANCE_systems-final*`):
tick means .083/.211/.097/.265ms (Brook1/Hollow4/Dunmere4/Cellar4); p95
.152/.375/.195/.466ms. Compact payload medians11,184/16,781/16,498/14,509bytes,
up627–1,001bytes from prior combined build for new live status/navigation.
Explicit saves29.08–33.36ms means/max39.75ms; disk/locks retained. No FPS, network
latency or long-session plateau certification. Documentation/report gives full
comparison and existing remaining durability/serialization costs.

Local activation completed20:34 EDT after verifying8 private save files in
`data/backups/before-adventure-systems-20261016-203352`. No8000 listener was present
at activation, so no unrelated process was stopped. New process24884 passed
health/build/HTML/new-client-route checks: server `d5b02b1d62ad`, client
`c08b45d73dbd`, protocol2 at http://127.0.0.1:8000/. See
`reports/SYSTEMS_ACTIVATION_2026-10-16.json`. Refresh clients. QA listeners stopped
and viewport override reset. Existing live-room/bed recovery rules still apply.

The reattached request `daad780d-33b8-4580-b623-5729f2688303` has the same SHA256
as the implemented request above. Reviewed current source and confirmed the live
8000 build still matches `d5b02b1d62ad` / `c08b45d73dbd`. Fresh isolated recheck:
19 Python tests (6 awareness/dash +13 Adventure systems),0 failures/errors/skips;
5 client suites passed (systems, map navigation, movement, network recovery,
landscape). Raw results use `SYSTEMS_REQUEST_RECHECK*`. No additional gameplay
edits, private-save access for tests or server restart were necessary. The full
364-test/26-client results and browser screenshots above remain prior validation,
not a newly repeated full suite or human playtest.

## Audio and score extension — October 16 (current)

`art/audio/OVERHAUL_2026-10-16.md` supersedes the October 11 audio routing audit.
198 Bfxr recipes retain DSP/vendor/license/manual-export protections; ordinary
hits are quieter, actual projectile families/materials coalesce duplicate hits,
and accepted UI/quest/skills/rune/Ascension outcomes have cues. `feedback.py`
adds bounded launch/collision and committed-outcome metadata with cause IDs for
reward coalescing; no combat damage/cooldown/movement rules changed. New
`static/audio-routing.js` owns cue policy. Restrained visuals and stable scenery
remain. Scene identity includes Adventure area/dungeon floor; travel/reconnect/
hidden baselines discard old combat. Critical/personal cold loads have a
cancellable 250 ms grace, never an unbounded replay queue.

`static/music.js` adds ten original editable synthesized arrangements including
Oakvale refuge, worn Dunmere and Caravan tension-to-refuge, with delayed combat
engagement, five-second hold, crossfades and hidden/mute/disconnect/defeat stop.
Sources/notes/permission are in `art/audio/music/`; WAVs/manifest in `static/music/`.
Music does not replace Bfxr effects. Runtime needs no authoring dependencies;
music/review authoring needs Python+NumPy (tested 2.3.5), effects need Node.
`art/audio/WORKFLOW.md` has portable builds and manual-export protection.

Settings v3 under gauntlet-audio preserve old preferences; defaults are master 1,
music .16, effects .4, ambience .12, UI .3. Independent levels/previews, master
mute, reduced decoration and shake remain browser-local. Effect decode cache is
8 MiB; music cache <=two tracks/32 MiB; effects voices tiered 6/8/10. Sparse
procedural/Bfxr atmosphere includes dry areas; no prop/actor idle loops. Server
serves strict music files/new scripts; refresh clients after local activation.

`art/audio/review.html` is the current playable reference. Validation: 338 Python
tests and 24 client suites; synthetic 180-second trace with 12,988 events/peak eight
voices, plus browser Caravan/dungeon/boss, Ascension and settings checks. See
`reports/AUDIO_OVERHAUL_VALIDATION_2026-10-16.md` for exact evidence and limits.
Actual listening and physical-phone/Bluetooth review remain outstanding; do not
claim a complete soundtrack, realistic recordings or completed listening.
No publication/deploy. Back up saves before restarting the real local server.

Local activation completed October 16 after hash-verifying eight files in
`data/backups/before-audio-music-overhaul-20261016-152217`. Server process 42988,
HTTP health and new audio/music routes passed; server/client source fingerprints
`db34f457077a` / `6a83de5a0a09`. See `reports/AUDIO_ACTIVATION_2026-10-16.json`.
Existing in-memory rooms reset; saved recovery remains. Refresh other clients.

## Completion and performance audit — October 16 (current)

See `reports/COMPLETION_AUDIT_2026-10-16.md`: requirement-by-requirement statuses,
implementation/evidence/remaining work, explicit prior-browser versus renderer/
helper distinctions, raw measurements and prioritized follow-up. No GitHub/Render
publication. Do not redo the completed expansion or UIv3/healer art that arrived
concurrently with this audit.

- Demand-load imported hero/enemy sheets/metadata, regional field/fork/ground
  fallbacks, Adventure PNG packs, hero ability sheets, flight banks, NPC/chest and
  enemy/cover atlases. Preserve existing village lazy loading and all source art.
  Initial observed static menu resources169→47, encoded28,949,642→3,310,487 bytes.
  PNG header RGBA estimate137,891,084→7,894,016 bytes; **not resident GPU memory**.
- `game.state` full response remains backward compatible. `/api/state` negotiates
  four immutable catalogs with the server fingerprint and skill UI with a token
  covering build/class/progress/loadout/legacy/Ascension/safety/slot count.
  `static/state-cache.js` reuses only matching same-room/player data; stale or
  missing tokens force a full refresh. Dynamic simulation/acknowledgements,
  cooldowns and eligibility always fresh. No change to50ms poll cadence/authority.
  Seeded steady responses shrink56.8–66.8%; profiled state work25.3–45.2%.
- WeakMap cache for stable scenery wrappers/bounds retains fade/depth behavior.
  Package filters omit reports and authoring WAV previews in runtime mode, and
  private env/key/log files in either mode. Sources/tests/licenses/rebuild files,
  artwork/backups remain on disk. Same final safe files:53,080,027→49,713,341 bytes
  uncompressed runtime contents. Whole-project size grew with concurrent art/Git/
  reports; never equate development-storage savings with FPS.
- Technical details now available in front-menu Settings with bounded timing and
  same-origin static Resource Timing (no API query/save/player data). Two malformed
  CSS glyphs corrected using Unicode escapes; preserved UIv3 styling.
- Full isolated Python334 passed/0 failures/errors/skips (66.865s), client21 suites
  and24 parse checks passed. Latest performance4 and HTTP3 subsets rerun, all pass.
  Default sandbox HTTP rerun hit WinError10013; authorized localhost socket run
  passed without weakening app locks/writes. Raw reports use COMPLETION_* names.
- Actual fresh normal Knight browser: skipped intro explicitly, village arrival,
  walking/release/menu stop, road combat/retreat and scrolling, overview/fogged
  atlas/cave prompt at1366×768 and844×390. Console inspection before browser-tool
  timeout had no game errors. Attempted Rootwater entry timed out in browser
  automation; after recovery last state was road/prompt, so **not counted** as an
  interior traverse. QA server8094 and its tab stopped; viewport reset. Prior
  Later recovered the browser check: ordinary cave entry/map/retreat, HP89/150
  retained across boundaries; wheel zoom125→188%. Another ordinary approach safely
  avoided the packs. Fixed a screenshot-proven short-landscape interior-map issue:
  compact two-column card leaves~220px of chart beside progress and expandable
  notes. `audit-rootwater-map-fixed-844x390.png` and actual arrival captured.
  A full cave/boss clear still was not performed. Prior
  October15 ~96s Healer Caravan and earned Brook rune purchase remain prior actual
  evidence; late Dunmere/Ascension remains helper-completed, not earned campaign.
- Explicit durable saves31–39ms mean/max52ms; atomic replace/fsync/locks retained.
  Browser ACK/render observations improved but focus/new artwork confound causal
  FPS/latency claims. No long-session resident-memory plateau or multi-room load
  certification. Physical phone, four-human co-op, full earned campaign pacing,
  all8 human Ascended builds and audio listening remain outstanding. Cloud recovery
  unconfigured/untested against real durable storage; no hosted durability claim.
- Activated local8000 only after hash-verified6-file backup
  `data/backups/before-completion-audit-20261016-100608/`. PID27584, server
  **5fdcf71253f6**, client **5563a3e5732a**, protocol2. Live/source match;8 known
  health/build/script/sprite routes200/no-store. One initial diagnostic guessed
  an unused projectile filename404; all actual flight banks verified200. Restart
  resets live rooms per established rule; existing saved facts/beds retained.

Final combined activation supersedes that preliminary fingerprint/PID: further
audio-routing/music and Ascended sprite edits arrived concurrently and were
preserved. Full Python suite rerun after the last Python edit:334 passed,0 failures/
errors/skips,77.441s (`COMPLETION_PYTHON_FINAL_2026-10-16.json`);21 client suites and
27 JS parse checks pass (`COMPLETION_CLIENT_2026-10-16.json`). This does not certify
perceptual audio comfort. Final server **c11cd7bcd313**, client **6fc4161ac92c**, PID39684
at8000. Fresh verified6-file backup `data/backups/before-audit-final-20261016-103009/`;
health/build/state-cache/music/audio-routing/ascended-sprites routes200/no-store,
live/source hashes match (`COMPLETION_COMBINED_ACTIVATION_2026-10-16.json`). QA8094
and owned tabs stopped; viewport reset. No publication/deployment.

Combined menu snapshot server4664ec9f4e97/clientc66745f973fa:51 initial static requests,
3,429,646 encoded bytes;78 /6,157,577 after Settings/audio. This has new concurrent
audio work and is separate from the controlled October15 pair. Combined inventory
477,194,325 project bytes,76,100,941 uncompressed runtime candidate,3,550,768 bytes
omitted by the new package filter on those same files. New music/art accounts for
content growth; nothing deleted. `COMPLETION_PERFORMANCE_combined-2026-10-16.json`
has repeated same-fixture server measurements; earlier benchmark figures remain
dated evidence. AST dependency inventory covers35 root Python modules, no external
runtime imports. Node/canvas/audio vendor sources are authoring/test dependencies.

The older section below describes the expansion activation before this audit;
its fingerprints/PID are historical. Current audit is local only.

## Last Caravan, expanded woodland, Dunmere and Ascension — October 15 (current)

Both latest pasted requests are implemented locally. No GitHub publication or
Render deployment. See `reports/WOODLAND_EXPANSION_VALIDATION_2026-10-15.md` for
activation/build details, exact evidence and limitations. Earlier work-log pending
notes and older handoff sections are historical; do not redo these features.

Activated port8000 after a verified 6-file backup in
`data/backups/before-woodland-dunmere-ascension-20261015-114429/`.
Live server **8a2840e150ba**, client **f1fce0b19386**, protocol2; read-only health/
new-client-route checks all returned200/no-store and fingerprints match source.
Local Python3.12.14 validated; .python-version still targets3.13 for deployment. Owned
QA servers/clients stopped and viewport reset. No private world used as fixture.

- `static/world-scenery.js` fades complete overlapping decorative objects using
  visible sprite bounds, short entry/exit hysteresis and a smooth transition.
  Local hero, actors, warnings and interaction markers stay opaque. No rectangular
  hero clipping/redraw. Portal/roof/dungeon/feature bounds match imported artwork.
  Explicit deterministic scenery profiles keep Gauntlet arenas sparse (cap10),
  bosses especially clear (cap6), and Adventure/village/route density independent.
  Server-owned tactical cover, collision and projectile blocking are retained.
- `opening.py` / `static/opening.js`: new Adventures start in The Last Caravan,
  a finite controllable road battle with bounded guard support, distant dragon/
  watch impact, withdrawal muster and Oakvale aftermath. Version1 ordered durable
  facts discard transient clocks; retries reset only unfinished encounters, cost
  no wipe currency and cannot farm arrival points. Skip introduction completes
  the same facts without skipping the chapter. Old/imported worlds bypass it.
  Connected humans gather; companions/offline players do not block. No-connected
  parties pause. Mid-opening joins share the existing attempt.
- `progression.py` explicitly distinguishes NPC dialogue, object inspection and
  signs; unknown titles no longer acquire a human portrait/reply. Signs open and
  discover directions only after E/tap. Rescue priority/exact-target validation
  remain. Quest/report panels use their own compact presentation.
- `chapter_flow.py` version1 provides11 shared sequential assignments: hunter,
  bridge, water, shrine, watch, ruins, border, failed harvest, irrigation, cellar,
  local conclusion. Accept/report explicitly with the Village Runner; ordinary
  early evidence is cached. Border accepts in Oakvale and reports in Dunmere.
  Main mechanisms/bosses explain accepted prerequisites. Old completed woodland
  migrates to the border offer without replay or repeated historical shop payouts.
  Completed cards show outcomes and next leads; tracking follows known routes.
- `region_content.py` adds11 stable areas: brook, mill trail, logging yard, hollow,
  burned watch, old network approach, border road, Dunmere, failed fields, ruined
  mill and cellar. Authored larger spaces/paths/territories, recognizable landmarks,
  loops and optional spring casket; no stage/town pressure. Ordinary outdoor
  respawn generations were added by the later systems pass above.
  Rootwater, Briarwatch, existing IDs and physical bridge shortcut remain intact.
  Outdoor atlas extends discovered geography; cellar uses a separate interior map.
- Three guarded travel shrines (Brook/Deepwood/Watch) separate permanent world
  activation from once-per-character attunement rewards. Watch also needs its
  register. Existing interruptible3s safe portal channel supports visited villages
  and active shrines, requires connected-human gathering, rejects nearby danger/
  seals, and preserves resources, recharge and the recovery bed. Late humans can
  claim their own shrine receipts; shared chapter rewards reconcile once.
- Dunmere has all existing hub services, a central portal and upstairs recovery
  beds. Per-hub room/lock state preserves Oakvale. Fixed a new exit placement
  collision with Dunmere's Guild (seed104731): select deterministic clear exit,
  arrival and edge points and route full-width roads with existing collision rules.
  24-seed accessibility regression passes; town generation itself is unchanged.
- The playable Dunmere chain investigates3 field sites, clears2 channels/operates
  the sluice, seals and defeats the Blighted Overseer in the mill cellar, recovers
  the additive ledger and reports a local resolution. Restored water/green strip,
  completed dialogue and permanent cellar-to-fields hatch show consequences.
  An interrupted sealed fight restarts coherently; fixed kill/reward receipts and
  wipe-once recovery remain. Legacy Adventure area/splash attacks now respect LOS
  against these walls as well as older dungeon walls. Pumping works/Ashen Ridge
  remain explicitly future leads, not playable regions.
- `magic_runes.py` version1 adds personal Magic Runes, separate from shared shop
  Runes. Ledger was written before reward implementation:8 guaranteed woodland,
  1 optional spring casket,7 guaranteed Dunmere. Finite report/shrine/cache IDs,
  retry receipts, expected ranks and confirmed-write rollback protect purchases.
  Health/mana cost1, +5% unmodified class base per rank, additive/cap5 each, rounded
  upward. Preserve current fractions/downing, old training and recharge on load/
  purchase/class change. Ascension costs15 CURRENT unspent. Only16 exist in this
  content: buying more than one ordinary rank prevents Ascension here; UI warns.
- `ascension.py`: all8 heroes have a real signature,2 functional passives and
  baseline +10% base HP/mana/+8% damage. Signatures commit for0.6s, cost mana/use
  normal slot and ability recharge, obey LOS and reuse existing art/audio. Knight
  committed strike/party barrier; Wizard controlled cluster; Archer piercing line;
  Cleric cleansing mixture; Rogue collision-safe lunge; Druid roots/summon accord;
  Bard interrupt/march; Healer rescue/barrier. Steady actor identifier, previews,
  actual before/after stats and Ascension branch in Skills. Learn/equip/purchase
  safely in either village. Guild changes retain Ascension and select the new kit;
  respec cannot refund Magic Runes or bypass cooldowns. Gauntlet is unchanged.
- Portable savev2/worldv1 extends additively with opening/chapter/region/hub/shrine/
  personal progression records. Validate versions, costs, prerequisites, receipts,
  world facts and bed geometry before importing. Originals/private identities are
  preserved. Existing optional cloud projection uses the same records; no cloud
  setup/credentials/uploads changed. Local disk only remains usable; Render free
  filesystem is temporary. Save status still waits for confirmed storage.
- Final isolated validation:330 Python PASS,0 failures/errors/skips (83.397s);
  19 client suites PASS,0 failures;23 JS syntax checks PASS. Includes18 expansion,
  8 opening and4 chapter tests, old saves/Gauntlet, one-time claims, rollback,
  all8 casts/passives/stats, class/respec, dungeon retry, offline/late joins, portals,
  LOS, hub geometry, export/recovery. No private saves used as fixtures.
- Actual browser: ordinary Healer+Cleric caravan~96s; ordinary Knight+Rogue cleared
  Brook, attuned, recalled and purchased earned Health150→158. Desktop1366×768/
  landscape844×390 reviewed. A HELPER-completed world separately tested Dunmere,
  3 personal attunements, exact15 Ascension, signature equip/cast and restart
  recovery. It is not an earned chapter playthrough. Gauntlet Tester lobby/live
  arena and returning to the preserved Adventure worked. Fresh game page recorded
  no warnings/errors. Browser-tool telemetry403s are external to the game.
- Automated ordinary probes:12 caravan party setups all93.25simsec;9 normal-stat
  shop-kit encounters6.45–37.6simsec/zero downings. Functional fixtures, not human
  balance certification. Four-palette wave/boss readability inspected in imported-
  asset renderer fixtures. Human multiplayer/full chapter balance, physical-phone
  play and perceptual sound listening remain outstanding. No new balance claims.

## Adventure controls, distinct worlds and eight hero trees — October 13–14 (prior build)

Local implementation only; no publication/deployment. Preserve the existing asset
cleanup, lazy loading, dungeon/portal artwork, atlas, foreground cutback, collision,
following camera, landscape gate, saves and Gauntlet loadouts. This pass supersedes
the older movement values and Adventure pre-run/training presentation below.

- Reproduced a concrete new-game failure: create/join responses included a private
  recovery proof, but the client retained only room/player. Strict-session polling
  then failed, leaving the lobby empty/disconnected. Full proof-bearing identities
  now survive creation, Continue and browser recovery. `session_flow.py` introduces
  explicit new-run/party-join operations, private idempotency receipts and boot
  guards for ambiguous creation timeouts. New worlds/characters are distinct;
  canceled or superseded responses cannot take over another screen/session.
- Main actions are New Adventure / New Gauntlet run / Continue / Join / Settings.
  Remembered cards query protected summaries. Main menu is distinct from checkpoint
  recovery; Change mode opens a separate run, never converts a world. New Adventure
  starts immediately in Oakvale; Gauntlet retains the classic lobby, host options
  and three-from-six choice. New party members join in Oakvale with an unused hero;
  returning characters use their private Continue identity, not just a room code.
- Instrumented bounded anonymous render/request/state-age/dispatch/ack/release/
  correction metrics and outermost RLock/tick/disk timings. Build fingerprints
  distinguish live Python from refreshed JS/CSS; `/api/diagnostics` is proof-checked.
  UI access: Menu → Technical details. No personal data is included in samples.
- The single in-flight input request could block direction/release behind a lost
  five-second request. `input-transport.js` cancels superseded input, uses ordered
  sequences, a 450ms timeout and 180ms active heartbeat; server deadman is 650ms.
  Scene/session epochs reject old input. Opening menus, rotation, disconnect and
  switching worlds release inputs and cancel transient work. Prediction is bounded
  to 200–350ms and correction speed to 8% of walking speed; authority is retained.
  Anchored simulation deadlines remove work-plus-sleep drift. Avoided duplicate
  interaction commits and transient-target saves, retaining atomic writes/locks.
- `interactions.py` owns nearby target, action, range and eligibility. Revive
  precedes props/exits, repeated hold cannot restart it, canceled hold tokens
  reject late rescue requests, and stale exact targets reject instead of opening
  another object. Explicit door/bed/stair/lock reasons replace silent failures.
  Solo reconnect retains a safe current position; restart still uses inn/home.
- Rootwater uses its existing lower-east Southern-road mouth (~78% height), now
  with a cave sign, atlas entry detail and entrance-specific prompt/radius. Browser
  entry without unrelated quests worked. Existing territorial combat, sealing,
  party gathering and dungeon rules remain. New scenery hints reuse existing art.
- `hero_skills.py` / `skill_casts.py`: all eight classes have **15 nodes each**:
  six legacy abilities (basic + one special are starters), three genuinely new
  actives, three two-rank modifiers and three passives, with costs/prerequisites.
  Knight and Healer were implemented/verified first; the others have real cast,
  passive and modifier hooks. Cleric retains mixtures/sacred splash/protection;
  Healer has targeted barriers, healing over time and rescue support. New icons,
  class animation strips and sound cues reuse established assets. Barrier pools
  show a small HUD label and steady ring; placed zones use restrained ground rings.
- Finite 20-point milestone ledger: arrival2, road1, inn1, hunter2, bridge2,
  shrine2, alcove1, cave2, floor1=1, floor2=1, tower2, region3. No XP/respawns.
  Basic + Active1 start equipped; Active2 opens on road exploration, Active3 after
  one quest. Up to five combat actions: Hold / Q / R / F / X. Unlocks and equipment
  are separate. Learn/equip/free respec only in Oakvale alive and out of dialogue.
  Respec/swaps keep HP/mana, earned receipts and ability AND slot cooldowns; dismiss
  live summons with normal after-death recharge. First Ultimate equip charges 15s.
  Companions use the same budget and auto-select their tree/loadout when home.
- Additive hero-progress v1 under portable save v2: validate node/cost/prerequisite,
  loadout and relative cooldown records. Older equipped abilities become legacy
  grants, earlier Vitality/Power/Focus stats remain, and unused old credit migrates
  once (old inn credit reconciled with its new milestone). Guild changes refund
  learned-node budget into the new hero while keeping receipts/slot recharge and
  current health fraction. Live-summon restart creates normal 8/15s locks, including
  the action slot. Unsupported data still rejects/preserves originals. No rewriting
  of private saves for tests. Gauntlet save/loadout behavior remains unchanged.
- Adventure has Map / Journal / Skills grouped at top; settings, save management,
  invitations and leave/change actions are under Menu. Health/mana/abilities share
  the bottom HUD. PC arrows remain hidden; mobile arrows/landscape requirement stay.
  Actual 844×390 review caught/fixed E/notice overlap and a 120px dash-button minimum
  overflowing its column. Final maximum-five-action fixture fits; dialogs scroll.
- Final isolated regression results: **300 Python passed, 0 failures/errors/skips**
  (64.853s), **19 client suites passed**, **21 static JS files parsed**, no client
  suite/syntax failures. Includes 10 new control-flow and 8 hero-progression tests.
  Covers old saves/export, point/claim retries, slot recharge/respec, companions,
  all new active casts/modifiers/passive families, roots/ice/walls, input reordering,
  lost-response release, multiplayer/dungeon/gathering/recovery and Gauntlet checks.
  Logs and exact counts are under `reports/ADVENTURE_CONTROL_*`.
- Actual ordinary-stat browser checks: Knight started fresh, learned/cast Shield
  Rush, cleared the road group and Rootwater entrance pack, retreated, reloaded
  and recovered through an isolated server restart with progress/skills intact.
  Learned/equipped/cast Active2 Iron Wall. Distinct fresh Healer had no Knight
  progress, learned/equipped/cast Life Barrier. Main menu/Continue returned to the
  original Knight; Gauntlet Wizard classic loadout/Tester combat worked. Reviewed
  desktop1366×768 and narrow844×390, Skills/Journal/atlas/interior map/settings.
  The maximum-five-slot HUD used helper-completed quests with normal HP, explicitly
  interface evidence rather than earned progression/balance. Fresh final tab had
  no console errors/warnings. No private world actions were used for QA.
- Measured baseline tick mean57.292ms → after50ms. Ordinary road/cave sample input
  ack p95=19ms, dispatch=.3ms, state age47ms; controlled lost-response test stop
  ack=8ms. Render p95=2.2ms. Samples differ in workload and browser scheduling;
  **do not claim a measured FPS improvement**. Final hidden-tab check was heavily
  background-throttled; one observed-release sample=66ms is not a latency percentile
  guarantee. Atomic save p95~39ms/occasional lock holds remain. Human multiplayer,
  physical-phone/network feel and all-eight-hero balance playthroughs are pending.
  Details: `reports/ADVENTURE_CONTROL_VALIDATION_2026-10-14.md`.

Activation: hash-verified **4 private save files** before starting Python:
`data/backups/before-adventure-controls-skills-20261014-085907/`.
The local server is active at `http://127.0.0.1:8000/`, Python
`54fe6a42a4d5` / client `5c869de0289a`. `/healthz`, `/`, and all four new
client routes returned HTTP 200. The hidden background process uses private
`data/runtime/` logs. No private world was opened for activation checks. A
sandboxed health request could not access localhost; its permission-enabled
read-only retry passed. No hosted storage or cloud credentials changed.

## Dungeon maps, new-content sprites and portal animations — 2026-10-13

The Sprites pass is integrated and active locally. Built-in ImageGen produced
seven selected sources: Rootwater and Briarwatch illustrated maps, separate calm
cave/tower floor plates, twelve transparent props, four stone materials and a
sixteen-frame portal effect sheet. `static/dungeon-sprites.js` is loaded before
the Adventure renderer and explicitly served by `server.py`. Runtime exports are
nine PNGs plus two atlas metadata files. Full authoring sources, exact prompts,
fingerprints, reusable exporter and previews are in `art/dungeon-portal/WORKFLOW.md`.

- Dungeon maps retain discovered-node/link gating, with fog, current-party and
  explored/cleared labels and open/sealed passage badges. Existing zoom/Fit/pan
  navigation now reads the SVG aspect ratio and accounts for horizontal centering.
  Larger map viewports improve readability; the card list still scrolls on phones.
- The seven chamber/floor layouts use new floor art and materials on the exact
  server barrier rectangles. Dedicated cave mouths, tower doors, stairs, bells,
  seals, survey markers, closed/spent supply crates and caches replace new-content
  placeholders. Props and decoration do not change collision, AI or shot blocking.
- The village shrine has a dedicated sprite. Portal participants display rune
  charging, a helix, departure streaks in the final 0.52s of the existing 3s channel,
  and a confirmed arrival burst after the server changes their positions. Movement
  or damage interruption dissipates the effects. No gameplay timing changes.
  Reduced motion uses a steady ring. Fresh/reconnected/hidden clients do not replay
  old arrival events. Public portal views add participant IDs, anchor and duration;
  the arrival event uses the existing ephemeral feedback stream, outside saves.
- Definition/asset inventory found no missing PNGs among 26 items, 48 ability
  icons, 3 curses, 8 heroes/4 summons, 9 enemy models, 12 town characters and 15
  combat/puzzle/flight packs. Loading fallbacks remain. Future unopened regions
  are not counted as implemented models.
- The local Python server was restarted on 8000 after a hash-verified backup of
  four private records: `data/backups/before-dungeon-portal-art-20261013-121842/`.
  Static changes need a refresh. The concurrent visibility/movement updates below
  are preserved. No publication performed.
- Syntax parsing and 21 fresh browser artwork fixture renders completed; final
  browser diagnostics were empty. No user-room actions, personal save changes,
  regression suite or ordinary-stat multiplayer dungeon playthrough were run by
  this art pass. `tools/render_dungeon_art.cjs` retains the client art fixture process.

## Hero visibility, continuous movement and dungeon maps — 2026-10-13

Local client pass; no publication or production Python changes by this pass, and
no live-server restart performed here. The concurrently active **Sprites** chat
activated its own dungeon/portal artwork update; the live renderer route was
confirmed HTTP 200 before completion. Refresh now loads both compatible updates.
Private saves, asset cleanup, lazy village loading and collision remain intact.

- `GauntletWorldScenery.renderDepth` cuts back foreground pixels to 28% opacity
  inside overlapping hero bounds. Trees/rocks, village dressing, roofs, portal
  shrines, NPCs, enemies, summons and teammates use explicit bounds/depths; the
  local hero is never faded. The inverse camera transform supplies the canvas
  clipping extent, so labels/animation outside overlap bounds are not cropped.
  Actor labels and combat warnings remain in their existing upper pass. Reuses
  the art; no sprite pack was regenerated or collision weakened.
- User reports movement lag **at all times**. Old exponential reconciliation
  could cancel a normal walking frame when polling errors approached 10–12 pixels.
  `movement.js` caps correction velocity at 25% of walking speed and permits
  500–1000ms of bounded prediction for delayed polls. Normal-stat jitter probes
  verify forward frames, bounded correction speed, position agreement and release;
  existing roots, downing, ice, obstacles and large teleport checks pass. This
  addresses the reproduced correction issue, not a certification of network/FPS
  performance on every device.
- Dungeon diagrams now have independent wheel zoom, +/−/Fit, swipe/scrollbar pan
  and a scrolling card list. At Fit, wheel-down passes through to the list. Per-world
  zoom/pan survive panel updates; disposed controllers release observers/handlers.
  Stable outer-box fit preserves the earlier atlas anti-shake fix. The controller
  is embedded in the already served `adventure.js` (no new Python route/restart).
  Adventure panel signatures are committed after successful rendering, allowing
  retry after an incomplete render. Client render exceptions now log their stack.
- Added real canvas cutback tests (including imported woodland tree art), jitter
  walking tests and dungeon wheel/navigation tests. Final **282 Python passed,
  0 failures/errors/skips**; **19 client suites passed** and all static JS parsed.
  First sandbox Python run: 281 passed, 1 localhost socket-permission error.
  Successful full rerun used the isolated runner with localhost permissions;
  production atomic writes/locks were untouched. Results:
  `reports/CLIENT_FIX_PYTHON_2026-10-13.json`.
- Actual browser review used disposable servers on 8019/8020: ordinary-stat village
  portal overlap, held/released left/right movement, desktop wheel zoom (100→162%),
  Fit, and list scrolling at 844×390 landscape. Fresh final clients showed no console
  errors/warnings. Completed-dungeon map setup used helper-completed encounters;
  it is UI evidence, not ordinary-stat dungeon combat or human multiplayer evidence.
  After the concurrent illustrated-map integration, repeated wheel zoom, Fit,
  scrolling and tower + buttons at 844×390; current SVG viewBox proportions are
  covered by the navigation fixture. Fresh current-art browser tab had no errors.
  Proof PNGs and detailed scope are in `reports/CLIENT_VISIBILITY_2026-10-13.md`.
  Physical-phone and human multiplayer feel checks remain outstanding.
- `tools/adventure_preview.py --scene portal` supplies a disposable central-shrine
  fixture. Its writable `--temp-root` defaults to `.test-tmp/`, rejects private
  `data/` and cleans fixtures on ordinary shutdown. No testing of the user's world.

## Village validation, recovery slots and movement — 2026-10-13

Local implementation only; no GitHub/Render publication. The asset archive and
lazy village image loading below are preserved.

- Investigated the cleanup's 27 Python errors. A reconstructed pre-pass generator
  completed 10,000 deterministic seeds (0–199, then `Random(20261013)` 31-bit
  seeds), with 1,553 rejected road candidates but **no exhausted generator**.
  The exact historical failing seeds/full error trace are unavailable; do not
  claim that the original `Could not generate a connected village` was reproduced.
  A concrete mismatch did exist: accepted building gaps of 180/158 pixels were
  narrower than the router's 184/159 footprint. Placement now matches that width.
  Every accepted village also flood-fills doors, arrivals, villagers and the plaza
  using the authoritative movement footprint, and samples entire road segments.
  Exhausted jitter uses one deterministic authored fallback, validated by the same
  rules, without increasing retries or suppressing errors. Tests exercise forced
  exhaustion at five seeds, all seven layouts, service access and consecutive visits.
- Villages reserve a central portal plaza while buildings/services/roads shuffle.
  Design v2 reconstruction preserves old inn-room/bed IDs, character progress and
  Adventure facts. Old Gauntlet checkpoints also resume safely after a wipe.
  Adventure's **Village portal** recalls to discovered Oakvale, and its central
  shrine returns to the departure area. All connected humans gather/confirm, then
  stand still for three seconds; offline players/companions do not block it.
  Nearby enemies, damage, movement, downing and sealed encounters prevent/cancel
  recall. Travel retains HP, cooldowns and encounter damage/claims; summons dismiss
  with their usual recharge. Gauntlet shrines are scenery; its campaign still uses
  normal travel. The current region has one village, not invented extra destinations.
- Movement prediction now stops during roots/dialogue/Guild locks, smooths latency
  correction and uses frame-independent ice friction matching the server. Save
  success appears briefly; failures stay visible. **Menu → Save files** opens details.
- Each character has three recovery entries: current Adventure, previous confirmed
  Adventure backup, and its latest Gauntlet inn checkpoint. Adventure files remain
  coherent whole-party records in `data/adventures/` and `data/adventure-backups/`.
  The local backup rotates under the existing record lock before confirmed current
  replacement. Backup preview needs the private recovery identity; recovery creates
  a separate world and leaves the original intact. Old files/browser identities
  remain. No rolling cloud-backup activation or durable Render storage is claimed.
- Enemy rendering uses each imported monster's idle/move/release strips and
  charge/heavy/channel anticipation strips. Enemy elemental projectiles override
  reused hero kit labels and retain their element after the owner dies. Offensive
  support casts no longer show healing particles. Existing assets/character art stay.
- `tools/run_tests.py` isolates all test storage (including the imported game
  singleton), checks locked atomic replacement/socket access, temporarily redirects
  TEMP/TMP/TMPDIR, restores settings and removes its disposable fixtures. It refuses
  a temp root inside private `data/`. An early OneDrive-folder run logged intermittent
  WinError 5 replacements; the clean writable non-OneDrive run did not. No atomic
  writes, locks or recovery validation were weakened. Socket tests actually ran.
- Final validation: **282 Python passed, 0 failures, 0 errors, 0 skips** (62.635 s);
  **17 JavaScript suites passed**, all static JS syntax passed. Actual disposable
  browser review checked the portal round trip, brief save notices, backup preview/
  separate-copy recovery, keyboard movement and desktop/844×390 touch-control
  layout, with no browser errors. This is not physical-phone/human multiplayer
  movement or balance certification. See `reports/VALIDATION_2026-10-13.md` and
  `reports/TEST_RESULTS_2026-10-13.json` for commands, limits and evidence.
- Before local activation, hash-verified all three private save JSONs in
  `data/backups/before-village-validation-20261013-112011/`. Restarted the authorized
  local server on port 8000; `/healthz` returned `{"ok":true}`. Live unsaved rooms reset.

## Runtime asset cleanup — 2026-10-13

- Moved 26 unused runtime exports (11,389,589 bytes) from `static/sprites/`
  to `art/unused-runtime-sprites/`: four regions' v1 village buildings,
  interiors, upstairs and unused hunter sheets; original Dragon idle/windup
  PNG/JSON; and ability/item/curse catalog PNG/JSON. Active Draco, adult Dragon,
  individual icons and terrain fallbacks remain. The archive manifest records
  original paths and verified SHA-256 hashes. Full source/art packages retain
  the archive; runtime packages omit it through the existing art exclusion.
- Village images now load once on first use by region and kind, rather than
  eagerly downloading all 28 exports. This removes 12,566,691 bytes of eager
  village requests: 11,067,524 bytes are deferred until needed and 1,499,167
  bytes of never-drawn hunter sheets no longer download. Existing procedural
  fallbacks and load-triggered terrain invalidation remain. No frame-rate or
  measured wall-clock speedup is claimed.
- Deleted 17 regenerable Python cache files (507,896 bytes). Package tooling
  and Git ignore test temporary folders and common cache directories. Saved
  games, backups, art sources, release packages, tests and build tools remain.
- Updated authoring references for the relocated village and ability catalogs.
  See `reports/CLEANUP_2026-10-13.json` and the archive README for details.
- Validation: all 16 JavaScript test suites passed and `static/app.js` syntax
  passed. The 271-test Python run had 27 errors: unchanged village generation
  raises `Could not generate a connected village`, and sandbox permissions
  affect temporary-file replacement/socket binding. The full Python suite is
  **not green in that cleanup run**; those issues were not changed by the asset
  cleanup. See the subsequent investigation and green validation above.
- Refresh clients to use lazy loading. No server code or live rooms changed,
  and no server restart was performed.

## First-chapter quality pass — 2026-10-12 (latest)

Local only; no GitHub/Render publication, purchases or private-save uploads.
`save_portability.py` and `adventure_recovery.py` add portable v2 export/import,
read-only previews, explicit older internal v1 migration and idempotent new-world
confirmation. Exports allow-list progress and omit session/recovery/account IDs,
chat and private telemetry. Validate untrusted sizes/types/IDs/abilities/known
items and dungeon versions; normalize item effects to current definitions.
Unsupported originals stay on disk. Import reconstructs the home village from
its saved seed and verifies the complete public state before committing a file.
The browser caught missing reconstruction during development; this is fixed and
covered by an API-state regression. Restore validates progress before making a
default room, preventing failed loads from becoming default autosaves.

World UUID, creator character UUID and world-bound character UUIDs are independent
of session room codes/hosts. New local records use UUID filenames; existing code
filenames are preserved. RunStorage uses an OS-released per-record lock, atomic
write and revision comparison; a competing/stale writer or unloaded original
cannot be overwritten. Save time/revision advances only after confirmed success.
New sessions use a private recovery proof for state/actions and protected claims;
public player IDs cannot impersonate another new-session character. Legacy
browser identities/checkpoints remain compatible. Menu departure disconnects
Adventure hunters instead of deleting their progression or moving ownership.
Continue displays browser recovery identities, progress, recovery point/storage,
confirmed time/failure and export. File imports choose a character in a separate
world; creators can share private recovery links for their other restored hunters.

Optional `cloud_storage.py` is behind RunStorage, with secret-free `.env.example`
and `migrations/001_adventure_cloud.sql`. No Supabase configuration is present.
Auth is verified through the provider; service-role-only RPCs enforce creator
ownership, world-character membership, CAS revisions and retry receipts. Account
tokens remain in page memory. A public room code cannot claim guest gear. Local
saves remain independent; cloud uploads run off the simulation lock with an exact
retry journal, confirmed status and conflict stopping. Remote recovery joins an
existing active party safely, or restores at home; conflicts/unloaded originals
can be recovered as a separate copy after preview. Public-key configuration
rejects a service-role/secret key in the browser-facing slot. **Cloud contracts
have mocked tests only: SQL execution, Auth setup, server environment credentials
and live ownership/restart/recovery verification are still unconfigured.** Use
existing Supabase Auth accounts/provisioning. Do not claim durable hosted saves.
Free Render filesystem storage remains temporary. No automatic cloud merge or
cross-world equipment transfer exists.

`adventure_rewards.py` offers personal pending choices at the alcove, cave boss,
shrine, tower and finale. Cave: survival supplies; shrine: rescue/ward support;
tower: class weapon/build item; finale: existing legendary armor/weapon usable by
every hero. Journal shows real slot comparisons and already-owned gear; full
pouches explicitly sell/replace an item or sell the reward for shared Runes.
Pending/resolved choices survive travel, wipe/reconnect, disk restart and portable
copies; repeat claims never pay again. Legacy awarded items/claims stay untouched.
Rootwater keeps all geometry/encounters/routes, adding stable survey markings and
short contextual notes. Tower floors explicitly preserve frontline/ranged roles,
stagger initial windups, use deliberate trap-lane compositions and cap summit
guards at two with a short opening. Stable encounter/kill IDs and completed waves
remain; no broad HP/damage/cooldown change. Completion dialogue acknowledges the
woodland, directs unfinished Journal activities, Ashen ridge and portable backup.

Opt-in anonymous `chapter_observations.py` and `tools/chapter_probe.py` capture
ordinary class/gear/resource/cooldown cases. Fixed identifiers/seeds make probes
repeatable. Their one-bend navigation limitation caused a pillar timeout and was
fixed in the probe, not by changing combat. `--ordinary-kit` and `--observations`
on adventure_preview provide a disposable browser setup; `--fast-combat` remains
an explicitly accelerated fixture. Recorded durations/resource deltas, downings,
wipes/revives, consumables, abandonment and reward choices are not player tracking.
The current 78 isolated Medium cases cover all eight solo heroes, two-to-four
hunters and a companion lineup; all cleared. They are not campaign attrition,
alternative-loadout testing or human multiplayer balance proof. See the report
for short-boss/opening-Ultimate observations and the unprepared browser wipes.

Sound changes are limited to quieter/rate-limited Light cues and low-priority
ducking around boss warnings and completed revives. No sound bank/props/atlas were
rebuilt. Visual/reduced-motion warnings remain. Listening tools were unavailable;
README lists a reproducible cue/combat listening checklist. Do not certify comfort
from playback or metrics. Human co-op, physical phones and listening remain open.

Validation: **271 Python tests**, **15 JavaScript suites**, normal-stat repeatability
checks and **78 ordinary-stat isolated probes**. Actual browser: cave entrance and
gallery combat, optional alcove/choice, wipe survival, export → preview → new-world
import → playable village → travel; tower floor-one wave and wipe recovery;
desktop and 844×390 landscape Continue/HUD, portrait gate, return to landscape;
no final browser diagnostics. The original user's world was never a fixture.
See `reports/CHAPTER_QUALITY_VALIDATION_2026-10-12.md`. Private saves were copied
and hash-verified before activation with `tools/backup_saves.py`; latest backup
location is recorded in the validation report. Local server serves port 8000;
client changes require refresh. SQL/live cloud activation remains separate work.
Final verified private backup: `data/backups/before-chapter-quality-final-20261012-190332/`
(3 JSON files). Final port-8000 health returned `ok:true`; no restore errors.

## Finite Adventure dungeons and stable map — 2026-10-12

Local implementation; no GitHub/Render publication. New `dungeons.py` owns
authored layouts, the additive versioned state, fixed encounter IDs and an
explicit `GameWorld._spawn_wave` adapter. It reuses the combat/warning/role tools
but bypasses Gauntlet campaign schedules, chest, pressure and victory logic.
Do not route Adventure dungeon floors through campaign stage advancement.

Rootwater passage: Southern road east (lower trail) → cave_entry → cave_gallery
→ cave_heart → clearing west (lower trail), with cave_cache north of the gallery.
Four compact chambers have permanent stone rectangles, safe arrivals, three
ordinary packs, entrance supplies and a Surveyor treasure/story branch. Ordinary
exits remain open with enemies alive. Gathering at the den seal starts the
Rootwater Cave Troll with cover manipulation and seals exits until victory.

Briarwatch tower: camp east → tower_1 → tower_2 → tower_3 → bridge east bank.
Each early floor has two waves; the summit has a Minotaur Captain and guards.
Floor 2 uses two existing warning traps and two lanes. Bell activation gathers
connected living humans, waves use a three-second sealed break, and cleared
floors wait for manual party travel. Retreat is allowed before a floor starts
and after it clears, through previous floors to camp. Final victory opens both
ends permanently. Returning does not regenerate enemies, rewards or the boss.
The tower uses a separate east-bank trail from camp and never repairs the river.
Ordinary cave formations leave the full four-player arrival spread outside
aggro range. Tower waves use fixed alternate anchors when hunters, bodies or
summons occupy a default spawn point. Composition and reward IDs stay stable.

`adventure.py` accepts all seven dungeon area IDs in discovery/save/restore,
travel, danger and tracking. Exterior/interior routes have reciprocal directions
and distinct exterior arrivals. Existing eight-area indices/layout seeds stay
stable. Interior progress has separate schematic maps rather than crowding the
woodland atlas; known dungeon entrances and unlocked routes have outdoor pins.
Journal supports one tracked dungeon or woodland goal. HUD shows floor/wave,
sealed/open status and short nearby prompts. Completed entrances gain a steady
green pennant; NPC feedback names reopened routes. Woodland completion reveals
the Ashen ridge story lead, with no additional biome implemented.

Permanent collision rectangles match the visible stonework and client prediction.
The camp tent's sides/back and ruins columns also have stable frame-zero footprints,
derived into old cached areas without changing quests or enemy health. Tent/arch
openings stay usable; the ruins trail now approaches the center of its arch.
LOS, projectiles, splash, boss marks and support healing cannot pass through
dungeon walls; charges stop safely at permanent stone instead of trying to damage
it as breakable cover. Dungeons omit tall cosmetic foreground props to retain
actor silhouettes. Native cavern/ruins ground and authored paths are reused.
Existing following cameras, outdoor territories, animation restraint, pixel UI,
landscape gate, personal equipment and shared Runes remain.

Persistence: existing Adventure outer format v1 now contains `dungeons` records
with version/id/type, entrances, visited rooms, completed encounter/wave keys,
floors, treasures, boss/route facts and an optional active attempt. Old records
without this section extend on load; unsupported records remain on disk with a
logged error. Claimed loot and enemy Rune IDs are retained across retries. An
interrupted sealed encounter drops partial bodies and resets its authored arena,
then restarts the first unfinished wave in full when the bell/seal is activated.
Completed waves/floors remain cleared. Restart/wipe returns to the existing
inn/home checkpoint; a wipe applies its 40% loss once. Travel does not heal or
reset abilities/dash; remaining recharge also saves, including the normal death
recharge of a dismissed live summon. Companions occupy one of four existing
party slots; offline/bot members do not block gathering. No humans means no
simulation or companion-only completion. Free Render storage remains temporary.

The atlas jitter was a ResizeObserver/scrollbar feedback loop. Fit now uses a
stable outer viewport box with a scrollbar reserve, writes only changed sizes,
and preserves zoom/pan on ordinary updates. The client regression models the
narrow scrollbar threshold and checks repeated callbacks, zoom centering and Fit.

Validation: 245 Python tests and all 15 client test files passed; static JS syntax
parsed. Seventeen focused dungeon tests cover entry/retreat, finite floors, 1–4
party scaling, companion gathering/pause, reconnect/host change, wall/shot/AoE/
summon/charge behavior, conservative recharge, one-time rewards, old saves and
interrupted/completed restart recovery. Actual isolated browser play traversed
the cave branch, claimed both caches, fought the troll, emerged in the clearing
and revisited its completed den; all tower floors were fought, floor 2 was
abandoned before activation, and the completed summit route was traversed to
the still-broken bridge and back. Desktop and 844×390 landscape review included
maps, journal tracking, warning traps and boss cues; browser diagnostics were
empty. These high-HP/damage flow fixtures are not human balance/physical-phone
tests. Details: `reports/DUNGEON_VALIDATION_2026-10-12.md`.

Disposable browser fixtures are `tools/adventure_preview.py --scene cave|tower
--fast-combat` (with optional `--touch-controls`); `dungeons-complete` prepares
a finished world for visual review. All use temporary saves. Never test by
moving the user's saved adventure. Private saves must be backed up with
`tools/backup_saves.py` before a necessary local restart.

Final local activation: three private save files were copied and SHA-256 verified
in `data/backups/before-adventure-dungeons-final-20261012-164926/`. The updated
server is running at `http://127.0.0.1:8000/`; its health endpoint returns success.
Disposable QA servers/tabs were closed. Refresh the client for the new UI;
use the usual browser identity/room recovery flow.

## Bxfr audio and confirmed combat feedback — 2026-10-11

Local implementation only; no publication/deployment. The retained Bfxr DSP and
licenses remain hash-identical. `art/audio/sounds.json` now has 95 seeded,
explicit recipes: distinct class Light/Special/Ultimate/impact families,
three Light variants, elemental summons/frost, danger/rescue, materials,
transactions/objectives and quiet accents. Runtime WAVs total 1,612,618 bytes,
52.7–590.3 ms, maximum peak 0.47998, no clipping or nonzero endpoint samples.
`build-sounds.cjs` protects changed/unregistered exports and supports declared
manual WAV/editor data; `--replace-modified` backs up intentional replacements.
Routine rebuild: `node art/audio/build-sounds.cjs`,
`node art/audio/build-preview.cjs`, `python tools/audio_inventory.py`.

New `feedback.py` maintains an ephemeral 128-event / three-second stream with
scene epochs, increasing IDs and relative ages. Casts emit only after acceptance;
actual hits, damage, summons, healing/ward resolutions, down/revive, dash,
equipment/purchases/chest outcomes and objectives use confirmed sources.
Windup/recovery transitions are sampled at the existing server tick. Dungeon
starts, waves, completion and live travel are covered; completion rewards no
longer emit duplicate completion cues. Checkpoints exclude this stream.

`static/audio.js` consumes IDs once, silently baselines first load, scene changes,
refresh, reconnect gaps and hidden returns, and never queues failed/locked audio
for later playback. Scene identity includes Adventure/dungeon location and
interiors. The listener uses local hero world coordinates, independent of zoom;
quadratic falloff reaches silence at 800 units. Tiered 6/8/10 voice limits,
gentle panning, compressor and pack/summon rate buckets protect useful cues.
Replacement voices start after the evicted voice's fade.

Atmosphere uses a separate 16% bus, quiet filtered procedural beds and sparse
accents for village, woodland, chambers, tower and boss spaces. A maximum of two
bed sources crossfades; obsolete sources stop on mute/reset/hide. There is no
realistic environmental audio or complete music soundtrack. Effects default to
45%; old volume/mute settings migrate. Settings add cue previews, master mute,
ambience volume, Off/Reduced/Normal shake and reduced decoration. Device reduced
motion disables optional shake and reduces particles, preserving essential
warnings and labels. New `static/feedback.js` has small confirmed impact/heal/
ward/rarity/completion marks; choreography shares a particle budget. Existing
stable scenery and combat/movement rules are preserved.

Audit/all 48 ability mappings: `art/audio/EVENT_INVENTORY.md` and
`event-manifest.json`. Rebuild/manual-export instructions: `WORKFLOW.md`.
Local listening artifact: `art/audio/preview.html` and `mixed-combat.wav`.
The 12-second mix is an authored reference using actual exports at approximate
pre-compressor gains, not a recorded multiplayer session. **Actual listening is
still outstanding**: this agent can verify browser playback but cannot hear it.
Headphones, speakers, Bluetooth and physical-phone policies/performance need
human review. Perceptual comfort is not certified from metrics.

Checks/reports: `reports/AUDIO_VALIDATION_2026-10-11.md`, audio test transcripts,
and `AUDIO_MULTIPLAYER_2026-10-11.json`. Final checks passed all 243 Python tests
and all 15 client test files. Disposable QA helper:
`python tools/audio_preview.py --players 4 --port 8013 --touch-controls` (or one
player on 8014); it uses temporary saves and ordinary stats. Broader existing
HTTP probes use explicitly synthetic high-HP reliability fixtures. Desktop and
844×390 landscape browser checks are simulated, not physical-device listening.
One dungeon regression fixture now supplies its camp source when entering the
tower directly, so its tracking test has discovered the required entrance.

Three private save records were hash-verified in
`data/backups/before-audio-feedback-20261011-123233` before starting the updated
local server on port 8000. Python changes require restart; client/audio changes
require refresh. Preserve `data/` and the audio authoring sources on transfer.

## Villages matched to the new world artwork — 2026-10-11

The user requested villages matching the richer new world design. Woodland,
ruins, cavern and frost now have replacement ImageGen building and interior
atlases, matching upstairs materials, and a new regional gate/well/lantern/garden
atlas. Six service buildings per region retain six roof color variants (144
sprites). All 24 room interiors have open central service/door approaches.
Upstairs floor/wall materials use the new inn art on the existing three-room
plan; regional bed, door and stair sprites remain from the established packs.

Village floors share the new world ground. Rounded, softly edged paths follow
the existing server-generated townPaths. Seeded trees use the new world scenery,
with extra understory, planting islands, gardens, lamps and common wells. Dressing
respects building/door routes, the south party arrival and Adventure story NPCs.
All seven village layouts remain supported. Scenery is cosmetic and adds no
collision, concealment or enemy detection behavior.

The client now sorts village buildings, foliage, villagers, heroes, gate and
runner by depth. Adventure Oakvale story NPCs join that pass, while travel/vote
cues and player names stay readable. Backend layout, services, training, guest
occupancy, door/bed targets and save behavior are retained. Runtime changes are
in existing static/app.js, town-sprites.js and adventure.js; thirteen v2 PNGs are
under static/sprites/. Refresh the browser to receive these changes.

Retained generated sources, nine exact built-in ImageGen prompts, crop/export
manifest, fingerprints and PowerShell rebuilds are in art/village-redesign/.
See WORKFLOW.md and preview.html. Keep this ignored authoring folder on transfer.
tools/render_village_art.cjs captures actual-client local fixtures without
creating rooms/actions/saves: all four themes in seven layouts, all 24 interiors,
four upstairs rooms, canopy overlap examples and Adventure home/celebration.
Final browser rendering diagnostics were empty; JavaScript syntax parsed.
Gameplay regression suites were not requested or run for this artwork change.

The local server was stopped when the task resumed. Three existing private save
files were copied and hash-verified into
data/backups/before-village-art-20261011-111919/ before starting it. The server is
running at the README HTTP address. No Python change or save migration was needed.

## Pixel interface and illustrated woodland atlas — 2026-10-10

The user requested a complete pixel-game UI redesign and a more appealing game
map. The existing browser UI now shares slate/brass pixel frames, stepped button
highlights, hard shadows and an original locally embedded 5×7 display face.
Entry/lobby, hero cards and loadouts, HUD/party/chat, pouch/equipment, merchant,
training, dialogue, journal, settings and stats use this theme. Longer copy uses
a readable system sans face. Larger HUDs show the current hero's portrait.
Literal ability icons retain their circular red recharge and glowing green
ready state. Loadout and Guild ability titles are no longer accidentally
overwritten when their icon/description elements are populated.

Adventure's Map is now a woodland atlas with a built-in ImageGen terrain image,
river, woods and ridges. The client overlays the server's known locations and
actual connections as winding dirt trails, using existing landmark sprites.
Stepped fog covers uncharted territories; charting all eight reveals the full
illustration. Unknown landmarks/connections are never drawn. Bridge/shrine icons
and names still reflect completion. Selected landmarks show a detail panel and
known connected trails. Party/goal focus, 1×–2.5× zoom, Fit and scroll/swipe pan are
local view controls; selecting a landmark does not travel the party. The graph's
exit directions remain authoritative; illustrated distances are approximate.
Short landscape phones open their first map view zoomed around the party.

Implementation is in the existing `static/style.css`, `index.html`, `app.js` and
`adventure.js`. Terrain is `static/sprites/ui-woodland-atlas-v1.png`. This pass only
needs a browser refresh. No server change/restart or save migration was needed.
It is local; no remote publication was requested.

Retained sources, exact ImageGen prompt, original bitmap-font builder, theme,
rebuild script, fingerprints and visual previews: `art/pixel-ui/WORKFLOW.md` and
`art/pixel-ui/preview.html`. Keep this ignored authoring folder when transferring
the project. `tools/render_ui_art.cjs` renders the actual client using isolated
fixture data without creating rooms/actions/saves. Artwork was reviewed at
1280×800, 844×390 and 667×375, with full/repaired/partially charted maps and major
menus. Browser rendering diagnostics were clean. This was an artwork review;
gameplay regression suites were not run for this UI request.

## Distributed woodland encounters — 2026-10-10

Adventure's large road/crossroads/clearing now each have three separate authored
territories (four ordinary enemies solo), spread near different trails/landmarks.
Camp has two territories (three solo guards); bridge has two (two solo spiders).
Co-op adds one enemy per extra active party member across the area's territories,
with the bridge's extras confined to its roomy northern bank. Location damage,
health scaling, bounded pursuit, open ordinary exits and no respawns remain.
Seeded pack positions leave every four-player arrival clear and avoid cover/water.
Home, shrine/boss encounters, camera, mobile landscape and Gauntlet are unchanged.

Cached areas carry additive `encounterLayout: 2`. Surviving enemies in an old large
area spread into separate territories once on entry, retaining IDs, damage/HP,
roles and kill/reward facts. No enemies are added to an already visited area;
cleared areas stay empty. Original compact saves keep their existing coordinates.
Revisits and restart preserve the new positions. Quests still require clearing the
camp/hunter guards; bridge repair and ordinary travel remain usable with mobs alive.

Validation: 223 Python tests passed, including five new spatial/persistence tests.
Four-player spawns were checked across 80 seeds in all five ordinary encounter
areas. Actual disposable browser review showed the three road territories in room
overview, local engagement and retreat; no console errors/warnings. This is agent
review and automated co-op coverage, not human multiplayer balance testing.
Local activation is on port 8000 with healthy `/healthz`. Three private save files
were copied/hash-verified in `data/backups/before-scattered-encounters-20261010-222726/`
before restart. `tools/backup_saves.py --label update` provides this verified backup
workflow for future local restarts. No GitHub/Render publication occurred.

## Woodland review, physical bridge and exploration feedback — 2026-10-10

Local implementation only. This section supersedes older descriptions of fixed
Sage Wand/Moonsteel rewards, signpost interaction and the decorative bridge.
Python authority/browser architecture, Gauntlet, Adventure v1 state, cached area
sizes, camera and landscape requirement remain. Tests use disposable storage;
the user's current Adventure and checkpoints were not used or reset for testing.

`stamp` is static by default; NPC loops opt in. Frame inspection found mismatched
bridge/tent/fire silhouettes, so stable base frames and clipped/code overlays
replace cycling whole environmental frames. Water/flame highlights, rare embers
and shrine glow have independent phases; reduced-motion suppresses decoration
without suppressing characters or combat warnings. Timber, ropes, stone banks,
tent poles, bench/logs and campfire stones remain fixed. Exit waystones remain
steady with static nearby/selected emphasis. Campfire is at (400,305), with
scenery reservations and authored side paths kept clear. Available discovery
artwork supplies wagon, leaf marker, burned watch and moss cache landmarks.

The area graph keeps its IDs/connections, but camp is south of crossroads and
east of bridge. All exit/reverse edges now agree; duplicate south crossroads
and north shrine trails have distinct horizontal offsets and source-aware safe
arrivals. Map curves leave/enter the actual exit edges. It is explicitly a
schematic route map, with a bending crossroads–shrine connection. Authored
paths replace center spokes, blend into terrain and continue through boundaries.
Far destination labels are quieter; nearby prompts explain closure requirements.

`BRIDGE_LAYOUT` drives artwork plus permanent rectangular terrain barriers in
`combat_environment`; client movement prediction consumes those same public
barriers. River crosses the full room; only repair opens its (235..285) span.
East entry from camp/workbench and south ruins trail stay on the east bank;
the north Southern road shortcut is on the west bank. Dash and swept AI detours
cannot bypass water. Summons at blocked spawn offsets fall back to their owner's
safe ground. On entry/repair, barriers derive from the persistent bridge fact,
including older cached v1 areas. Restored names update heading/map/destinations.

Signpost features are excluded from actionable proximity. Connected living
humans within 120 units receive a passive direction board; tick reveals named
trails once and saves only when discovery changes. Offline humans/bots do not
read it; it closes on departure/interior/puzzle. It creates no dialogue or lock.
The left/right southern branches are distinguished explicitly.

Personal `trackedObjective` is an additive saved field, changed by validated
`adventureTrack`. Known-location BFS recommends usable routes and avoids the
locked shortcut. Journal separates active/completed/unrevealed goals, has a
map star/next-exit highlight, and moves save explanations into a disclosure.
The unrevealed ruins list remaining hunter/bridge/shrine requirements. All three
stay available in any order. Runner/hunter/watch connect the dragon's earlier
attack to the awakened Minotaur, without claiming a dragon fight in this region.

Optional `cache` at road (175,355) pays 12 Runes + Healing Draught per hero;
`watch` at clearing (700,365) pays 8 + Mana Draught. Coordinates scale with cached
area size. `discovery:*` claimed IDs survive travel/retry/reconnect/save recovery;
cache disappears after claiming, watch remains readable. Their journal entries
are hidden until found. They do not mutate mandatory quests or respawn enemies.

Shrine rewards use `CLASS_WEAPONS`; final rewards are Moonsteel Sword (Knight),
Arcane Conductor (Wizard/Archer), Pursuit Blade (Rogue), Summoner's Staff (Druid),
Dragonbone Armor (Cleric/Bard/Healer). Reward history records recipients, item
names and full-pouch sale conversions; previously claimed rewards are preserved.
Short arrival/world-change notices use bounded saved notification history.
Travel readiness enumerates connected humans still gathering/confirming or
blocked by dialogue/downing; offline players and companions remain excluded.
Existing recovered hunter, restored altar/new plants, removed poison and village
celebration remain visible consequences. Short landscape dialogue layout now
fits narrow devices while keeping the established left/right arrangement.

Validation: 218 Python regressions; 12 JS suites; all static JS syntax checks.
Eleven new server regressions cover passive signs, topology, safe arrivals,
water/dash/detours/summon spawns, additive old-cache migration, tracking/recovery,
one-time optional finds, all hero rewards/full pouches, gathering/disconnect/
reconnect and repaired bridge/restored shrine persistence. Actual canvas pixel
comparisons verify fixed props and localized/reduced decoration. An old damage
test was made deterministic by holding animation wall time while comparing
damage tint; character rendering was not changed for that correction.
Four-client 20s HTTP check: 2,290 requests, no captured errors, healthy ticks,
p95 18.2ms, max tick 2.01ms. Browser fixtures reviewed 1280×800, 844×390, 667×375:
sign dismissal/tracking/map, broken crossing, workbench repair and actual crossing,
campfire/tent over time, both optional finds, receipts/journal, narrow dialogue
and landscape touch UI. Human multiplayer and physical phones still need tests;
synthetic reliability results do not establish balance. Detailed evidence is in
`reports/ADVENTURE_REVIEW_VALIDATION_2026-10-10.md` and its HTTP JSON.

All three private save files were copied and SHA-256 verified in
`data/backups/before-adventure-review-20261010-220652/` before activation. Preserve
these private records; their originals still match after the local restart and
`/healthz` is OK on port 8000. Browser travel to Southern road and back retained
the repaired crossing and restored heading. Current Render free storage remains temporary. Earlier
validation sections below are historical, and other concurrent art edits are
preserved rather than replaced by this pass.

## Open-world artwork and richer regional scenery — 2026-10-10

Local art/client integration only; no GitHub or Render publication. The current
Adventure definitions and drawing paths were audited for new placeholders.
Four transparent world packs supply 100 prop/NPC source phases, including
bridge states, altar states, tent, furniture, fire, supply chests, clues,
waystones, a unique courier and seated/recovered hunter. Four further unique
landmarks cover the broken wagon, leaf waymarker, scorched watch and moss cache.
The four newer equipment keys now have their own 64×64 icons, and map/journal
markers use actual landmark thumbnails. Existing matching village interiors,
combat cover/effects, heroes and ordinary enemies are reused.

The shrine Guardian has a new carved gray stone/moss/rune body, separate from
the Cave Troll and druid golem. Two 96×96-cell sheets contain idle/move/release
and charge/slam/rock-channel actions in eight directions: five generated views
plus deterministic NE/E/SE mirrors. Selection uses only `shrine-guardian`; its
combat kind, damage and authoritative timing are unchanged. NPC pose loops
play. Fixed structures stay still; water highlights and fire/embers animate
within their fixed silhouettes, with reduced-motion support.

The user's added area request replaces the small repeated central texture and
edge-strip extension with four calmer 512×512 regional ground materials and
sixteen foreground objects. `static/world-scenery.js` caches mirrored macro
tiles at native pixel scale and soft route edges. It uses Adventure's current
authored meandering routes, distinct location palette treatments and deterministic
border/interior scenery clusters; larger fields contain more interior islands.
Woodland uses oak/birch/ferns/logs; ruins use ivy arches/columns/flower ivy/masonry;
cavern uses stalagmites/mushrooms/crystals/shale; frost uses snow pines/birches/
shrubs/ice arches. Village ground uses these materials under existing town paths.

Cosmetic objects never enter Python collision, enemy vision, line-of-sight or
projectile blocking. Existing physical river barriers and destructible cover
keep their server behavior. Actual routes, exits, objectives, interaction
landmarks, river and rune apparatus are kept clear. `app.js` sorts scenery,
enemy bodies, summons and heroes by feet, allowing characters to walk under
canopies/overhead structures. Health/player labels, attack warnings and ultimate
effects draw above this layer. Original terrain is retained as a loading fallback.
Both `world-scenery.js` and the new art/flight modules are in the server whitelist.

The prior projectile/readiness request is also completed: 23 dedicated flight
designs × four frames, real basic/snare/large Deadeye arrows, actual descending
Rain of Arrows, tumbling flasks, literal frost/thorns and animated affinity bolts.
`static/projectile-animations.js` rotates to actual velocity and keeps shot age
across polls. HUD icons remain in recharge/menu UI. Readiness CSS now gives
usable Light/Special/Ultimate icons a green contour and ring; cooldown, mana,
active summon and downed guards remain authoritative. The focused projectile
checks and actual CSS fixture at 1280/390 widths passed. Full live Adventure/
human multiplayer playthroughs were not run for this art pass.

Built-in ImageGen was used. New sources, exact prompts, native nearest-neighbor
exporters, crop/mirror/hash manifests and animated authoring previews are retained
locally in `art/adventure-sprites/` and `art/projectile-animations/`. See their
`WORKFLOW.md` files and the Adventure `AUDIT.md`. Run
`pwsh -NoProfile -File art/adventure-sprites/build-all.ps1` for the complete world
export. `node tools/preview_sprite_art.cjs --art-only` exports authoring previews
without creating rooms/saves. These new ignored authoring folders should be
preserved explicitly when moving editable artwork between machines. They are
not in the older October 8 backup archive. Static updates require a browser
refresh; newly whitelisted scripts require the authorized server restart.

Local activation: checkpoint CEVKC/UTAE4 and the current Adventure record were
copied and SHA-256 verified in `data/backups/before-world-sprites-20261010-220403/`
before replacing the identified port-8000 server. `/healthz`, both scenery
modules, the flight module and new runtime PNGs returned HTTP 200 afterward.
Modified JavaScript and Python syntax parsed successfully. Live in-memory rooms
reset on that restart; existing on-disk saves were retained.
The actual game renderer was also visually inspected with client-only area and
Guardian fixtures; no room/action APIs were used. That review caught a canopy
overlapping the boss arena. Placement now reserves full object height as well
as its foot position; the final Guardian preview leaves the fighting space clear.

## Selected larger areas, following camera and mobile landscape — 2026-10-10

Local update only; no GitHub/Render publication. The user clarified that only
some rooms should become larger, and mobile gameplay should require horizontal
orientation. Newly created road, crossroads and clearing areas use 1800×900,
1920×1080 and 1440×900 respectively. The village, camp, shrine, bridge, ruins,
interiors and puzzle rooms remain 960×540. Area state now carries `size` inside
the compatible Adventure v1 record; cached older areas without it retain
960×540, without relocating saved enemies/objectives. Unvisited areas can use
the new size. New adventures receive the full expanded set.

`combat_environment.dimensions` supplies server movement, role AI, companion
dodge/detours, summon spawn and projectile bounds. Adventure exits/entries,
groups and features use the actual area size. Leash radii, combat ranges, damage
and difficulty are unchanged. Public snapshots include `areaSize`; movement
prediction agrees with those bounds. `static/camera.js` keeps a browser-local
view transform, follows the predicted local hero, clamps at field edges and
preserves equal X/Y scaling. Native-size terrain/edge strips extend woodland
art. Cached backdrop keys include area IDs and sizes. Target clicks and enemy
pings use the same camera projection, including while zoomed out.

In large fields, hold V or hold Area view for full-field overview; release returns
to following. A short button tap previews for three seconds. Focus loss, travel,
interiors and puzzles clear it. Compact rooms remain fully visible without a
camera button. The canvas follows its CSS dimensions, removing the old unequal
axis stretch. Mobile/touch-first devices must play in landscape; portrait has
an opaque rotation prompt and makes the gameplay UI inert. Movement/held
attack/revive/overview inputs release immediately; polling and the shared game
continue. The lobby stays usable in portrait. Rotation back restores controls
without stale input. Touch-capable mouse desktops do not get the phone gate.
Short landscape layouts reposition Area view away from the touch pad and retain
44px touch controls. No orientation/fullscreen permission request is needed.

Validation: 207 Python tests (six new area-size regressions) and ten JavaScript
suites passed. `tests/test_area_sizes.py` verifies large movement/dash, role AI,
summons/projectiles beyond old bounds, travel/gather/reconnect, revisits/sizes,
save recovery and compact old-cache/Gauntlet/puzzle behavior. Camera tests cover
follow/clamp, round-trip target projection, hold/tap expiry, pointer identity,
scene reset and aspect ratio; landscape tests verify input release/UI blocking,
rotation recovery and mouse/lobby exemptions. Four-client HTTP fixtures handled
2,450 requests over 20s; all four moved outside old bounds, errors were empty,
health stayed good, localhost p95 15.97ms and longest tick 1.24ms.
See `reports/AREA_CAMERA_MULTIPLAYER_2026-10-10.json` and the validation markdown.
Browser QA used disposable road fixtures, desktop 1280×800, portrait 390×844 and
landscape 844×390 / 667×375. It checked held touch movement, timed/held overview,
target selection/pings in a panned field, the portrait-only prompt, returning to
landscape, and compact Oakvale after a fixture wipe. Console checks were empty.
Fixture touch exposure does not claim physical hardware emulation; human co-op,
physical phones and encounter-density tuning in the bigger fields need playtests.

Before local activation both original private checkpoint files were copied and
SHA-256 verified in `data/backups/before-area-camera-20261010-201552/`.
Private saves remain excluded from reports/releases; normal local activation
serves the update on port 8000. Previous prototype validation below is historical.

## First playable Adventure woodland region — 2026-10-10

This is a **local implementation only**, as explicitly requested. Do not publish
or deploy it without a separate user instruction. The hosted build described
below remains the October 9 release. The Python authoritative server/browser
architecture is preserved, and Gauntlet remains the default selectable mode.
Old Gauntlet saves remain separate and compatible.

Create a party, select Adventure in the host's Mode selector, choose three
abilities and Begin Adventure. Challenge and the optional companion work; the
Gauntlet run-length selector is hidden. Oakvale reuses the shuffled woodland
village, shops, inn, Guild, interiors and beds. Its layout stays stable for this
Adventure. The first runner dialogue gives the immediate missing-hunter objective;
there is no mandatory first-village exit tutorial gate in Adventure.

`adventure.py` owns explicit IDs, connections/entry points, area cache, territorial
groups, quests, travel, rewards, recovery and save/view records. Areas: home,
road, crossroads, camp, clearing, shrine, bridge, ruins. All links are bidirectional.
Road/crossroads/camp/bridge form a loop after bridge repair; crossroads/clearing/
shrine provide a second loop. The bridge opens a direct road shortcut. The old
ruins unlock after hunter, bridge and shrine completion; their existing Minotaur
King is the region's final fight. Completion shows dialogue and village
celebration without ending exploration.

Ordinary groups are placed once and persist defeated; enemy HP/environment state
is captured on saves/travel. Enemies engage nearby intruders or attackers inside
their leash, then return home without healing. Exits stay available during outdoor
combat and the unsolved shrine puzzle. Guardian awakening explicitly seals exits.
No compulsory waves, route pressure, town-visit pressure or accumulating stage
scaling operate in Adventure. Location danger and chosen challenge govern combat;
initial group/boss creation scales to the present party, including the companion.
Summons are dismissed on area changes, while recharges otherwise carry across
travel. Companion AI follows and fights engaged groups without voting/solving.

Connected humans must physically gather and each confirm E/Interact at the same
trail; offline players and bots do not count. Walking away clears confirmation.
Presence updates release a pending exit even in the puzzle phase after a human
disconnects. Reconnecting heroes join the party's current area, clear stale
interiors and use safe arrival positions. The first reconnect after disk recovery
keeps the saved upstairs bed placement. Cached quest NPC positions avoid shuffled
buildings and the gate courtyard; accessibility was checked across 80 villages.

Hunter: read tracks/sign, defeat clearing wolves and finish the hunter dialogue;
the recovered hunter appears in Oakvale. Camp guards protect a shared repair-kit
chest; the bridge workbench repairs boards and unlocks the shortcut. Shrine:
existing solo or connected-human clue exchange puzzle, then a Stone Guardian;
completion changes the altar and removes poison. Final ruins guardian completes
the region. Ledger entries cover every enemy and reward, with one-time shared
Rune/personal equipment or consumable rewards. Full pouches receive sale value.
No new classes, crafting, survival or large skill tree were added.

Persistence: separate **version 1** Adventure documents in
`data/adventures/CODE.json`; old Gauntlet v1 remains `data/checkpoints/CODE.json`.
`RunStorage.save_adventure/load_adventures/delete_adventure` is an atomic local
backend interface suitable for a later durable provider. World discovery, areas,
quest/reward/kill facts, bridge/boss completion, Runes, personal gear/loadout,
class-change/training progress and overall statistics are saved after mutations
and completed revives. Companion consumable use saves immediately too, even
though its AI uses the internal action path. Unsupported records are preserved/logged; write failures
produce a visible warning. Runtime clocks, HP/mana, positions, buffs, summons and
unfinished puzzle attempts are not resumed. Restart recovers at the party's last
upstairs inn bed, or Oakvale's gate if none was chosen. Beds choose recovery and
heal; innkeeper dialogue only teaches existing training. A wipe keeps completed
world objectives/items/routes, resets an unfinished guardian, restores at the
recovery point and loses 40% of shared Runes once. Consumption/spending remains
part of saved progression. Preserve all private data during transfers/restarts.
Free Render storage is temporary; durable online saving was not implemented.

Client: `static/adventure.js` integrates the location heading, compact Journal,
discovered SVG map with known quest markers, trail prompts and landmark/world
consequence rendering. Map labels retain readable size with horizontal panning
at phone width. `movement.js` uses the area ID in its scene identity to prevent
cross-area interpolation. Guide and leave/save text distinguish the two modes.
Map/Journal sit above the desktop title hitbox; teammate HUD sits below them.
The existing E/touch interaction and combat/revive/attack/dash controls are reused.
An unrelated lobby reliability issue found in browser QA was fixed with the
atomic `chooseAbility` action, so fast category clicks cannot overwrite another
choice using a stale snapshot. Legacy `loadout` remains supported.

Validation: **201 Python tests passed**, including **29 Adventure tests**.
Validation uses disposable saves and parties. `tests/test_adventure.py` covers
the full route in solo+companion and three-human parties, revisits, gathering,
offline/companion rules, puzzle disconnects, correct reconnect area, territory,
fixed danger, one-time rewards (including after restart), world changes, equipment
and revive persistence, save errors/versions, bed recovery, unfinished bosses,
wipe penalties and old-save coexistence. Enemy roles are assigned when an area
is built, then retained across revisits, so a defeated support cannot be replaced
by changing another enemy's role. Restoration installs a room only after all
placement/validation succeeds; corrupt records leave no partial room behind.
The full-route tests use authored
positions/defeats and do not establish balance. Two older Gauntlet navigation
tests were stabilized to stop at arrival instead of simulating random combat
long enough to clear the destination stage.

The latest four-client Adventure probe performed 3,442 HTTP requests in 30 seconds,
kept all four clients moving, captured no simulation errors and stayed healthy;
p95 localhost response was 18.78 ms, longest tick 1.44 ms. See
`reports/ADVENTURE_MULTIPLAYER_2026-10-10.json`. Extra HP isolates reliability;
these are automated local fixtures, not human/hosted/physical-phone tests.
Browser QA covered ordinary creation/onboarding/travel/clues plus an actual solo
shrine puzzle and held-attack guardian kill. Completed-world fixture views checked
the recovered NPC, restored routes, final map/journal and continued exploration.
1280×800 desktop and 390×844 narrow layouts were checked, including held pad
movement, tap travel, journal and map panning. `tools/adventure_preview.py` makes
only temporary saves; its `--touch-controls` option exposes the existing pad for
narrow QA without claiming hardware touch emulation. Browser console checks had
no runtime errors. All eight JavaScript regression scripts and static JS syntax
checks passed. Human multiplayer, physical phones, long-run balance and portrait
camera/aspect comfort remain to be evaluated; the inherited portrait renderer
can stretch artwork. No extra hosted services or credentials were requested.

The local server was restarted with this update and is serving the Adventure
selector/script at http://127.0.0.1:8000 with healthy simulation ticks. Before
restart, both existing private Gauntlet checkpoint JSON files were copied to
`data/backups/before-adventure-20261010-171230/`. SHA-256 matches were verified
before restart and the originals still matched afterward. Disposable preview
servers/tabs were closed and the normal browser viewport restored. Live memory
rooms reset on restart; real saved games were preserved. No GitHub/Render actions
were performed for this update.


## Hosted multiplayer simulation crash, dash and language filter — 2026-10-09

Render logs confirmed an 11:05:47 PM EDT simulation-thread crash: a bleeding
Wolf died in a Mini-boss Squadron, then tick called enemies.index on that removed
enemy (game.py line 2797 in the hosted build). HTTP and health stayed available,
but the only simulation thread died, stopping all room movement and enemy AI.
Enemies removed by bleed are now skipped; squadron targeting uses the active
iteration's stable index. Per-room tick errors are isolated and logged with room,
stage and phase (repeats limited to every 30 seconds). The outer simulation loop
also survives unexpected exceptions. Health returns 503 if no successful global
tick has occurred for five seconds, so a stalled loop no longer appears healthy.

Movement input/state requests now time out after five seconds, releasing stuck
input queues; room creation/join allow 60 seconds for free-host cold starts.
Private snapshots carry the accepted input sequence and clients synchronize to
it after refresh/reconnect, preventing new movement from being rejected as old.
Routine successful input, state and health polls no longer flood server logs.
Light attacks retain damage, animation and sounds without filling party chat
with a message on every shot; Special/Ultimate announcements remain.

Dash retains its server-enforced five-second recharge and now shows a progress
bar plus countdown, with fractional readiness from the server. Downed heroes
cannot use the button or keyboard shortcut. English profanity, slurs, common
insults and self-harm harassment phrases are masked server-side in chat/names.
The filter handles common leetspeak, punctuation/spacing, repeated letters,
full-width/accented letters and invisible characters, with word boundaries to
preserve ordinary names/game words. Fully masked names become Adventurer.
This is a curated local filter, not a general semantic moderation service.

Validation: 172 Python tests passed, including the exact hosted bleed/squadron
crash, room isolation, loop recovery, dash enforcement, reconnect sequences and
filter behavior. Browser/client regressions passed. Four simultaneous HTTP
clients completed 3,527 requests across stages 7/13/17/20/25 with no simulation
errors; localhost p95 response was 17.46 ms and longest tick was 3.1 ms. See
reports/MULTIPLAYER_RELIABILITY_2026-10-09.json. These are synthetic local numbers,
not hosted network guarantees. tools/multiplayer_probe.py uses disposable combat
fixtures, without touching real rooms/saves. Its extra HP isolates reliability
from balance. Physical-phone and human-network comfort still need playtesting.

Published runtime commit 9be0e4486ec5c8a0abbc37b32b28fb8c0f6320e2 to GitHub main
and manually deployed it to Render (srv-db4qi6o473hc738p6k70). Render reported Live
at 11:36:31 PM EDT. Hosted smoke testing verified the client bytes match this
workspace, four real HTTP players all moved across 362 requests, enemies
progressed, dash recharge was enforced, chat/names were masked and health stayed
successful. This short hosted check supplements the local stress fixtures;
human multiplayer and physical phones remain necessary for comfort testing.
The local server also restarted with verified copies of both bed checkpoints in
data/backups/before-multiplayer-fix-20261009-233607. Hosted live rooms reset during
deployment; the free Render service still has no durable checkpoint disk.

## Village variety and equipment click reliability — 2026-10-09

Villages now choose from seven arrangements: market ring, two hamlets, winding
street, staggered lanes, western common, crescent and scattered courts. Visits
avoid repeating the previous arrangement, mirror and jitter buildings,
occasionally relocate a whole building, and shuffle all services including the
Guild. Roads use branching, loop or lane networks with multiple commons instead
of a single central crossroad. Villagers cluster around the commons or scatter;
regional trees stay clear of roads. All six services, every party spawn and the
welcome runner remain accessible. Layout metadata uses the existing townDecor
checkpoint field; old checkpoints retain their saved village until the next visit.

The pouch previously rebuilt its buttons on every fractional ability cooldown
or HP update. A pressed button could disappear before release, so equipping
appeared to do nothing. Item/slot changes now rebuild the inventory; health,
mana and status only refresh utility availability. HUD utility buttons likewise
remain stable. Both tools and all three utility slots still swap occupied slots
atomically, including when the pouch is full. Shop utility availability refreshes
without rebuilding the inventory, and mana draughts can be used there too.

Validation: 162 Python tests passed; all Node client tests and app syntax passed.
A 2,000-seed generation probe completed without failures. New regressions cover
seed stability, diverse/connected road layouts, consecutive visit variety, and
equipment button identity/click dispatch during health, mana and cooldown polls.
An isolated browser run verified equipping and swapping both tools and all
three utilities against the real server, and reviewed multiple village layouts.
No physical-phone or human multiplayer session was run for this change.

Python changes require a server restart; clients should refresh for the pouch
fix and road drawing. Downloaded copies on another computer need the updated
files; editing this workspace does not automatically update those copies.

Activated locally on port 8000 in exec session 99629. Both bed checkpoints were
copied and SHA256-matched to data/backups/before-village-equipment-20261009-225915
before restarting. HTTP health and exact current app.js bytes were verified.
The isolated QA server and browser tab were closed. These changes have not been
published to GitHub or Render in this task.

## Render free deployment preparation — 2026-10-09

The user chose Render free hosting. `render.yaml` defines one free Python web
service in Virginia with manual deploys, `/healthz`, and `HOST=0.0.0.0`.
`server.py` reads HOST/PORT while retaining local IPv6/IPv4 defaults.
`.python-version` selects Python 3.13; requirements.txt documents stdlib-only use.
README contains the Deploy to Render link and release instructions.
Free hosting loses its temporary checkpoint files on sleep/restart/redeploy;
local data is excluded from publication. Rooms require a single process/instance.
Render deployment is live and verified:
https://the-gauntlet-d0pc.onrender.com
Service: srv-db4qi6o473hc738p6k70; Blueprint: exs-db4qi3o473hc738p69sg.
Dashboard: https://dashboard.render.com/web/srv-db4qi6o473hc738p6k70
Deployed commit: 4d357efdb57c627e4277ddf4aaef8ff9c3e2f526.
Render confirmed Free plan and successful deploy; runtime Python 3.13.16,
listener port 10000. Public browser smoke created room 2ZP96, selected Knight
abilities, entered Stage 1 / Wave 1, and showed no browser errors/warnings.
Rapid consecutive ability choices required reselection after server responses;
remote-latency choice synchronization remains an observation for future work.
Proof: reports/RENDER_LIVE_2026-10-09.jpg. Local server was not restarted.

Deployment HTTP checks pass for health, client, room creation, joining and state.
The full suite passed 160 tests on rerun. Initial full run had six village
routing errors; isolated village checks and the rerun passed without code changes.
This intermittent observation remains open; no village changes were made here.

## Latest GitHub publication — 2026-10-09

The user requested publishing the current playable build to
Nael-Shakhsheer/The-Gauntlet main, including the HUD, all 48 ability icons,
eight hero casting atlases and shared ability animation integration.
157 Python tests passed, as did Node syntax, equipment comparison, movement,
audio and held-attack/client checks. Public uploads exclude saved data, large
authoring projects, release archives and machine cleanup records. The earlier
tracked October 6 ZIP remains on GitHub; its local cleanup is not a request to
erase repository history. Record the verified publication commit after upload.

Publication completed and remote main/tree verified:
https://github.com/Nael-Shakhsheer/The-Gauntlet/commit/c47db9e6576e31b3fe9805c056c34886be5399ff
All 357 current public game files match GitHub blob hashes; the retained legacy
ZIP brings the repository to 358 files. This includes all 57 new runtime PNGs,
source and metadata for icons/casting animations. Saves and cleanup records were
excluded. GitHub's main archive downloads the complete playable source build.

## Ability casting poses and shared ultimate eruptions — 2026-10-09

Eight new hero animation atlases add three-frame Light, Special and Ultimate
body sequences. Each has eight directions: five generated views and three
deterministic mirrors. All 48 ability IDs connect to these class/type body
sequences and their own artwork/colors/effect treatments. Alternatives share
their class/type physical sequence; there are not 48 independent body atlases.
Druid crouches/kneels to trace summoning circles, Archer draws a massive bow,
Bard uses a full-size concert harp, and the other five heroes have matching
physical casting actions. Original idle/move sheets remain intact.

Every successful Ultimate has glowing rising pixel ribbons, expanding ground
energy, class/ability particles and its actual name visible to teammates. Shared
cast IDs and relative elapsed/remaining time come from ability_animations.py,
through player snapshots and ability_cast effects. Held Light attacks cannot
erase a longer Special/Ultimate pose. Class, stage, status and scene changes
guard stale animations; final-enemy kills can finish their brief cast into loot
or exit. Actual affected recipient IDs drive teammate buff/heal/revive particles.
Projectile visuals now use the dedicated animated flight atlases described
above, including ice shards, arrows, bottles, thorns and musical notes.
Cover-target shots also retain IDs.

The four Druid summons have circle emergence and lightning/fire/ice/stone attack
particles. Enemy windup sheets still follow actual role/boss attack progress,
with concentrated energy, charge dust and release particles. Normal enemy
attacks now select imported attack frames too. Enemy support healing, pounces,
charges, heavy strikes, Draco shot/bite cycles and all adult Dragon affinities
keep their current creature bodies and committed directions. Combat rules,
cooldowns, mana, inputs, movement and damage/spawn timing are unchanged.

static/ability-animations.js is registered in the server static whitelist and
integrated into app.js/combat-environment.js. audio.js follows public cast IDs
to avoid duplicate or missed cast cues. Eight generated source atlases, exact
prompts, references, 48-ID coverage, hashes, 576-cell crop/mirror manifest,
PowerShell exporter and native preview are retained in art/ability-animations.
Gutter detection is necessary: equal fractional crops cut off source feet.
Fixed per-hero scale and foot baseline match the old sheets; ultimate props
remain larger. See WORKFLOW.md. preview.html is a local artwork viewer using
the actual renderer, with all 48 choices and eight directions; it makes no rooms.

Artwork/native exports were visually reviewed; Python/JavaScript syntax checks
passed. No automated gameplay tests or full multiplayer play-through were run.
Both disk checkpoints were copied and SHA256-matched to
data/backups/before-cast-animations-20261009-123304 before the authorized restart.
Python updates require a restart; static assets require clients to refresh.

## Ability icons and recharge rings — 2026-10-09

All 48 ability choices now have distinct literal pixel-art designs, including
an ice shard for Frost Lance and separate Druid summon icons. Individual
64×64 transparent icons and a complete 6×8 atlas/metadata live in static/sprites.
Lobby and Guild ability choices show the same icons as the equipped HUD.

The central ability bar now contains Light, Special and Ultimate, between the
two tools. It reuses the actual held-Attack button and retains its input listeners;
buttons persist across cooldown snapshots. Numeric ability countdowns are
replaced by a clockwise glowing red ring. The full ring becomes green when
cooldown readiness is confirmed, mana is sufficient and the hero can act.
Names, shortcut hints and mana costs remain. Active Druid summons show Active
with an empty ring and begin refilling after death. Low mana remains labeled.
Desktop HUD/world offsets and narrow-screen icon sizes accommodate the circles.

The private ability-slot snapshot adds fractional cooldownRemaining alongside
the existing rounded cooldownLeft. The client advances visuals between polls
but does not show Ready before server confirmation. Ability rules, cooldown
durations, costs and saves are unchanged. Python requires a restart for the
precise field; static changes require a browser refresh.

art/ability-icons retains eight built-in ImageGen sources, all exact prompts,
48 design descriptions, a style reference, deterministic PowerShell exporter,
crop/export manifest and catalog/cooldown previews. Artwork was visually
reviewed; no implementation tests or full live gameplay checks were run for
this request. See art/ability-icons/WORKFLOW.md for rebuilding.

Activated on port 8000 after copying and SHA256-checking both bed checkpoint
files to data/backups/before-ability-icons-20261009-115336. The identified old
server was stopped under the existing restart authorization; the current
project's server.py is now running in exec session 5719. Live rooms reset;
both disk checkpoints remain intact. Refresh the game page to load the icons.

## HUD tools, utilities and rune star — 2026-10-09

Tool 1 and Tool 2 now flank the bottom HUD's central ability/interaction space.
They show the equipped tool sprites and open the pouch when clicked. The three
utility slots sit directly under Help/Gather/Enemy; their click actions and 1/2/3
shortcuts still use the utility items. The movement pad is hidden for mouse/keyboard
devices through the hover/fine-pointer media query and remains on touch devices.
The center retains working Special/Ultimate controls and cooldown labels, ready
for the user's future ability sprites/animations; no new artwork was supplied.

The STAR puzzle rune and totem clue now draw matching five-point symbols in slate
and brass frames, replacing the old six-point sprite for that sigil. The fallback
text glyph is also a five-point star. Other rune artwork is unchanged.
Client syntax and existing held-attack, movement and equipment-comparison checks
passed. An isolated browser fixture using the actual HTML/render functions verified
1280x720 and 390x844 layouts without horizontal overflow, utility click dispatch,
tool-to-pouch behavior and both star drawings. Physical-phone testing remains open.
Refresh the HTTP game page; no server restart is required.

## Consolidated OneDrive backup — 2026-10-08

The user requested one complete backup and removal of game files that only take
up space. The verified backup is the sibling file
`../The-Gauntlet-Complete-Backup-2026-10-08.zip` (800,772,746 bytes; SHA256
bbb89c40483b81d9844bdf7ac8f91ad09c4ffe03a8980cec82f4f826d00b0925).
It contains the complete current project including original art, saved data and
Git database, plus the older laptop copy and release history. All archived entries
passed CRC and SHA256 checks. Current files have their ordinary layout inside
The-Gauntlet/. Historical versions share identical content through _Backup/INDEX.json
and _History/, with _Backup/RESTORE_HISTORY.py for restoration. Old release ZIP
wrappers were flattened; all member-file contents were retained. Python bytecode
caches were omitted as regenerable files. OneDrive cloud sync was not verified.

Cleanup completed after the user explicitly approved the exact deletion list.
Removed the older laptop copy, releases, original visual art folders, reference
screenshots, data/backups, bytecode caches, stale package manifest and old root ZIP.
All 2,262 removal candidates were checked against the backup's source hashes or
identified as disposable caches/generated metadata before deletion. Git storage
was compacted. Removed 2,338,372,728 bytes; after adding the single backup and Git
compaction, net space reduction is 1,538,468,847 bytes (about 1.54 GB).
See reports/CLEANUP_2026-10-08.json for the completed audit.

The current working game, all 215 static files, art/audio, both bed checkpoints
and active Git repository remain. Runtime file hashes matched before/after and
live HTTP checks passed for the page, client scripts, Druid sprite and Bard audio.
The server was not restarted. Visual authoring paths mentioned below and in
README.md now refer to archived material: extract The-Gauntlet/art/ from the
complete backup when editing original art. Historical versions can be restored
using the archive's _Backup/RESTORE_HISTORY.py.
The root legacy ZIP removal is a local Git working-tree deletion; cleanup changes
have not been committed or published to GitHub.

## Tactical update and publication — 2026-10-07

Publication completed and remote main/tree verified on2026-10-08:
https://github.com/Nael-Shakhsheer/The-Gauntlet/commit/92e417c5f4db837c80aa9d28153eb496e247031d
The code commit contains290 files, including the prior October6 archive, all147
runtime binary assets and142 source/document/test files. Every runtime asset SHA
matches the verified local build; private checkpoints are excluded. Earlier
publication-pending notes below are historical. The large ZIP upload was replaced
by a complete runnable source commit through the authenticated GitHub connector.
The local main branch now tracks origin/main. Its Git index was connected with
a mixed reset that preserved the working files, original art and both saves;
the previously published legacy ZIP was restored into the root. Large visual
authoring art and reference screenshots are locally ignored, while audio rebuild
sources remain tracked. Git publishing through the connector works; the native
Git credential store has no signed-in account, so future native pushes may need
sign-in. Public fetches work.

The user selected the reassessment's ability alternatives, description accuracy,
behavioral gear and signature bosses for implementation. `tactical_rules.py`
holds ability metadata, four build items, roots/bleed and equipment modifiers.
Druid Briar controls groups versus focused Thornshot; Wizard Arc chains versus
lower-DPS Frost control; Cleric Radiant splashes versus focused Sanctified Throw.
Rain of Arrows is a committed targeted area (380 cast range, 110 radius, .65s
delay), and Death Bloom actually bleeds for five seconds. Actual control honors
resistance, line of sight and attribution. Universal Ultimate cooldown remains15s.

Conductor, rescue cuirass, summoner staff and pursuit blade have explicit costs;
unique effects do not stack. Summon gear preserves health fraction without swap
healing. Pursuit requires actual Dash/Blink/Shadowstep movement and consumes one
follow-up. Rescue protection ends with the channel and has8s recharge. Shops
offer build tools, and pouch/shop comparisons show stats and gained/lost effects.
`equipment-comparison.js` is registered in the HTTP static whitelist. New item
icons reuse existing sprites with distinct borders. Concurrent Bfxr audio work
and adult Dragon/Draco art were preserved.

Great Minotaur charges collide with cover and create3s vulnerability (+35%).
Behemoth raises/shatters cover, Matriarch lays interruptible connected poison,
and Fire/Ice/Storm/Dark/Arcane Dragons each alter the spatial problem. Boss state
includes concise tactics and armor/true-form labels. Phase two is foreshadowed,
changes elemental tactics and starts with brief recovery. Cover stays bounded,
clear of standing actors, and friendly Rain cannot damage heroes.

157 Python tests passed, including23 tactical regressions. Node tests passed for
equipment comparison, audio, movement, held attack, personal chests, damage
flash and town sprites. Isolated port8001 browser verified descriptions, one-click
staff replacement and comparison gain/loss updates, desktop and390x844 wrapping,
with no console errors. The twelve-second light probe verifies roles in stationary
one/three-target fixtures, not human balance. See reports/TACTICAL_UPDATE_VALIDATION.md.

Activated on port8000 after hash-checking both bed checkpoint copies in
data/backups/before-tactical-20261007-223417/. The prior audio server was stopped
under the existing restart authorization and replaced by the current root's
server.py (exec session76303). Live equipment-comparison.js returned200. Live
rooms reset as expected; both disk saves remain intact. The verified playable
ZIP passed all157 Python tests after extraction into a fresh temporary folder.

GitHub publication is authorized for Nael-Shakhsheer/The-Gauntlet main. The old
branch still held the October6 ZIP when the user checked: a large ZIP connector
upload failed and no commit had been published. Use source plus all runtime assets
instead. Never claim completion until the remote head is verified. Public source
excludes data/checkpoints, release archives, large original visual art and reference
screenshots; full local ZIP preserves art and optionally saves. `package_game.py`
supports --runtime-only and excludes stale root PACKAGE_MANIFEST.json.

## Current-build reassessment — 2026-10-07

The planning chat reassessed the latest build; see
`reports/DESIGN_REASSESSMENT_2026-10-07.md`. It credits implemented targeting,
prediction, objectives, sprites, audio and independent run length. Limited early
Druid combat and 390x844 browser inspection used a separate in-memory port8001
server; production rooms/checkpoints were left intact. Portrait aspect stretching
is confirmed (960x540 canvas displayed about390x628). An isolated kit check also
confirmed an all-healing solo Healer can still start. Remaining proposals prioritize
display/kit correctness, ability tradeoffs, behavioral equipment, boss identities
and human full-run/phone tests. No gameplay changes; this does not authorize all
recommendations. Desktop/phone reference images are alongside the report.

## Retro sound effects — 2026-10-07

The first audio layer is implemented using actual Bfxr 1.0.4 synthesis code
(the user's "BXFR" was interpreted as Bfxr after checking its official site).
Twenty small local WAVs in `static/audio/` cover class Light attacks, Specials,
Ultimates, dash, damage, healing, down/revive, loot/curses, interactions, stage
and puzzle clears, ambush/dragon phase warnings and impacts. No soundtrack yet.
`static/audio.js` reads confirmed snapshots through `app.js`, suppresses repeated
effects and stale reconnect/background events, attenuates/pans remote sounds,
limits voices and uses a compressor. It changes no gameplay, save formats or
action protocol. Very brief events between polls can be missed.

Main-menu Sound settings and in-game Menu → Sound settings provide a 45% default
effects volume, mute and Test sound. Preferences persist per browser/site in
`gauntlet-audio`. Click/tap/key gestures create/resume audio; sounds before
activation are discarded. Failed audio cannot block the game. WAVs are served
by a restricted `/audio/` route and the new script is registered in `server.py`.
Refresh the HTTP page to load audio. No editor, npm packages or audio API key
is needed at runtime.

`art/audio/WORKFLOW.md`, `sounds.json`, `build-sounds.cjs`, source hashes, retained
Bfxr source and MIT/Apache license texts provide a portable rebuild/tuning path.
Run `node art/audio/build-sounds.cjs`; Node is only needed for authoring. The
20 mono 44.1kHz/16-bit files total about 400KB, with bounded peaks/short fades.

Validation: 134 Python regressions and existing held-input/client sprite checks
passed; the new Node audio checks cover activation, attack/damage/dash/status
feedback, deduplication, reconnect/background suppression, mute, bounded bursts
and all WAV headers/levels. JS syntax passed. Browser verified live sound-bank
loading/decoding (Sound ready), Test sound with no console errors, mute, keyboard
volume control, main and in-game entry points, and modal fit at 390×844. Screenshot:
`reports/audio-settings-phone.jpg`. Human headphone mix review and physical-phone
audio-policy testing remain; automated checks do not judge the sound aesthetically.

The server was restarted under the standing authorization after copying and
hash-checking both bed checkpoints to `data/backups/before-audio-20261007-200314/`.
It now runs on port8000 (exec session46002, PID28064 at activation). The earlier
server PID27224 and extra restart process35444 were stopped. In-memory rooms
reset; bed saves were preserved. Do not assume process IDs remain current later.

## Draco and adult Dragon sprites — 2026-10-07

The compact Dragon design from the first combat sprite pack now belongs to
Dracos, with dedicated `draco-idle` and `draco-windup-v1` PNG/JSON files. It is
copied exactly from the original game sheets. Existing Draco shot/bite behavior
and spawn/balance rules are preserved. The renderer maps shot preparation to
channel frames and bite preparation to heavy frames; movement returns to live
facing after recovery instead of retaining the previous attack direction.

Final Dragons now use a new fierce adult design with an elongated snarling head,
large ivory horns, heavy charcoal scales, broad leathery wings, four clawed legs
and a long barbed tail. `dragon-adult-idle-v2` and `dragon-adult-windup-v2` are
1044×1044 sheets with 116×116 cells and a 96×96 native artwork footprint, versus
Draco's 68×68 cells and 48×48 artwork. Both have eight directions, using exact
mirrors for eligible west-facing views. Idle, movement, attack and progressive
charge/breath/channel windup animations are imported. Elemental glows and the
final boss's phase-two growth remain.

Client base/windup renderers use the new adult filenames and a larger display
tile. Adult health bars/glows/shadows are sized for the larger body; the shared
damage-flash canvas is enlarged to fit the wings. No server rules or checkpoint
formats were changed by this art pass. Other concurrent Draco gameplay changes
in `game.py` and `enemy_roles.py` were preserved.

`art/dragon-lineage/` retains the compact references, adult concept, two generated
animation sources, exact prompts, crop manifest, builder, artwork inspection
inventory, animation gallery and field size comparison. The shared combat pack
exporter now accepts a separate manifest and configurable cell/footprint sizes,
while its original pack keeps the same defaults. Artwork was visually reviewed;
no implementation tests or live gameplay checks were run for this art pass.
Refresh the browser for the new art.

## Combat sprites and cursed item art — 2026-10-07

The current browser client renders seven enemy families (Minotaur, Troll,
Serpent, Wolf, Spider, Dragon and Chimera/`monster`) with new attack anticipation
sheets. Each has three progressive frames for charge/pounce, heavy attack and
aim/channel preparation in eight directions. West-facing directions are exact
mirrors of the corresponding east-facing source poses. Dragon and Chimera also
have new idle/movement/attack base sheets, replacing their procedural fallback
once loaded. Existing enemy identity, elemental glows and boss sizing remain.

Fresh room snapshots feed `GauntletCombatEnvironment.observe`; relative server
windup progress advances the body animation and holds the loaded pose until the
attack releases. Facing remains committed through release/charge. Boss recovery
triggers its attack release frames even without server `animationUntil`.
Cancellation without recovery/charge returns to normal animation. Visual state
is pruned with removed entities and reset between room/stage changes.

Four regional cover atlases provide crate/rock intact, damaged (half HP) and
destroyed debris states, hit shake and a short destruction burst. Terrain sprites
cover trap plates, warning seams and raised spikes, bubbling poison and ice
glimmers. Trap activation follows the authoritative warning/cooldown transition.
Animated warning runes, slams, meteor impacts and damaging pools stay clipped to
the actual hazard radius. Existing precise danger boundaries, aim lanes,
countdowns, progress bars and loading fallbacks remain. Arrow, rock, orb,
lightning and dagger flight sprites and hit/burst/slash/bleed/heal/aura/cast/dash
effects replace the former generic shapes when loaded.

Ashen Shackles (`sluggish`), Brittle Oath (`frail`) and Hollow Edge (`weakened`)
have individual transparent icons displayed beside the existing private curse
description in the affected player's pouch. This introduces no new curse or
equipment slot and preserves curse duration and privacy.

Pack: `art/combat-sprites/` retains 19 original asset requests, corrected sources,
all exact prompts, identity/palette references, manifest, export builder,
inspection inventory and preview galleries. Runtime PNG/JSON files are in
`static/sprites/`; client changes are in `static/combat-environment.js`,
`static/app.js` and `static/style.css`. Source and exported artwork were visually
reviewed and normalized with nearest-neighbor scaling/binary alpha. No gameplay
or implementation tests were run for this art pass. Refresh the HTTP browser
page; Python/server rules, startup dependencies and checkpoint data are unchanged.

## Planning review — 2026-10-07

The user designated a chat for developer critique and forward design. The current
review is saved in `reports/DESIGN_REVIEW_2026-10-07.md`, with a live visual reference
in `reports/design-review-live.jpg`. It combines limited browser inspection of the
early game with current source/report review; it is not a completed campaign,
human multiplayer balance test or physical-phone test. Priorities include combat
feedback/target control, viable and meaningful loadouts, encounter pacing, stacked
difficulty, behavioral equipment and boss identity. These are planning proposals,
not approval to implement the entire review. No gameplay code changed.

This file saves the project's working context for a new chat or another computer.
It is a summary of decisions and implementation, not a copy of the conversation.
Read `README.md` for the normal startup instructions. `GAME_DESIGN.md` contains
earlier planning and can disagree with the more recent decisions below.

## Continue on another computer

1. Copy and extract `The-Gauntlet-Laptop-2026-10-06.zip` on the laptop. The archive
   includes the source, instructions, and all imported sprites. The original
   sprite ZIP files on the home PC's D: drive are not required.
2. Install Python 3.10 or newer if needed. No third-party Python packages are
   required.
3. Open the extracted **The Gauntlet** folder as the coding workspace in Codex or
   ChatGPT Work. Start a new chat with the prompt below.
4. In a terminal in that folder, run `python server.py` (or `py server.py` on
   Windows if that is how Python is installed). Open `http://127.0.0.1:8000/`.

Suggested new-chat prompt:

> Read AGENTS.md, PROJECT_CONTEXT.md, and README.md. Continue working on The
> Gauntlet from its current state. Preserve the agreed game design and existing
> features. I prefer you to implement routine changes without repeatedly asking
> for approval. My next change is: [describe the change].

The archive is a snapshot; subsequent edits on one computer do not automatically
update the other. Copy an updated project back before continuing there. Active
rooms run in server memory, while inn checkpoints persist under data/checkpoints/.
Copy data/ too when transferring saved runs; combat progress since the inn is not saved.
Keybindings and browser room identity are stored in that browser's localStorage.

## Product and user preferences

- A real-time, top-down, cooperative pixel fantasy game for **1-4 players**.
  Friends join from phones or laptops using a room code without accounts or an
  installation. The game is not turn based.
- During play, the game fills the playing view. HP is a red bottom bar; mana is
  blue; three equipped utility slots appear on the right side of the bottom HUD.
- Combat, explorable towns, physical fork paths, and separate puzzle rooms form
  a run. Avoid replacing these with full-screen choice popups.
- Keep future destinations' encounter types and difficulty hidden. Boss and town
  counters and raw phase titles such as STAGE_EXIT should not appear in the HUD.
- Sprites should resemble the supplied directional pixel art, with distinct
  elemental glows. Town characters are smaller so they fit the buildings.
- The user wants implementation to proceed autonomously for ordinary changes.
  Do not ask for approval at every turn.

## Architecture and file map

| File | Responsibility |
| --- | --- |
| `game.py` | Authoritative GameWorld, classes/abilities, actions, movement, combat, enemies, difficulty, stage schedules, routes, towns, economy, inventories, checkpoints |
| `puzzles.py` | Puzzle creation and private per-player room/clue views |
| `server.py` | Standard-library HTTP server, room/join/action/state APIs, static assets, simulation loop |
| `static/app.js` | Browser input, polling, interpolated canvas rendering, sprite animation, HUD and menus |
| `static/index.html` | Client page structure |
| `static/style.css` | Pixel fantasy UI, responsive playing view, menus and overlays |
| `progression.py` / `static/progression.js` | Hunter story, first-village welcome/tutorial, stat training, upstairs inn rooms and bed checkpoints |
| `static/town-sprites.js` | Supplied service NPC, villager and floating chest animation renderer |
| `static/sprites/` | Imported Knight, Wizard, Serpent Guard, Minotaur and Cave Troll PNG sheets with JSON metadata |
| `README.md` | Running and playing the game |
| `GAME_DESIGN.md` | Earlier broader design notes; some sections are outdated |

The server ticks at approximately 20 Hz. The browser polls state at approximately
10 Hz and renders independently using requestAnimationFrame and interpolation.
The arena coordinate system is 960 x 540. No framework or package install is
currently needed.

HTTP APIs: `POST /api/rooms`, `POST /api/join`, `POST /api/action`, and
`GET /api/state?room=...&player=...`. Static files are served by the same server.
Sprite PNG/JSON requests are restricted to the `static/sprites` directory.

## Heroes and controls

Only one player can choose each class in a party. There are now **eight** classes
(the initial seven gained a separate Healer).

| Hero | Role | Base HP |
| --- | --- | --- |
| Knight | Melee tank | 150 |
| Wizard | Ranged arcane caster with support options | 100 |
| Archer | Fast ranged piercing attacks | 105 |
| Cleric | Splash-potion support | 85 |
| Rogue | Fast bleed damage and temporary invisibility | 80 |
| Druid | Elemental summoner with projectile Light attacks | 80 |
| Bard | Team damage and movement buffs | 75 |
| Healer | Strong healing and rapid revives, low damage | 110 |

Each class has two Light, two Special and two Ultimate choices in
`ABILITY_SETS`. Equip one from each category, for three abilities total. The
source is authoritative for ability names, powers, mana costs and cooldowns.

- Move with WASD by default; arrows and a touch pad also work.
- Left click / touch Light button: Light attack. Q: Special. X: Ultimate.
  Main-menu Controls & keybindings can remap relevant actions.
- Space: directional dash, five-second recharge.
- E: interact. Hold E near a downed teammate to revive in combat.
- 1, 2, 3 or numpad 1, 2, 3: equipped utilities. Clicking the slots also works.
  Gameplay hotkeys should not fire while typing in chat or another input.
- Light, Special and dash cooldowns refresh when entering a new stage. Summons
  are removed. Every hero's equipped Ultimate starts on its full cooldown,
  including the first combat stage and combat following towns or puzzles.
  New waves do not restart the Ultimate timer.
- Built-in party text chat supports puzzle coordination.

### Druid summons

Both Light choices, Briar Bolt and Thornshot, launch projectiles. Equip one
Special and one Ultimate from the following choices, using the normal loadout:

| Category | Summon | HP | Attack | Recharge after death |
| --- | --- | --- | --- | --- |
| Special | Lightning Bird | 55 | Ranged lightning projectile | 8 seconds |
| Special | Fire Wolf | 90 | Melee | 8 seconds |
| Ultimate | Ice Bear | 180 | Melee | 15 seconds |
| Ultimate | Nature Rock Golem | 240 | Melee | 15 seconds |

Summons chase and attack their nearest enemy independently. Enemy melee and
projectiles can damage and kill them. Their ability is locked while alive;
recharge begins only at death, and the HUD shows Alive or the remaining timer.
One equipped Special summon and one equipped Ultimate summon can coexist.
Special summon hits deal 90% of the equipped Light attack's damage, rounded to
an integer; both Ultimate summons hit for exactly twice that Light damage.
Damage uses the owner's equipment, active damage buffs and curse at cast time.
Summons have no timed expiry. Survivors keep their HP between waves within a
stage. At the next stage, all summons disappear. Special becomes ready again,
and Ultimate begins its full 15-second cooldown. This replaces any unfinished
death recharge. Players must cast them again. Wave countdowns and new waves do
not reset them.
Leaving the room, changing class, checkpoint recovery or a full-party wipe
dismisses them. They cannot continue the run after every hero falls.
Each has distinct animated canvas art, a friendly name, an HP bar, and damage
flash support. The former timed spirit-wolf damage buff has been replaced.

## Combat, difficulty and run progression

- At the start of a combat stage, players form a line near the bottom and enemies
  begin near the top with space between them.
- Clearing a wave starts a **three-second countdown** at the top. Retain the
  current scenery and player positions; the next enemies run in from an edge.
- Ordinary wave base counts are currently 1-2 / 3-5 / 5-8 / 8-12 for one / two /
  three / four players. Stages have two waves for one or two players, three for
  three or four. Party size also scales enemy HP, damage, speed, aggression and
  projectile speed. Hidden route modifiers can change these base results.
- Enemy families include Serpent Guard, Minotaur, Wolf, Cave Spider and Cave
  Troll. Mobs receive combat kits drawn from the eight hero classes, including
  ranged and support attacks. They can move while attacking; squadrons flank and
  try to surround players. Minotaurs receive a 30% speed boost.
- Enemy projectiles aim once and then travel straight so they can be dodged.
  Heroes and enemies have attack animation/effects, including projectiles.
- A short attack-range indicator surrounds the local hero during combat.
- Downed players have an eight-second revive window. The Healer revives faster.
  Enemies become more aggressive around knockdowns. A full-party wipe recovers
  at the latest inn checkpoint, loses 40% of shared Runes, and retains items.
- Gradual added difficulty starts at **stage 8**. `_stage_ramp` uses
  `0.62 + 0.38 * (stage - 1) / 24`, then adds `0.08 + 0.04 * (stage - 8)` for
  stage 8 onward, clamped to stages 1-25. Existing stat/cadence calculations use
  that ramp. This latest tuning did not add extra waves or extra enemies.
- Large bosses occur at **stages 8, 16 and 25**. The last is always a randomized
  dragon. Two to four miniboss stages are distributed through each boss interval.
  Miniboss encounters use an empowered enemy or a larger squadron.
- First-boss pool: Serpent Matriarch, Labyrinth Minotaur King, Ancient Stone
  Behemoth, Chimera, Great Wolf Guardian. Dragon types: Fire, Ice, Dark Magic,
  Arcane and Storm.
- One 8% roll per new run determines whether an assassination ambush is scheduled
  on an eligible combat stage. It can occur at most once even after checkpoint
  recovery. Stronger enemies enter from all four sides, scaled to party size.
- Victory celebrates the final dragon defeat; defeat uses a dark presentation.

## Physical exploration and routes

- Stage rewards use a physical chest in the arena. Approach and press E; announce
  obtained loot to the player. There is no separate "leave unopened" choice.
- After combat and any treasure, prompt the party to gather at the top opening.
  This transitions into a **separate fork area**.
- Follow the left or right trail all the way to its screen edge. Everyone must
  reach an exit; majority wins a split vote and the host breaks a tie. Moving
  away cancels a player's vote. The server constrains movement to the trails.
- Fork signs show actual **location names**, not encounter spoilers. The sign
  was moved upward onto grass to avoid covering the path.
- A hidden pressure counter changes with the chosen path. Its run modifier
  affects **wave size OR enemy HP**, never both together. A rare, one-use
  Pathfinder's Lens provides a clear indication of the easier route.

## Towns, items and checkpoints

- Runs schedule 2-4 towns, weighted 15% / 70% / 15% for two / three / four. Counts
  are hidden. Village names: Mossgate, Bellweather, Hearthrest, Silverbrook and
  Rookhaven.
- Each village shuffles building locations and appearance. Players walk around
  outside, then enter individual building interiors with E at the door.
- Innkeeper, Merchant, Alchemist and Guildmaster are inside the Inn, Store,
  Alchemy Lab and Guild. All six buildings, including the two decorative houses,
  share the shuffled location and appearance system on every town visit.
  Approach the NPC and press E. There are additional decorative houses.
- The Guildmaster opens a hero picker and allows **one class change per player
  per run**. The current hero and heroes already taken by teammates are disabled.
  Selecting a hero previews that hero's six class-specific skills with the two
  options in each category shuffled and one random default choice per category.
  Each hero currently has exactly six skills, so randomization changes their
  order/default loadout rather than drawing new skills or borrowing other classes.
  Choose one Light, one Special and one Ultimate, then confirm to spend the change.
  Back out, Escape, or return to the hero list without spending it. Previewing and
  polling do not change the live class/loadout. The server validates location,
  class availability, the loadout and the per-player limit atomically.
- A class change retains carried/equipped items, mana, curses and HP percentage,
  updates base HP and class-specific merchant stock, and resets ability/dash
  cooldowns. The class, loadout and used allowance survive later towns and wipes.
  Village entry and checkpoint recovery spawn below the lower building row; the
  main path runs between buildings so the new sixth building does not block it.
- Upstairs beds in unlocked inn rooms restore the party and record the checkpoint;
  innkeepers teach and offer stat training. Merchant stock is
  class-specific (e.g. Wizard wands rather than Knight swords). Alchemist has
  potion/restoration interaction. There is no town-to-town travel menu.
- To leave, every player gathers at the outside gate and presses E to vote.
  Moving away cancels that player's readiness.
- Currency is **Runes**, shared by the party, earned through enemies, chests and
  rewards. Utilities include healing, mana, temporary buffs, special arrows and
  route hints. Loot rarities range from Common through Legendary.
- Equipment: three utility slots, two tool slots (weapon/armor), ten carried
  pouch items. Equip/unequip anywhere; selling requires a merchant. Equipment
  overlays change the hero's appearance and affect combat.
- Pouch opens as a bottom-center bar. **Expand** reveals item descriptions and
  **Collapse** returns to the compact view.
- Curses occupy their own hidden sixth pouch slot; they cannot be sold or
  cleansed and must expire naturally after five completed combat/puzzle stages.
  Towns do not reduce the timer. Current curses slow movement, reduce outgoing
  damage, or increase incoming damage. Chest curse chance is 12% when uncursed.

## Puzzles

- Schedule 1-3 puzzles per run, weighted 65% / 30% / 5%. One is guaranteed;
  a third is rare.
- Players are separated into private rooms containing scattered rune sigils and
  a randomly placed clue totem. Clues require communication across the party.
  Rooms and completion adjust to party size, including solo play.
- Players must stand at their matching rune; all must be correct to proceed.
  Totem/rune use matching clear sigils and colors when the clue is revealed.
- Wrong answers increase hidden run strain slightly: 0.5% per first two mistakes,
  1% per next two, 2% each from the fifth, capped at 15%. It persists across wipes.
- Intro/clue dialogue disappears after **three seconds** and can be reread with E.
  Standing on a rune closes the dialogue and does not create a warning popup.
  Wrong-rune penalties and party chat feedback remain. Totem proximity is now
  physical proximity only; reading a clue remembers it without treating every
  later location as the totem, so E on a rune cannot reopen the clue panel.

## Art and recent changes

- Sprite workflow saved on 2026-10-06 in `SPRITE_WORKFLOW.md`. The user approved
  a generated Cave Troll concept and explicitly requested horizontal mirrors
  for eligible directions. Generate South, Southeast, East, Northeast and
  North; mirror East to West, Southeast to Southwest and Northeast to
  Northwest. Mirroring swaps weapon hands and asymmetric details.
- `art/samples/cave-troll-spritesheet-v1.png` is a 612x612 animation sample
  with 68px cells and idle/walk/attack columns 0-2/3-5/6-8. Its prompts,
  sources, metadata and relative-path rebuild script are retained beside it.
  Diagonal poses are approximate. Cave Troll was subsequently imported into
  the actual game; see the latest implementation notes below. Follow the
  saved workflow for future art.
- `art/exports/Cave-Troll-Sprite-Import-v1.zip` packages this approved sheet,
  metadata, import instructions, a Python importer, and the saved creation
  sources/workflow. The importer backs up files, registers Troll, uses the
  3/3/3 frame ranges, and maps enemy kind `troll` to it. ZIP integrity,
  checksums, import/backups/idempotence and JavaScript syntax passed using an
  isolated extracted copy. The actual game was not modified by packaging.
  `art/exports/build_cave_troll_package.py` recreates the archive.
- `art/exports/Cave-Spider-Sprite-Import-v1.zip` is the next completed art
  package. It includes a 612x612 PNG, 68px cell metadata, Python importer,
  import instructions and retained prompts/source art under `art/cave-spider/`.
  It uses five generated directions and three exact horizontal mirrors, with
  idle/scuttle/bite columns 0-2/3-5/6-8. The importer preserves existing Troll
  entries and supports the original renderer too. Exact mirror pixels,
  distinct frames, ZIP/checksums, isolated imports/backups/idempotence,
  no-write checks and JavaScript syntax passed. Spider is not imported into
  the actual game or checked in live gameplay. Its `WORKFLOW.md` and
  `art/exports/build_cave_spider_package.py` retain the repeatable process.

- Heroes and enemies briefly take on a red hue when damaged. The client keeps
  per-entity damage tracks, flashes for 220ms and fades during the last 100ms.
  A reusable isolated canvas applies the tint only to the character's opaque
  pixels, including imported sprites and hero equipment; elemental glows,
  scenery, name labels and HP bars retain their normal colors.
- `game.py` reports a `damageTaken` event counter for each hero/enemy through
  the shared damage methods, including projectile, melee, area and bleed hits.
  This catches a hit even if healing occurs before the next state poll. The
  client also detects HP decreases for a server process started before this
  update, so a browser refresh can enable the effect without losing active rooms.
  Restarting an older server process enables the counters. Healing, initial spawning and
  a class change's base-HP adjustment do not start a flash.
- `CHARACTER_ROSTER.md` lists the currently implemented heroes, enemy families,
  bosses, dragon types, village NPCs and generated enemy variants.
- Imported directional sprites: Knight, Wizard, Serpent Guard, Minotaur. The
  latest completed change was the Minotaur sprite import from the supplied
  `16-bit_pixel_art_aggress-Idle-spritesheet.zip`.
- All are 9x9 sheets. Row zero provides facing poses; remaining rows correspond
  to South, Southeast, East, Northeast, North, Northwest, West and Southwest.
  Knight/Serpent/Minotaur use 68px cells; Wizard uses 64px cells.
- In `static/app.js`, `heroSprites` and `drawImportedHero` handle imported sheets.
  Minotaur uses columns 0-2 for idle, 3-5 for movement, 6-8 for attack. Other
  sheets have their own pose selections. Imported enemies retain elemental glows
  without hero equipment overlays; bosses/minibosses are scaled larger.
- Enemy affinities Fire, Ice, Dark, Arcane, Poison, Storm and Nature add colored
  glows around the base sprite rather than replacing it with unrelated art.
- Performance work separated rendering from polling, interpolated positions,
  cached scenery/glows, and reduced repeated DOM work. Stage scenery stays
  stable between waves. Town sprites use a smaller scale than combat sprites.
- Recent changes also removed the raw phase-title badge, moved the fork sign,
  and added the gentle difficulty ramp after stage 7.

## Known limits and unfinished requirements

- **No public deployment yet.** Localhost works on the host computer. Same-LAN
  devices use the host's LAN IP; a public link requires a hosting decision and
  deployment. The original multiplayer challenge wanted a public link.
- Runs without an upstairs bed checkpoint, and progress beyond the saved village,
  are lost on restart. Bed checkpoints persist locally under `data/checkpoints/`.
- All eight heroes, five enemy families, four Druid summons, town NPCs, villagers
  and the floating chest have supplied art. Remaining enemy families use canvas art.
- Guild class switching is implemented. `tests/test_guild.py` covers town layout,
  canceling, class-specific randomization, invalid requests, teammate conflicts,
  retained equipment, and checkpoint/once-per-run behavior. Run with
  `python -B -m unittest discover -s tests -v`.
- Balance is evolving from the user's play feedback. Recent syntax checks and
  sprite HTTP checks passed, but comprehensive multiplayer/mobile playtesting
  has not been performed. Do not claim gameplay was fully verified.
- At this handoff, Git exists locally but has no commits and no remote. Nothing
  has been uploaded or published for the laptop transfer.

Latest completed gameplay change: Druid projectile Lights and four independent
elemental summons, requested on 2026-10-06. `tests/test_druid.py` covers projectile
impact, targeting, summon deaths, independent locks, exact recharge durations,
stage transitions, rewards, party wipes, leaving and Guild class changes.
Eighteen Python regression tests and the JavaScript syntax check passed.
Isolated browser checks verified all four summon visuals, the Druid loadout,
and independent Alive locks; the browser reported no errors. Client canvas
checks also cover all four summon renderers and their damage flashes.
`tests/test_damage_flash.cjs` uses Node with @napi-rs/canvas to
verify damage tracking, fade timing, actual tint pixels, transparency, healing
and class-change behavior. Browser checks used an isolated damage fixture with
imported and drawn heroes/enemies; no fixture behavior is in the game. The
earlier Guild browser checks covered cancellation, skill selection, confirmation,
second-change lockout and a 390px phone layout.

Follow-up on 2026-10-06: removed rune warning popups and corrected the remembered
totem proximity flag. Standing on a rune closes any open puzzle dialogue;
E can reread the clue only at the totem. Wrong-rune penalties and chat remain.
`tests/test_puzzle_feedback.py` covers the penalty without a popup, E on a wrong
rune, remembered clues away from the totem, and the shared 58px interaction radius.
All 22 Python tests and JavaScript syntax checks passed; a client function check
verified rune overlay suppression and totem rereading. Restarted the actual
server at port 8000 and verified the new Druid ability list plus spawning Fire
Wolf and Nature Rock Golem in normal combat. Existing rooms were cleared by the
restart; the Druid changes and damage event counters are now active.

Follow-up on 2026-10-06: summons now reset at each new stage, together
with their ability locks and death recharge timers. New waves preserve live
summons, their health and ongoing death recharge. The updated Druid regression
checks exercise actual route-to-stage progression and next-wave spawning.
All 23 Python tests passed. The server was restarted to activate this change.

Latest balance follow-up on 2026-10-06: Druid Special summon damage is now 90%
of the equipped Light's hit damage; both Ultimate summons deal 200%. Every
hero's equipped Ultimate begins each combat stage on its full normal cooldown.
Combat after towns or puzzles applies the opening cooldown, while subsequent
waves preserve it. `tests/test_stage_cooldowns.py` covers both Ultimate choices
for all eight heroes, the first stage, route progression, waves, towns and
puzzles. Druid tests cover both Light choices with equipment, buffs and curses.
All 27 Python regression tests passed.
Restarted the live server on port 8000 and checked all 16 Ultimate choices via
the HTTP API: opening casts were rejected on cooldown, Light/Special remained
ready, and the updated Druid damage multipliers were present. Test rooms were
removed after verification.


## Latest implementation — party tools, durable inns, Cave Troll and held attacks

The user selected roadmap items 4, 5, 12 and 13. All thirteen critique points
are saved in IMPROVEMENT_BACKLOG.md; other items remain deferred.

- `telemetry.py` measures each combat stage, preserving stats between waves:
  actual hero/summon damage (overkill capped), hero/summon HP lost, armor/ward
  prevention, summon survival/uptime/spawns/deaths, elapsed stage time, party
  size, Ultimate casts and whether the stage ended before its opening recharge.
  Bird projectiles retain summon credit after their caster dies. Bleed credits
  its source hero. Rejoining participants are added to the report.
- `run_storage.py` writes atomic versioned inn checkpoints and local append-only
  `data/balance.jsonl`. Production `WORLD` uses the project data folder and a
  15-second disconnect timeout. Plain `GameWorld()` remains isolated for tests.
  Town entry and town transactions save; process restart restores that town,
  player identities, classes/loadouts, items, Guild usage, Runes and schedules.
  Transient summons/buffs/movement are reset. Same-origin browser localStorage
  retains identity; Main menu disconnects and Continue saved run reconnects.
  Pre-inn runs and post-inn combat progress do not survive a server restart.
- Offline heroes do not take enemy aggro or block exits, forks, chests, town
  votes, puzzle answers, or party wipe detection. Stale input stops after two
  seconds; the client refreshes held input every half second. Host transfers
  to an active participant. All-offline rooms pause; reconnect shifts monotonic
  combat deadlines forward by paused duration. Offline heroes remain reserved
  for their returning players, including their chosen classes.
- Cooperative totems form a clue cycle among active players. A player's clue
  describes the next player's rune. Private views never expose whether their
  own multiplayer rune is correct; the whole group answer is evaluated together.
  A new incorrect full arrangement incurs one penalty rather than repeated
  waiting penalties. Solo retains its own clue and feedback. Disconnections
  reassign the cycle; reconnect adds a chamber if the stage began while absent.
- `static/coordination.js` contains teammate HP/rescue HUD, five-second Help/
  Gather/targeted Enemy pings, Share clue, optional five-page guide, resumable
  menu flow and on-demand Run stats/JSON download. `GET /api/stats` keeps reports
  out of the ten-per-second state payload. Phone controls have 44px minimum
  targets and split skill names/statuses; underlying canvas aspect/camera
  behavior is unchanged and remains a future mobile improvement.
- Cave Troll assets imported from `art/exports/Cave-Troll-Sprite-Import-v1.zip`
  after checksum verification. `static/sprites/troll-idle.png/json` use 68px
  cells, eight directions, idle columns 0–2, walk 3–5, attack 6–8. All enemy
  kind `troll` variants use them, including the Stone Behemoth. Existing glows,
  scale, damage tint and fallback remain; Druid golems keep their own art.
- Hold left click on the arena or hold Attack to repeat the **equipped** Light
  with its actual cooldown/range/effects. Pointer release/cancel, focus loss,
  hidden tabs and dialogs stop it. Touch movement and attack are independent.
  `_attack` now calls the equipped Light through `_cast_ability`, replacing the
  unused generic attack path that had different damage and cooldown behavior.
  Rising attack input fires immediately so brief taps cannot fall between ticks.

Validation: 39 Python tests pass, JavaScript syntax checks pass, both Node client
checks pass (held input transitions and all 72 Troll animation cells, plus canvas
red-flash/summon rendering). Isolated port-8001 browser checks covered teammate
health/rescue/offline states, Troll rendering, 390×844 and 844×390 HUD geometry,
quick Help pings, teammate clue display/sharing, guide pages, Run stats, and
Continue saved run. Atomic save/load and reconnect timing have backend tests.

`tools/balance_probe.py` produces `reports/BALANCE_REPORT.md` and raw JSON for
90 deterministic bot simulations: stages 1/8, all eight solo heroes, parties
of 2/3/4 with Druid versus Wizard, and both Druid summon loadouts solo. Bots
approach and cast; they do not dodge, revive, equip items or act like humans.
Use the methodology in the report before drawing balance conclusions. No
additional damage/cooldown nerf was applied. Human-run telemetry is now available.

Activated the update on the live port-8000 server. HTTP smoke checks verified held Thornshot repeats and stops on release, the on-demand stats API responds, and Troll assets plus coordination.js are served. The old pre-persistence rooms were cleared by this activation restart. New inn checkpoints now protect future restarts. Temporary preview server stopped; reports/gameplay-preview.png is a labelled QA-fixture screenshot showing the imported Troll and updated HUD.


## 2026-10-06: overall stats, varied villages, progression and Cave Spider

Latest user request implemented:
- `/api/stats` and Menu → Run stats now return/display overall totals per player:
  damageDealt, damageTaken, revives, deaths, kills, plus name/class labels.
  `room.runStats` accumulates across waves, stages and checkpoint retries. Damage
  counts actual HP lost, includes summon damage, excludes summon HP from hero
  damage taken, and credits the finishing attacker with each kill (including
  delayed summon projectiles). Deaths count falling or party wipe once per life;
  downed heroes rescued in time are not deaths. All revive methods count each
  rescued ally. Inn disk snapshots include totals. Legacy saves without runStats
  start counters after the update. Stage balance telemetry remains local for
  the previously requested contribution analysis; it is no longer the stats UI.
- `_present_routes` saves one 50% fork decision for each non-town transition.
  `_tick_travel` enters a fork or advances directly using `_advance_stage`.
  Scheduled towns arrive directly. The offered fork routes are combat regions.
- `town_layout.py` generates scattered, staggered, row and column house layouts
  with shuffled services/roofs. Grid searches connect the gate/crossroads to all
  doors around house footprints. Roads, trees and 12 non-interactable villagers
  are serialized as townPaths/townDecor/townVillagers. New towns vary spatially;
  inn snapshots preserve scenery on resume. Legacy town saves regenerate roads
  from their saved house positions. Villagers are scenery and never NPC services.
- `_spawn_wave` tunes fresh enemies after selecting their encounter. Every town
  visit adds +25% HP, +20% damage, +10% speed, +12% attack frequency relative to
  untuned values. Miniboss encounters (empowered and squadron) additionally use
  ×1.15 HP, ×1.12 damage/speed, ×1.25 attack frequency. Ranged elites close to 88%
  of their normal range. Town pressure applies on all following waves/stages;
  checkpoint resumes preserve visit count and do not count another town visit.
- Pouch Tool 1/2 and Utility 1/2/3 directly swap incoming and equipped items,
  including a full five-item pouch and different tool types. Displaced items
  return to the pouch. Client swap buttons remain enabled and wrap on phones.
- Supplied Cave-Spider-Sprite-Import-v1.zip assets were checksum verified and
  imported into static/sprites/spider-idle.png/json. Spider uses 68px cells in
  a 612px sheet: eight compass rows, idle 0–2, scuttle 3–5, bite 6–8. All enemy
  kind spider variants use it with existing glows/scaling/damage tint/fallback.
- Existing balance-probe reports are historical baselines before this update.

Validation: 49 Python tests pass. JavaScript syntax, held-input checks, all 144
Troll/Spider directional animation cells, and canvas damage-flash/summon checks
pass. Browser testing on isolated port 8001 verified the generated town, villagers,
full-pouch armor-for-weapon and utility swaps, overall stats, 390×844 stats/pouch
layout without horizontal overflow, and the imported Spider in-game. No browser
console errors were observed. Preview screenshots under reports/ are QA fixtures:
town-update-preview.png, run-stats-preview.png, spider-update-preview.png.

Live activation: port 8000 restarted with this update. HTTP smoke checks confirm
client/Spider assets and the five-counter stats endpoint. The existing UTAE4 inn
checkpoint restores with its saved houses plus generated connected roads and
12 villagers. Existing legacy saves start the new totals at zero. Refresh the
client to load the updated scripts. Temporary QA server stopped after testing.

## 2026-10-06: Wolf, Druid and four summon sprite package

Created `art/exports/Wolf-Druid-Summons-Sprite-Import-v1.zip` with six transparent
612x612 sheets and JSON metadata: Wolf, Druid, Lightning Bird, Fire Wolf, Ice Bear
and Nature Rock Golem. Each uses the established 68px cells, eight compass
directions, idle 0–2, movement 3–5 and attack 6–8. West/Northwest/Southwest are
exact mirrors. Five-direction generation sources, exact prompts, measured crop
bounds, `build-sheets.ps1`, labelled preview and workflow are retained under
`art/wolf-druid-pack/`. Lightning Bird uses measured columns to keep extended
wings inside their own frames. Other sources use measured vertical row bands.

The ZIP includes `import_wolf_druid.py`, `IMPORT.md`, all six PNG/JSON pairs,
source/rebuild files and checksums. The importer registers all six sheets,
maps wolf enemies, enables their 3/3/3 animation ranges, and hooks summon art
inside damage tint before procedural flipping. It preserves the affinity ring,
shadow, health/name labels and existing renderer registrations. Summon sizes:
Golem 1.5x, Bear 1.35x, Fire Wolf 1.15x, Bird 1x. Druid has a general staff-cast
sequence for Light/Special/Ultimate. The package contains no gameplay changes.

This package is prepared for handoff; these six sheets have not been installed
in `static/sprites/` by this task. Sheets were visually inspected and their
export geometry, transparency, frame variation, mirrored pixels and ZIP hashes
checked. No live gameplay review or importer execution was performed for this
batch. Rebuild the ZIP with `python art/exports/build_wolf_druid_package.py`.

## 2026-10-06: Archer, Cleric, Rogue, Bard and Healer sprite package

Created `art/exports/Archer-Cleric-Rogue-Bard-Healer-Sprite-Import-v1.zip` for
the five remaining heroes. Each sheet is transparent 612x612 with 68px cells,
eight directions, idle 0–2, movement 3–5 and general attack/cast 6–8. West,
Northwest and Southwest are exact mirrors. Archer uses green ranger gear and
bow/quiver; Cleric ivory/gold robes and holy flask; Rogue charcoal/violet hood
and twin daggers; Bard rose/burgundy gear and lute; Healer ivory/teal robes and
mercy rod. General attack/cast poses serve Light/Special/Ultimate, while the
game continues to draw the actual projectiles, support effects and invisibility.

`art/hero-party-pack/` retains five original source sheets, exact prompts,
measured row/column crop bounds, final sheets and metadata, animation preview,
`ASSET_REVIEW.json`, `WORKFLOW.md` and `build-sheets.ps1`. Column adjustments
keep Bard notes, Rogue slashes and one Cleric cast from crossing crop boundaries.
The ZIP includes these files, five ready-to-import PNG/JSON pairs, checksums,
`import_heroes.py` and `IMPORT.md`. The importer extends the loader and two
3/3/3 animation lists; it preserves existing sprite registrations and can be
used before or after the Wolf/Druid pack in the supported renderer. Existing
files are backed up and unchanged repeated imports do not write files again.

All five sheets were visually inspected. Export grids, padding, alpha, distinct
frames and exact mirrors passed asset checks; ZIP content hashes were checked.
These sheets are prepared for import and have not been installed into the game
by this task. Importer execution and live gameplay were not evaluated. No
gameplay/server files changed. Rebuild the ZIP with
`python art/exports/build_hero_party_package.py`.


## 2026-10-06: Campaign difficulty, companion AI, boss rework and sprite imports

Implemented the user's campaign/combat request and both subsequent sprite ZIPs.
Current runtime imports supersede the earlier "prepared, not installed" entries:
all eight hero sprites are active, plus Wolf and LightningBird/FireWolf/IceBear/
NatureGolem. Copied static PNG/JSON pairs from the supplied packages and checked
SHA256 sums; did not execute their import scripts. New sheets use eight facing
rows and 3 idle / 3 walk / 3 attack frames. Hero effects, gear and damage tints
remain in the existing canvas renderer; summon rings and HP bars are retained.

`companion_ai.py` controls an optional normal player flagged `bot=True`:
random available hero/loadout at run start, shared party scaling, nearest-enemy
combat, normal mana/cooldown costs, hazards, reviving, loot/equipment, travel,
town votes and cooperative puzzles. A human must Share clue for its rune;
its inscription appears in a persistent HUD as well as the puzzle panel.
Bots do not inherit host, time out or keep an all-human-offline run simulating.
They reset fork navigation every visit and persist in inn checkpoints.

Host-only lobby runOptions chooses Easy (20 stages, .9), Medium (25, 1.25),
Hard (30, 1.6). Medium defaults for old checkpoints. Difficulty/totalStages
persist in checkpoint and checkpointResume metadata. All event schedules adapt
to totalStages; final dragon is last. Enemy HP/damage added factor is
1.15 * mode_multiplier * (1+.05*(stage-1)), composed once per spawn with existing
stage/party/town/elite factors. Mode attack frequency is sqrt(multiplier).
Solo normal waves: stage13 2–3,17 3–4,20+5; party increases enemy count.
Stages13–16 three waves 75%,17+ always three. Boss waves keep boss compositions.

All Ultimates now use 15s opening AND recast cooldown. Legacy mana costs are
captured before normalization (no unintended cost reduction). Druid summon
abilities retain alive locks and 8s/15s death recharge. Ten pouch slots,
compact scrollable grid, direct tool/utility swaps; phone buttons44px.
Chest rolls item/runes/heal55/25/20 after existing12% curse chance; no new items
were invented. Replaced stage exit text with an arrow.

`boss_ai.py` adds warning circles, ticking pools, slams, large shot fans and
fixed-direction charges with swept collisions. Minotaur King and Stone Behemoth
movement2.5x. Single empowered minibosses also use special attacks. Dragon phase2
revives at1.6x first maxHP,1.35x damage,1.2x speed,1.25x attack frequency and larger
art, with party meteor strikes; final kill/victory only after second phase.
Shield Bash boss stun.25s, single miniboss.55s, normal1.5s. Normal pursuit goals
update every.6–1s, bosses.75s; removed mirrored strafing. Enemy projectiles steer
for1.1s at bounded.65rad/s (boss.35); no instantaneous tracking. Offline pause
shifts all new attack/hazard/homing clocks.

Validation:70 Python regression tests passed, Node syntax/held-input checks,
936 directional imported animation-cell checks, canvas damage/summon alpha
checks. Isolated HTTP8001 preview verified lobby difficulty/NPC selection,
normal Fire Wolf cast+Alive lock, all four summons, all five newly imported
heroes, dragon phase2/warnings, full10-item tool+utility swapping and390px pouch
geometry with no horizontal overflow. Screenshots in reports/:
hero-party-update-preview.png, summons-update-preview.png,
campaign-update-preview.png, campaign-pouch-phone.png. Preview uses disposable
fixtures; production contains no QA routes. Old balance reports are historical,
not rerun under this tuning. Human balance/long-run playtesting remains useful.
No skill-tree code was implemented: user asked only for a proposal in chat.

Live activation: restarted server.py on HTTP8000; all client files and22 new
sprite PNG/JSON responses match disk. Existing inn checkpoints preserved.
Canvas verification also rendered all11 new PNGs and tested actual imported
summon damage tints with alpha preserved. Isolated preview server/tab closed;
viewport override reset. Refresh the live browser to load updated static files.

## 2026-10-06: Town characters and floating treasure chest package

Prepared `art/exports/Town-NPCs-Villagers-Floating-Chest-Sprite-Import-v1.zip`:
Merchant, Guildmaster, Alchemist, Innkeeper, eight related villager designs,
and a floating Treasure Chest. Guildmaster has regal silver/gold armor and a
purple cape with his helmet off. Innkeeper has an ordinary villager build,
ginger moustache, brick vest, teal apron and mug. Villagers share a compact base
with different clothing, skin, hair and occasional headwear.

The twelve character PNGs are transparent 612x612, 68px cells: preview row,
eight facing rows, three idle / three walk / three peaceful gesture frames.
Northwest, West and Southwest are exact horizontal mirrors. Chest is 612x136,
two nine-frame closed/open floating loops at 160ms per frame (1.44s cycle).
Vertical offsets are baked into its frames; avoid adding a second bob.
Animated PNG previews for both chest states and a twelve-character gallery
are retained in `art/town-npc-pack/` alongside all thirteen sources/prompts,
measured crop manifests, metadata, asset review and reusable art builders.

This package is prepared for import, not installed. Existing live hero, enemy
and summon imports from the campaign update remain in place. The new package's
stdlib Python importer adds an independent `static/town-sprites.js` loader,
three small hooks in the villager/service-NPC/chest draw functions, and a defer
script before app.js. It preserves labels, interaction rings and procedural
fallbacks; does not replace app.js wholesale or change server/data formats.
Existing twelve stationary villagers cycle through eight designs with varied
facings/phases. The open chest loop is supplied for future use because looted
chests currently disappear. Import directions are inside the ZIP in IMPORT.md.

Asset inspection passed for all 864 directional character animation cells:
binary transparency, padding, frame variation and exact eligible mirrors.
Chest has eighteen distinct exported cells and two nine-frame animated previews
at 160ms per frame. Importer execution and live gameplay were not evaluated in
this art task. Rebuild art with `./art/town-npc-pack/build-sheets.ps1` in
PowerShell 7; rebuild the ZIP with `python art/exports/build_town_npc_package.py`.

## 2026-10-07: Battlefield art revamp

Implemented the requested new style for all four combat regions: woodland
clearing, ancient ruined courtyard, crystal cavern and frostlands. Each uses a
full-field pixel-art background matching the imported hero sprites. Quiet flat
central ground and clear top/bottom passages keep fighting space readable;
trees, masonry, crystals and snow-covered rocks are concentrated at edges.
Scenery is decorative, with no new collision or server changes.

`static/sprites/field-woodland-v1.png`, `field-ruins-v1.png`,
`field-cavern-v1.png` and `field-frost-v1.png` are 480x270 and render at the
existing 960x540 canvas size without smoothing. `fieldArt` in static/app.js
preloads them via the existing sprite route and invalidates the terrain cache
on successful loads. `drawArenaBackdrop` reuses the cached regional background
through combat, treasure and stage-exit phases. Old procedural props are used
only if the image is unavailable, avoiding duplicate scenery over the art.
Each region has one static field; the former stage-dependent scattered props
remain only in fallback rendering. Town, fork and puzzle renderers keep their
own scenery. Existing hero, summon, NPC, chest and progression code is retained.

Source images, four exact generation prompts, relative-path manifest,
PowerShell export/gallery builder, overview preview and art review are retained
in `art/stage-fields/`. Built-in image generation used the hero-party gallery
as a style reference. Nearest-neighbor export gives a consistent two-pixel
display grid; the source drawings' literal pixel clusters remain approximate.
Rebuild with `./art/stage-fields/build-fields.ps1`. Art was visually inspected;
implementation tests and live gameplay checks were not run for this request.
Refresh http://127.0.0.1:8000/ to load the static update; no server restart needed.

## Hunter story, training, bed saves and town sprites — 2026-10-07

The latest story/tutorial request authorizes the previously proposed stat tree.
`progression.py` owns dialogue, quest, training and inn progress;
`static/progression.js` renders those flows, the clearing and upstairs guest rooms.

- A peaceful clearing follows stage 1 or 2 once, without consuming another stage.
  Speak to the wounded hunter to accept the find/kill dragon quest. Present humans
  accept and gather at the northern exit; bots accept automatically. Menu → Quest
  shows the objective. First-village runner approaches with two dialogue pages;
  all party movement/attacks freeze until present humans finish. Each present
  human then completes the innkeeper tutorial before the south gate opens.
- Four-page innkeeper tutorial opens training: three ranks each in Vitality
  (+4% base max HP), Power (+3% base damage), Focus (+5% mana regeneration),
  one point per rank. Each hero earns one point for the tutorial and one for
  each of the first two great bosses, once per run. Ranks survive Guild changes
  and use the new hero's base stats. No account-level progression or respec.
- Inn stairs lead to three rooms, one/two randomly occupied and locked. Free
  beds restore party HP/mana and set disk checkpoints. Talking to the innkeeper
  no longer restores resources or saves. Checkpoint updates apply only in the
  saved village; a later village needs a new bed save. Restore/wipe recovery
  places heroes inside the saved guest room; reconnect preserves interior
  position. Older automatic inn saves stay valid and bind to their original town.
- Enemies target only living heroes/summons. Downing their target releases
  pursuit and pending aimed boss attacks. Projectile, splash, hazard and charge
  damage ignore downed heroes; further hits cannot shorten rescue time.
  Mana recovery is 2/s combat, 6/s otherwise, before Focus (previously 4/12).
- All character/NPC/enemy/summon shadows are circles. Druid idle frames 550ms,
  walk frames 300ms with subdued bob; Bear scale 2.15 and Golem 2.5 make their
  visible art slightly taller than the combat Druid.
- Manually imported the supplied town pack: four service NPCs, eight villager
  designs, floating chest, 26 PNG/JSON files and inspected town-sprites.js.
  No package importer script was executed. Directional NPC idle/walk/gesture
  animation preserves interactions; villagers remain decorative. Chest uses
  baked floating animation and its open loop during pending loot; existing
  rewards/curses/full-pouch behavior stays intact. server.py serves both new JS files.

Validation: 82 Python regressions passed, including legacy migration and disk
bed recovery through the state API. Node held-attack/936 animation-cell checks,
actual-PNG damage/alpha tests, 864 NPC/villager cells and 18 chest frames passed.
Isolated browser QA covered hunter quest, runner, tutorial, training purchase
(Druid HP 80→84), stairs, bed save and floating chest healing. Console clean.
390×844 training fits without horizontal overflow and has 44px action buttons.
Saved previews in reports include town, training, phone, guest rooms and chest.
Temporary port-8001 server stopped; viewport override reset. Functional checks
do not replace human multiplayer balance or physical-phone playtesting.

Activated Python changes on port 8000. Existing checkpoints were backed up under
data/backups/before-hunter-update-* and stayed byte-identical. All 32 client and
NPC/chest live static responses match disk. Refresh to load the client; start a
new run for the early story/welcome. Historical notes above predate bed saves.

## Human votes, compact dialogue and no downed countdown — 2026-10-07

- `_voting_players` includes connected humans only. Town exits, physical fork
  voting, direct route actions and departure/rejoin checks use that group.
  NPC/stale offline votes do not affect route totals, majority or host ties.
  Human votes resolve immediately without waiting for the companion's position.
  Stage/peace exits also require humans only. No-human rooms cannot advance.
  NPCs still count in combat difficulty, party slots, chest loot and puzzles.
- `activeVoterCount` drives fork/stage HUD denominators; town vote totals and chat
  readiness counts are human-only. Leaving town clears interiors/dialogue for
  the entire party and carries the companion into combat with the humans.
- Story dialogue is a bottom panel, max 540px wide / 300px tall (280px phone cap),
  with a lighter backdrop. All dialogue pages and server-owned movement locks
  remain. Browser QA: 540×181 desktop panel; 352×194 at 390×844, no horizontal
  overflow, 44px Continue button. Screenshots: reports/compact-dialogue-preview.png
  and reports/compact-dialogue-phone.png.
- Removed the downed expiry mechanic and HUD countdown. Allies remain downed
  indefinitely while someone is alive, including when old timer values exist.
  Party wipe still occurs if everyone goes down. Manual revive channel remains
  1.8s (Healer 0.8s); instant revive abilities still work. HUD says Needs revive.
  How-to-play text updated. Deaths count actual wipes, not downing or waiting.

Validation: 89 Python regressions passed, including six human-vote cases and
late revival after a 60-second wait. Client syntax and held-attack/936 animation
cell checks passed; compact dialogue verified on desktop and phone browser.

Follow-up in the same update: stages 1–6 have a 10% three-wave chance for every
party size, otherwise two waves. Stage 7+ retains existing party/late-stage rules.
The state API provides a per-viewer chest.opened value derived from that hero's
decision or pending chestReward; the renderer uses it instead of shared
runesAwarded. A teammate opening/looting never opens another player's chest art.
The new regressions cover exact probability boundaries and separate views for
unopened, pending-full-pouch and claimed shares; 91 server tests pass.
Node client regression also verifies personal chest rendering when shared Runes
have already been awarded. Activated on the live port-8000 server; checkpoint
backups retained under data/backups/before-vote-chest-update-*. All four updated
client responses match disk. Temporary dialogue preview server stopped and its
browser tab removed; phone viewport reset.

## 2026-10-07: Fork screens match the previous region

Implemented four regional fork backgrounds: woodland, ruins, cavern and frost,
matching the corresponding battlefields. `drawForkBackdrop` in static/app.js
selects `room.region`, which game.py already preserves throughout stage exit
and the fork. Destination region is assigned only in `_advance_stage` after
route selection, so both branches show the area just left without revealing
future scenery. No server, progression, save format or route-voting changes.

The new `static/sprites/fork-REGION-v1.png` files are 480x270, displayed at
960x540 without smoothing. A separate fork canvas caches them and invalidates
on artwork loads. While unavailable, the current region's battlefield and
region-colored procedural paths provide the fallback. Existing signs, names,
edge votes and Lens hints remain dynamic; signboards have simple pixel trim,
and dark label panels keep text legible over the frost background.

`art/fork-fields/` retains four generated sources, exact prompts, layout guide,
relative-path manifest, export/gallery builder, preview and art review.
Built-in image generation used the canonical fork guide and each battlefield
as layout/style references. Sources had approximate path widths/positions;
the exporter clears the exact walking corridors using trail textures sampled
from the generated art. Manifest coordinates match FORK_PATHS, with 108px-wide
roads, rounded joins/caps and a subtle outer trim. Scenery adds no collision.
Rebuild with `./art/fork-fields/build-forks.ps1`.

Artwork was visually reviewed, including canonical exported paths and clear
stem/side exits. Implementation tests and live gameplay checks were not run
for this request. Refresh http://127.0.0.1:8000/ to load the static change;
no server restart is needed. Battlefield, town, puzzle and hunter art remain
as currently implemented.

## 2026-10-07: Complete equipment and utility icon set

Created individual pixel-art sprites for every equipable ITEMS entry: 22 total,
13 tools (10 weapons, 3 armor) and 9 utilities. Catalog was extracted from
game.py using AST/literal_eval without importing the game or touching rooms.
Complete names, rarities and existing effects are retained in
`art/item-sprites/ITEM_CATALOG.md` and catalog.json. No new items or stat changes.

`static/sprites/item-KEY-v1.png` files are 64x64 transparent cells with artwork
uniformly fitted to a maximum 48px footprint. Nearest-neighbor sampling and
binary alpha give crisp edges. `item-icons-v1.png` is a 384x256 atlas, six columns
and four rows, with two empty cells; `item-icons-v1.json` maps every stable key
to its rectangle, filename, name, type and rarity. Original pixel clusters and
color palette remain approximate. All 22 final sprites were visually inspected.

`createItemSprite`/`decorateItemLabel` in static/app.js add sprites to quick
pouch items, equipped slots, merchant stock, town inventory, pending chest loot,
swap choices, route-lens action and utility hotbar. Item names, descriptions,
prices, action buttons and keyboard behavior are preserved. Unknown/missing art
keeps text, and the hotbar restores its former symbol on image failure. Icons
are decorative for accessibility because adjacent names identify the items.
CSS uses 32px icons and 24px in compact equipped slots/phone hotbar; text retains
compact truncation and expanded wrapping. Existing on-character gear overlays
are unchanged. No Python/server/save changes or restart required.

`art/item-sprites/` retains all 22 sources and exact prompts, the immutable style
reference, manifest, catalog, gallery, PowerShell builder and asset/export
reviews. Built-in image generation used one call per item with transparency.
Rebuild via `./art/item-sprites/build-items.ps1`. The complete art handoff is
`art/exports/Equipable-Items-Sprite-Pack-v1.zip`, recreated by
`python art/exports/build_item_sprite_package.py`. This ZIP contains art/source
files and metadata, not an automatic importer or whole client replacement.
Sprites are already integrated into this project; refresh the browser to load
them. Implementation tests and live gameplay checks were not run for this
request; art/export inspection does not establish live UI behavior.

## 2026-10-07: Environmental combat, roles, balance and conversation HUD

Implemented the four newly selected improvements, plus subsequent dialogue,
utility placement and companion AI requests. Preserve all imported art hooks.
`combat_environment.py` owns stage-local cover, traps, poison and frost ice.
Crates/rocks block swept movement and projectiles (the nearest collision wins),
take Light/AOE damage and remain broken between waves. New stages regenerate
them using a room terrain seed. Poison affects living actors once/second, and
traps have .75s warnings/4s rearming. Enemy terrain damage is nonlethal so players
receive kills. Ice blends velocity, including release momentum. Summons and
foes detour around cover; dash/strike/blink no longer tunnel through it.

`enemy_roles.py` assigns family roles: minotaur charger, serpent ranged,
wolf/spider ambusher, troll bruiser; the last ordinary enemy in groups of 3+
can become support, excluding assassins. Supports heal one wounded living foe
after a warning. All roles commit to windups and recovery, use independent
movement decisions and cancel attacks aimed at downed targets. Empowered/boss
enemies retain boss_ai patterns. Boss timings are fixed 1–1.5s windups and
1–1.5s recovery (charges add their .7s travel), with locked charge endpoints,
shot fans, danger circles and recovery labels. Charge speed caps at 420.
`static/combat-environment.js` renders these overlays over the regional artwork.
It tolerates old server attack state while waiting for an upgrade restart.

Companions now predict incoming projectiles, escape marked ground/charge danger,
alternate .65s dodge commitments, sidestep periodically, kite when ranged and
crowded, and choose short cover waypoints. Normal speed/stats/damage still apply.
Immediate danger interrupts a revive attempt. All new clocks participate in
disconnect pause/resume so warnings, recovery and dodge timers cannot expire offline.

Balance: preserve 90%/200% Light damage and 8/15s death recharge. Bird HP40 and
interval1.15; Wolf65/1.15; Bear125/1.4; Golem170/1.8. Live summon attacks recompute
their equipped Light contribution so temporary boosts expire. Stuns gain1.8s
resistance; normal stun.6s, mini.55, boss.25. Healer Gentle/ Major Mend now target
one injured ally. Empty healing casts do not consume mana. Expired wards no
longer keep stale mitigation. Telemetry v2 records actual healing/revival HP,
ward HP saved credited to caster, and captured projectile/bleed boost assistance.
Boost assistance overlaps attacker damage; never add those totals together.
Run stats/UI/download still show only five overall fields.

`tools/balance_probe.py` runs198 cases for all heroes, sizes1–4, stages1/8/16,
two seeds; solo Wolf/Golem extras. `--before-tuning` substitutes old summon/stun
constants only inside its process. Matched JSON and readable findings live in
reports/. Initial90-case old-combat baseline is retained separately. Fresh base
gear/no training and limited seeds mean this is not a final balance claim.
24/66 cleared stage-one simulations ended before the15s opening Ultimate timer;
keep that timer as requested and validate further with humans.

Story dialogue uses two compact panels: player left, NPC right, facing sprites
and corresponding text/response. All original acknowledgement/quest/training
rules remain. Utility icons flank central E interaction (1 left,2/3 right),
retain accessible names/tooltips and click/tap/keyboard use. Six-page optional
guide includes environmental gameplay. Browser checks at1280x720/390x844/844x390
verified conversation layout, reachable landscape responses and actual mana
utility consumption. Screenshots in reports/.
111 Python regression tests and client/town sprite checks passed at this point.
Server was restarted on port8000 after the user explicitly authorized ending
their unsaved stage3 Druid/companion run. Existing CEVKC/UTAE4 bed checkpoints
were copied to `data/backups/before-combat-update-20261007-.../` before restarting.
Live HTTP smoke confirmed the new script200, a scaled two-member combat room,
three cover objects/two terrain zones, role assignment and15s opening Ultimate.
Refresh the browser to load the updated client. Temporary QA servers/tabs are
closed after verification; the normal server remains running.

## 2026-10-07: Themed villages, house interiors, hunter road and UI refresh

Village rendering now follows the previous area's `room.region`, matching the
woodland, ruins, cavern and frost battle/fork art. All six existing building
roles have distinct exteriors in every theme: inn, store, alchemy lab, guild,
cottage and lodge. Their original six roof colors remain available through
deterministic recoloring (144 exterior variations). Names and shuffled layouts
remain server-owned. Ground and the original 44/30px roads are cached at half
world resolution, using the matching fork trail texture. Building silhouettes
fit the existing collision footprint; doors retain their existing coordinates.

Every theme has six distinct furnished downstairs interiors, an upstairs inn
background, and tree/gate/bed/stair/open-door/closed-door props. Caverns use
luminous mushrooms in place of trees. Upstairs floor textures and windows are
assembled on the authoritative three-room plan. Beds have three quilt colors;
doors, occupied rooms, save prompts and stairs remain dynamic. Frost exterior
props retain snow while indoor stairs/doors were corrected to clean surfaces.
The wounded hunter now has four themed road/clearing backgrounds, with the
central 108px trail and open exits; NPC, bandage and quest interaction remain
separate. No new collision, mechanics, save format or Python changes.

Runtime art is `static/sprites/village-REGION-KIND-v1.png` (28 files), plus
eight `portrait-HERO-v1.png` menu images cropped from current hero idle sheets.
Client integration is in static/app.js and static/progression.js. The previous
procedural drawing remains as a loading/missing-art fallback. Refresh the HTTP
game page; no server restart is required for this update.

The requested follow-up UI pass is implemented in static/style.css, app.js and
index.html: entry/party menus, hero and ability selection, chat, HUD, meters,
utilities, compact/expanded pouch, equipment, merchants, loot swaps, route and
puzzle panels, guild, training, story/quest/guide/settings/stats dialogs and
victory/defeat views use timber/slate/brass/parchment styling. Actual hero
portraits replace class glyphs. Pouch items have larger icons, textual rarity
and matching border accents, equipment captions and an informative empty
state. IDs, actions and keyboard behavior are retained. Existing recent HUD
utility/interaction placement and compact dialogue portraits are preserved.

`art/village-art/` retains 24 built-in image_gen originals/specifications,
three corrective edits and their originals, references, manifest, PowerShell export
and preview builders, workflow, UI scope and art/export review records.
Sources have approximate pixel clusters/palettes; exports use nearest-neighbor
sampling and binary alpha for sprites. Atlas bleed is removed by component
filtering, roof recoloring preserves shading, woodland/ruins floor plates were
corrected to a single biome throughout, and backgrounds use generated
textures. Rebuild with `./art/village-art/build-villages.ps1`, then
`./art/village-art/build-previews.ps1`. No API key or fallback CLI was used.

Artwork and export geometry were inspected. Implementation tests and live
gameplay/UI checks were not requested or run for this change; those remain a
separate validation step. Preserve the existing Python/server/client design
and data/checkpoints when transferring this project.


## 2026-10-07: Deliberate encounters, controls, length selector and Dracos

Implementation follows the user's continuing combat/control update and newest
Draco enemy request. Preserve the concurrent imported battlefield/effect and
village/UI artwork; these changes use those existing sprite hooks.

New files: static/movement.js, combat_encounters.py,
tests/test_deliberate_combat.py, tests/test_dracos.py, tests/test_movement.cjs,
tools/audit_difficulty.py, and reports/COMBAT_UPDATE_VALIDATION.md. The movement
script is registered in server.py and deferred before app.js. Its browser
initialization is guarded for the still-running older server until activation.

Local movement prediction replays normalized direction history against server
position/speed/slide state, reconciles small errors over 100ms, snaps larger
teleports and stops after 250ms without a snapshot. It matches cover/ice,
town/interior/locked-room and fork collision. Server movement remains authoritative.
Polling targets 50ms including request/render time. Input sends are coalesced,
sequenced and release-safe; stopRevive now cancels human revive channels.

Terrain is one or two widely scattered breakables and one random trap/poison/
(frost-only possible ice) zone per stage, with spacing and open entry/exit lanes.
They persist through waves. Objective plans start at stage4, exclude scheduled
boss/mini/puzzle/town/ambush stages, have at least three stages between them and
are saved in inn snapshots. Rift: destroy structure to stop 5s reinforcements,
then clear foes. Ward: survive32s, intercept enemies from alternating edges,
then clear foes; ward destruction defeats the attempt without charging hero
death counters. Charge: sentinel plus two rocks; cover collision creates2s
recovery. Objectives use the standard damage/projectile/target/finish systems.
Ward is a combat target outside the hero/summon roster. Offline clock shifting
includes objective spawn/deadline. Checkpoint restore defaults old saves safely.

Normal enemy groups introduce Dracos at STAGE17 (confirmed by the user), rather
than global wave17. Base HP124, damage7, speed108–126, all ordinary scaling still
applies. Per-enemy25% introduction roll, maximum min(3,active party size) per
wave. Dracos keep their own role; supports are chosen from other families.
Assassin generation explicitly excludes Dracos and objective reinforcements
clone an ordinary foe. Dracos alternate a300-speed, radius8, turnRate.3 projectile
and a55-range bite; .35/.4s wind-ups, .25s recovery,1.25s base attack interval
with existing capped rate scaling. A bite can miss; it still advances the cycle.
Downed targets are excluded and cancelled pending attacks retarget normally.
Existing dragon-idle/windup sheets render Dracos at1.25 scale versus hero1.65,
ordinary enemies1.5 and larger bosses. Warnings show SHOT/BITE and aim/range.
CHARACTER_ROSTER.md is updated.

Optional target preference: click/tap a foe, Tab cycles, Escape/Clear restores
auto. Server selection prefers that foe only when legal for the attack, falling
back for range/cover. Input carries preference to avoid click/attack races.
Summons retain nearest-enemy AI. Local hero and selected target have clear
markers; ordinary combat names/permanent role panels and attack-range fills
are reduced. Danger wind-ups and health remain. The exit rectangle is removed
while preserving the earlier requested arrow.

Compact pouch hides unused utility/tool slots; Expand exposes all. Always show
a dedicated curse sprite/name/stages slot (or placeholder), outside ten carried
spaces, using curse-sluggish/weakened/frail-v1.png. Existing expanded curse
status is retained. Chest notice mojibake is fixed, with a guarded client repair
for the older server. Main-menu exit explains current in-memory Continue versus
persistent upstairs bed checkpoints and permits cancelling. Optional guide is
six pages, including new objectives and target preference.

Challenge and campaign length are independent: Easy.9/Medium1.25/Hard1.6 and
Short20/Standard25/Long30. runOptions captures values before disabling selectors;
renderClasses does not reset them while a request is pending. Explicit stages
mark lengthChosen; later challenge-only API edits preserve it. Legacy clients
without any explicit length keep their earlier default mapping. Inn snapshots
persist lengthChosen. The user's stuck-Long bug is caused by the older active
Python backend still coupling Hard to30; it is fixed in source and isolated HTTP
and browser checks, and requires production restart.

Town pressure increments smoothly: new town arrival history gives half a visit
on the next combat stage, a full visit on the following stage, preserving eventual
+25%HP/+20%damage/+10%speed/+12%attack rate per visit. Legacy checkpoints without
arrival history retain their accumulated pressure. Telemetry now captures
challenge/length/town visits/route pressure/town arrival history. The audit
reports81 generated schedules and53 historical stage observations (unverified
provenance, no old contextual metadata); it cannot establish human balance.
Stage17 composition and group size are explicit audit concerns. Required human
solo/multiplayer and physical-phone testing stays in the backlog and report.

Validation:129 Python tests pass; Node held-input, movement, damage/alpha,
936 hero/enemy/summon cells and864 NPC/villager cells/18 chest frames pass;
JavaScript syntax passes. Isolated HTTP tested nine challenge/length pairs,
simulated two-member synchronization, disconnect/reconnect and stale movement
release. Browser checked1280x720 and390x844, actual Draco rendering/wind-up,
ward HUD, selection/clear, session exit/cancel, length persistence and curse
art. Phone compact pouch272px, no horizontal overflow. Existing portrait canvas
aspect distortion and physical-phone comfort remain outstanding. Isolated scene
average draw time~.30–.34ms; limited local measurement, not a general benchmark.
See reports/COMBAT_UPDATE_VALIDATION.md, DIFFICULTY_AUDIT.md and PROTOCOL_CHECK.md.

Activation status at this entry: source complete and tested; production Python
server on port8000 has not been restarted. RoomAAT4A is at stage1 exit without
an inn checkpoint; explicit confirmation to discard that run and restart was
requested. Preserve data/checkpoints and back them up before an approved restart.
Static files need refresh, but movement.js and new APIs require the backend
restart. The previous server session ID is6629. Temporary QA server28722 on8001
and browser tab21 are cleanup-only fixtures, not user runs.


## 2026-10-07: Tester mode and automatic restart authorization

The user explicitly said not to ask permission for server restarts moving
forward. This is standing authorization for updates; it is recorded in AGENTS.md.
Back up bed checkpoints before restarting, then activate and check the server.
Do not re-ask solely because live rooms reset. Both CEVKC/UTAE4 checkpoint copies
were verified before the Draco restart in data/backups/before-dracos-update-
20261007-172623, with SHA256 manifest. A further backup before Tester activation
is data/backups/before-tester-update-20261007-173949.

Dracos/control/objective/independent-length updates were activated, then Tester
mode was added and activated in a second automatic restart. Normal server now
runs on port8000 (exec session99711); source and running backend agree. Temporary
QA servers30557/28722 are stopped; the later Tester preview40959 is cleanup only.
Previous unsaved live roomAAT4A resets under the user's explicit authorization.

Temporary Tester is a Run length option9, independent of difficulty/companion,
kept until the user requests removal. Its physical stages1–9 map to standard
25-stage progression1/4/7/10/13/16/19/22/25 through GameWorld._effective_stage.
This drives stage ramp, per-stage strength, normal group size/Draco threshold,
stage wave count, terrain damage and objective HP. Schedules are explicit and
non-overlapping: miniboss2, bosses3/6/9, town4, puzzle5, objective8. No assassination
roll in Tester; scarce normal stages stay available for the requested content.
Late ordinary waves guarantee the first Draco at Tester stage7, while normal
campaigns keep stage17. Normal cooldowns/story/tutorial/summon/vote rules remain.
Mode derives from totalStages==9, already saved in bed snapshots. State adds
 testerMode/balanceStage; HUD shows TesterN/9; lobby describes compressed pacing.
Telemetry records those fields to distinguish fast tests from ordinary runs.

134 Python regressions pass, including five Tester checks for repeated schedules
on all difficulties, reference25-stage stat equivalence, early late-game groups
and three-wave stages/Dracos, disk bed recovery and an accelerated actual wave/
boss/puzzle/inn-transition test that finishes after both dragon phases at9. That
test fast-forwards damage/time and is not human balance evidence. Existing Node
checks pass and browser confirmed Tester9 sticks on changing toHard, then starts
with Tester1/9 and15s Ultimate. Live HTTP confirmed Tester9 accepted and preserved
on a challenge-only edit. Audit expanded to108 curves including Tester; physical
phone/human balance checks remain outstanding.

User additionally requested a ZIP of the latest game and a new commit to their
The-Gauntlet GitHub repository, explicitly invoking GitHub. The local Git repo
has no commits/remotes and no configured author. Plugin management confirms
GitHub installed/enabled, but no repository connector tools are exposed in this
chat's available tools. Git credential manager has no non-interactive GitHub
credential, and the in-app GitHub browser is signed out. Repository URL was
requested; no URL is assumed. Package preparation continues independently of
that access step. Private data/checkpoints must remain excluded from GitHub by
.gitignore; preserve them in the local transfer ZIP.

## 2026-10-07: New workspace and portable handoff

The user switched this chat to `The gauntlet` and requested running the game
there. Its initially empty working folder was populated from the verified
Dracos/Tester source-art ZIP: all 879 file hashes matched, including the two
existing bed checkpoints. The game now runs from this folder on port8000
(exec session58290); the HTTP page and app/movement/combat/style assets return200.
The live browser was opened through Codex. The older laptop folder remains intact.

The repository is https://github.com/Nael-Shakhsheer/The-Gauntlet, default branch
main. The connected GitHub plugin now exposes repository tools and confirms
the owning account has push permission. Its prior contents are README.md and an
older ZIP. Publishing is prepared as runnable source and all runtime sprites,
preserving the existing archive/history. The separately prepared playable ZIP
includes all game code and runtime sprites; it excludes private checkpoints,
balance logs, large original art projects and screenshot reports. The full local
source-art ZIP retains original artwork and the saved bed checkpoints. Both
packages have per-file hash manifests and archive verification. The earlier full
package passed all 134 Python regressions after extraction. Publication is not
complete until the branch head is verified against the new commit.

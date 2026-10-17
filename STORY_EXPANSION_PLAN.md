# Adventure story expansion proposal — 2026-10-13

Design proposal, not implemented gameplay. Based on the current Adventure code,
October 13 handoff, Rootwater passage, Briarwatch tower and Oakvale portal/save systems.

## Direction

Expand Oakvale's woodland into a regional mystery about failing water, displaced
people and a broken protective network. Continue into Dunmere, a farming basin
whose harvest is dying. Preserve the existing dragon, burned watch, shrine guardian
and Labyrinth Minotaur King; connect their actions rather than replacing them.

Borrow Grim Dawn's broad quest structure: a central journey, optional requests
from people along it, discoveries worth investigating and clear completion facts.
Do not copy its characters, dialogue, factions or plot. Official references:
https://www.grimdawn.com/guide/gameplay/questing/ and
https://www.grimdawn.com/guide/items/the-hunt-for-loot/.

## Core story

Oakvale's grain deliveries stopped before the dragon attacked. Wildlife now abandons
the deep woods, the brook runs cloudy, and travelers blame one another. The missing
hunter investigated a supply caravan, witnessed the dragon strike an ancient watch
seal and fled wounded. He knows what happened locally, not the entire explanation.

The woodland shrine and old ruins were parts of a network regulating an underground
spring. Its custodians have become hostile after the watch seal broke. Defeating
the Minotaur secures the woodland, but a recovered register reveals that Dunmere's
pumping works were drawing far more water than the network could supply.

The dragon did break the seal. Later evidence suggests it was hunting something
underneath it. This is a question to follow, not a reveal that excuses the attack.
Ashen Ridge remains the dragon's eventual destination. Dunmere lies on the road
toward it and is the immediate next chapter.

NPC working names: Mara, Oakvale's runner; Edda, the innkeeper; Corin, the injured
hunter; Sella, a displaced farmworker; Tovin, Dunmere's millwright. Reconcile with
any established names before implementation. Each has incomplete knowledge and
a practical need. Introduce them through short exchanges, not one opening lecture.

## Geography and size

Grow from eight outdoor areas to twelve, including Oakvale. Keep current area IDs
and add four authored locations: brook, logging yard, hollow and border road.
Increase meaningful routes and points of interest before enlarging every canvas.
Only scrolling exploration spaces need larger dimensions; fights need readable
arenas, safe approach points and space for all four players.

Proposed graph, with existing routes preserved:

- Oakvale -> Southern road -> crossroads -> hunter clearing -> shrine.
- Crossroads -> abandoned camp -> bridge -> old ruins.
- Road <-> brook <-> crossroads: optional loop and early water evidence.
- Camp <-> logging yard <-> bridge east bank: supplies, refugees and another loop.
- Clearing <-> hollow <-> shrine: optional grove and a local elite encounter.
- Old ruins <-> border road -> Dunmere gate: chapter transition.
- Rootwater retains its road-to-clearing exit. Briarwatch retains camp-to-bridge exit.

Existing physical river restrictions still apply to new routes. A visible trail
must not accidentally bypass the broken bridge or a sealed boss encounter.
The border road is discoverable before the finale, but passage requires the
woodland's main-story completion. Explain the barrier through danger and damaged
works rather than an unexplained invisible wall.

Every new exploration area needs a recognizable landmark, a purpose, at least
one worthwhile optional find, and a route or shortcut. Avoid blank travel acreage.
Initial pacing targets, to validate with ordinary builds: first useful quest
result within 5–10 minutes; main woodland path 45–75 minutes; optional exploration
adds 20–40 minutes. These are design targets, not measured current playtimes.

## Woodland main story

| Quest | Objective and clear condition | Story/result |
|---|---|---|
| Empty Stores | Speak to Mara and inspect the abandoned caravan manifest on the Southern road. Both persistent facts complete the step. | Missing grain shipments make the search relevant to Oakvale. |
| The Missing Hunter | Inspect the tracks, defeat the named encounter guarding Corin and speak to him. Record rescue and show him safely in Oakvale. | Keep the current rescue abstraction; do not introduce fragile escort AI. Corin describes the burned seal. |
| A Road Worth Keeping | Recover the camp repair kit and install it at the bridge workbench. Guard defeat permits the chest; it does not itself complete bridge repair. | Restore a physical shortcut and the route for supplies. |
| Water Without Light | Inspect the brook's marked spring outlet, solve the existing shrine puzzle and defeat its guardian. Restore the altar after victory. | Brook observation explains why the shrine matters; restoration changes the visible water locally. |
| The Broken Watch | Collect the route register at the watch and inspect the ruins entrance seal. The shrine restores access and Corin identifies the register. | Show where the evidence points before the final fight. Keep these interactions brief and on the existing route. |
| Beneath the Old Stones | Defeat the Labyrinth Minotaur King and inspect the exposed sluice register. | The woodland threat ends, and the register connects it to Dunmere's water demands. |
| Grain Road | Deliver the register to Sella/Mara and speak to the border watch. | Open Dunmere; keep optional woodland content available. |

The hunter, bridge and shrine retain their existing required roles. Brook evidence
can be found before the quest is offered; existing facts advance it automatically.
Mandatory information stays on the main route. Rootwater and Briarwatch add
explanations and rewards, but neither is required to understand or finish the story.

## Optional woodland quests

| Quest/location | Exact clear condition | Reward/consequence |
|---|---|---|
| A Place at the Fire / camp and yard | Speak to two stranded workers, clear the specifically marked yard approach group, then establish a shelter at its supply point. | Supplies and named survivors later appear in Oakvale. No random population counter. |
| Letters That Never Arrived / road and yard | Recover three fixed, uniquely identified letters and deliver them to Edda. | A personal account of the stopped trade; consumable choice. Letters found early count. |
| The Last Dry Seeds / yard | Recover one sealed seed chest and choose Oakvale's reserve or Sella's Dunmere caravan. | Same-value immediate reward; different NPC arrival and small optional Dunmere follow-up. Neither choice blocks the main story. |
| What the Water Took / brook | Find the marked damaged wheel and retrieve its upstream spindle after defeating its guarding group; return it to the millwright's apprentice. | Reopens a local supply stall with ordinary useful stock. |
| The Surveyor's Debt / Rootwater | Read the existing survey marks, find the alcove's stamped ledger and return it to the runner. | Context for the old spring network and one personal gear choice. Retain existing cave claims separately. |
| No More Watchfires / Briarwatch | Clear the existing tower floors and take the captain's signal token from the summit; activate the signal mechanism. | A permanent beacon landmark, tower reward and a Dunmere patrol dialogue variant. No fabricated tower repeat waves. |
| Roots Around the Hearth / hollow | Inspect the abandoned cottage and destroy three authored root anchors, then interact with its freed hearth. | Opens a small treasure cellar; use existing dungeon patterns for its one encounter. |
| The Hunter's Promise / Oakvale after rescue | Return Corin's marked keepsake from the watch and speak to him after he reaches home. | A short personal resolution and support-oriented reward. |

Offer the first three or four during the initial expansion. Add the others after
the main chapter plays well. Do not show eight quest markers immediately at spawn.
Limit turn-in journeys by clustering tasks and using the existing safe portal.

## Dunmere: failing cropland

Visual identity: pale wheat, green drainage weeds, cracked earth, abandoned furrows,
idle windmills, grain stores and low cloud. Healthy strips survive near working
ditches. Show neglect and desperation before overt corruption. Preserve strong
enemy and danger-cue contrast against yellow/brown ground.

The farmers' emergency harvest additive initially helped exhausted soil, but it
was made with material carried up from the old pumping tunnels. The additive fed
a root infestation while excessive pumping weakened the woodland spring network.
The grain steward concealed the risk to avoid losing the remaining food supply.
Workers and farmers disagree over blame; they have understandable interests.

Do not reveal all this on entry. The first evidence suggests drought, then blocked
water, then an unusual blight. Records and underground investigation connect it.
No new faction reputation economy is needed for the first slice.

First playable slice: border road, Dunmere gate/hub, west fields and ruined mill.
The hub has a working bed/recovery point, map location and discovered portal
destination. Complete the current region-aware recovery and travel plumbing before
adding a second hub; do not assume Oakvale-only routines support it already.

| Opening quest | Required facts | Result |
|---|---|---|
| The Harvest That Never Came | Meet Tovin; inspect three marked field sites: dry ditch, rooted crop and empty granary. | A specific cause to investigate, rather than a generic kill objective. |
| Water for the Living | Defeat the mill approach group, clear two named channel blockages and operate the intact sluice lever. | Water visibly reaches one field; a worker returns to the hub. No whole-region instant recovery. |
| Under the Mill | Enter the granary cellar, defeat the Blighted Overseer and recover its additive ledger. | End the slice with a resolved local threat and a lead to the pumping works. |

Two starter side quests: retrieve medicine from a guarded farmhouse for the hub's
injured workers; recover a fixed seed sack and deliver it to the recipient chosen
in the woodland. If the player never did that woodland side quest, offer a local
version with its own clear reward instead of making it unavailable.

Later cropland expansion: orchard, irrigation channels, abandoned farmstead,
grain depot and pumping works. Underground dungeon: sluice tunnels that exit
beyond the blocked canal. Tower dungeon: a watch silo with a distinct wave mix
and summit escape. Regional finale: destroy the three pumping root hearts and
defeat the Harvest Warden. Repair produces limited signs of recovery, not full
healthy crops overnight. The dragon trail then continues toward Ashen Ridge.

First-slice enemies should reuse supported combat roles with distinct readable
variants; add one authored elite and its anticipation/release behavior. New enemy
art and animation can follow once encounters are balanced. Do not populate every
farm space with generic woodland wolves or expose prototype art as final assets.

## Quest, party and save rules

- Use explicit named stages: unavailable, offered, active, ready-to-turn-in,
  complete. Evidence and kills can occur before acceptance and must reconcile.
- Store stable world facts such as inspected clue IDs, defeated encounter IDs,
  installed repairs and committed story choices. Derive journal instructions from
  those facts. An arbitrary count or dialogue index must not substitute for them.
- World objectives are party-shared. Rewards and resolved receipts are personal,
  offered once per eligible character. Late joiners receive the world recap and
  eligible unclaimed rewards without duplicating shared currency or world events.
- Present one tracked goal, its location, current step and visible progress.
  Explain blocked objectives by their actual prerequisite. Separate optional work
  from main-story gates, and let players review missed dialogue.
- Only major irreversible story choices require a party vote. Connected humans
  gather and vote; companions and offline players cannot block it. On a tie, leave
  the choice undecided and allow retry. Do not auto-commit on disconnect or timeout.
  Routine clues, turn-ins and repairs do not require repeated approval/voting.
- Quest objects do not take ordinary inventory slots. Claim eligibility comes
  from authoritative quest facts; quest items cannot be sold or consumed accidentally.
- Rewards are useful choices through the existing reward system; avoid adding
  more mandatory training points until balance is checked. Story consequences
  should change NPCs, routes, dialogue or services, not just reward text.
- Save committed progress through current atomic/versioned storage. Recovery and
  wipe retain completions and choices. Unfinished sealed encounters restart under
  current dungeon rules. Do not allow portal travel to bypass locks or finish goals.
- Distinguish gameplay region IDs from the art palette. Dunmere requires a real
  progression region even while prototype scenery uses supported palette assets.
- Keep old area/quest/character/bed identities. Old completions are never revoked.
  An old finished woodland world can enter the new border route without repeating
  rescues, puzzles or bosses. New optional work can be offered without replay payouts.
  Reconcile portable imports, legacy records, rolling backup and cloud allow-lists.
- No implicit reset or repeat enemy spawning. The current Adventure uses finite
  authored encounters. Any future repeatable activity needs a separate design.

## Implementation order and acceptance

1. Establish quest definitions/stages and migration; preserve current woodland
   behavior. Add persistent clues, early-find reconciliation, turn-in state and
   receipts. Test duplicate actions, reconnect, wipe, export/import and late join.
2. Rewrite woodland dialogue and main objectives. Add brook and logging yard plus
   three side quests. Connect existing dungeon lore to the mystery. Play the whole
   route on ordinary stats before expanding it further.
3. Add hollow and border road; remaining selected side quests and visible outcomes.
   Verify exits, collision, map layout, portal destinations and old-save completion.
4. Build Dunmere's first slice: hub, fields, mill and short cellar, three linked
   main quests, two optional quests and a single elite. Give it a satisfying local
   ending rather than a large empty region with placeholder entrances.
5. Expand cropland only after solo and two-to-four-player pacing/recovery checks.

Use the current isolated `tools/run_tests.py`, relevant JavaScript suites and
disposable playtest saves. Check main-only completion, optional quest orders,
evidence before acceptance, absent questgiver recovery, duplicate claims, party
choices, full pouches, old completed worlds and travel between both hubs. Record
actual results and limits. Keep ordinary character stats for balance verification.

## Prompt for the implementation chat

Implement this design in staged, playable increments. Read AGENTS.md,
PROJECT_CONTEXT.md, README.md and STORY_EXPANSION_PLAN.md, then inspect the current
quest, dungeon, dialogue, map, portal and persistence code. The proposal's names
are working names; preserve any established characters and stable save IDs.

First complete phases 1 and 2: strengthen the quest model and save migration,
rewrite the woodland main story around Oakvale's supply/water crisis, add brook
and logging yard with connected trails, and implement A Place at the Fire,
Letters That Never Arrived and The Last Dry Seeds. Add short contextual lore to
Rootwater and Briarwatch. Keep the hunter/bridge/shrine/Minotaur progression and
existing optional dungeon mechanics compatible. Do not merely display future
quest text without working conditions, rewards and consequences.

All completion must come from authoritative stable facts. Handle discoveries
before acceptance, one-time rewards, late joins, connected-human story votes,
wipe/recovery, portals and portable exports/imports. Old saves retain completed
work and rewards. Preserve Gauntlet mode, current art, lazy loading, all data/
and the recent movement/recovery improvements. Load new assets only when needed.

Prepare phases 3 and 4 as the next concrete milestone: hollow and border road,
then the Dunmere hub/fields/mill/cellar slice. The cropland replaces Ashen Ridge
as the immediate destination; Ashen Ridge remains a later dragon lead. Do not
claim Dunmere is playable until its linked quests and travel/recovery work.

Run the isolated Python runner, relevant client suites and disposable ordinary-stat
solo/co-op scenarios. Document changes, migrations, exact checks and remaining
content in PROJECT_CONTEXT.md. Follow save backup instructions if server code
changes require restarting. No publishing or deployment is requested.

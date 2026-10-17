# Personal Magic Rune source ledger

Authoritative reward design, recorded before reward implementation (2026-10-14).
Magic Runes are character-bound and never replace or convert the shared shop Rune
pool. Each source ID has one receipt per character/world, including eligible late
joiners. No enemy drops, retry rewards or repeatable farming sources exist.

| Chapter | Stable source ID | Condition | Personal amount |
| --- | --- | --- | ---: |
| Woodland | shrine:brook | Clear brook shrine guards; deliberately attune | 1 |
| Woodland | shrine:deepwood | Clear hollow approach; deliberately attune | 1 |
| Woodland | shrine:watch | Inspect watch records and clear shrine guards; attune | 1 |
| Woodland | report:hunter | Rescue hunter and report accepted assignment | 1 |
| Woodland | report:bridge | Repair supply route and report accepted assignment | 1 |
| Woodland | report:shrine | Restore mechanism and report accepted assignment | 1 |
| Woodland | report:woodland_boss | Defeat Minotaur, recover register and report | 2 |
| Woodland optional | cache:dry_spring | One authored concealed cache off the hollow path | 1 |
| Dunmere | report:failed_harvest | Inspect all three field sites and report | 1 |
| Dunmere | report:irrigation | Restore channel/sluice and report | 2 |
| Dunmere | report:mill_cellar | Clear cellar elite, recover additive ledger, report | 2 |
| Dunmere | report:chapter_outcome | Deliver findings and secure the local supply outcome | 2 |

Guaranteed totals: **Woodland 8, Dunmere 7 = 15**. Woodland optional cache adds one.
All listed sources are implemented and covered by the October15 isolated quest,
receipt, migration and recovery tests. The full object/accept/report test reaches
15 guaranteed runes and performs Ascension; browser checks of the late chapter use
a clearly labeled helper-completed world, not an earned full campaign playthrough.
No rewards are granted for entering Dunmere. Future pumping-works content is not
included in this ledger or counted as implemented.

Permanent health/mana purchases each cost one unspent Magic Rune, give +5% of
unmodified class base maximum per rank (additive), and cap at five ranks each.
Ascension consumes **15 currently unspent** Magic Runes. Purchases preserve current
resource proportions/downing and all recharge; they cannot restore resources by
repeated loading, swapping class or retrying a transaction.

The currently playable total is16 including the optional cache. Spending more than
one rune on health/mana therefore prevents reaching15 unspent within this content.
The purchase preview explicitly explains that finite tradeoff; respec does not
refund permanent Magic Rune purchases. Ascension adds10% of base HP/mana and8%
damage, one class signature and two class passives. See README for current kits
and `reports/WOODLAND_EXPANSION_VALIDATION_2026-10-15.md` for verification limits.

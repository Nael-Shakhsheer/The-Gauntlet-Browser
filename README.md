# The Gauntlet — local release candidate

This candidate contains the five-region Adventure and the separate Gauntlet
mode. Primary artwork review and specific generation provenance are documented;
human multiplayer, physical-device comfort, actual listening and hosted recovery
remain separate limitations. This package does not automatically upload or deploy
anything. The menu's build label and PACKAGE_MANIFEST.json identify this package.

## Run

Install Python3.10 or newer, extract the ZIP, then open a terminal in the folder
containing `server.py` and run:

```text
python server.py
```

Open **http://127.0.0.1:8000/** in your browser. Keep the terminal running. The
playable game uses only Python's standard library; Node and art tools are not
required. Do not open `static/index.html` directly.

Choose **New Adventure**, **New Gauntlet run**, **Continue** or **Join a party**.
A new run creates a separate identity and preserves other saves. Gauntlet's
legitimate nine-stage Tester length remains available. Temporary Dev tools,
showcase, scripts, endpoints and mutation dispatch are absent from this package.

## Controls

Move with WASD or arrow keys, hold left mouse for your basic attack, Space to
dash, E to interact or hold a rescue. Adventure active slots use Q/R/F and the
ultimate uses X. Slots open through progression; Map, Journal and Skills are
available from the Adventure HUD. Selected large outdoor areas follow your hero;
Area view briefly shows the whole location. Touch controls require landscape.

Use **Menu → Controls & settings → Controls & keybindings** to inspect/remap your
actual bindings. Settings also contains sound, reduced effects and shake controls.
Menus do not pause a live cooperative world. Inspect the map from a safe position.

## Saves and recovery

Adventure saves world facts and personal progression automatically after storage
confirms success. Upstairs inn beds or appropriate sanctuaries choose recovery
points. A wipe loses15% of shared Runes once and preserves completed objectives.
Gauntlet persists only its inn-bed checkpoints. Each character has Current
Adventure, Adventure Backup and Gauntlet Checkpoint recovery slots.

Continue is tied to this browser identity and server address. Use **Save files →
Export backup** for a portable Adventure copy; import previews the record and
creates a new world after confirmation. Preserve `data/` when moving the game.
Never replace it with the empty data folder from another copy.

Local files persist on this computer. Render's free filesystem is temporary;
this build does not promise durable online saving. Optional server-side cloud
storage needs separate configuration and real recovery verification.

Back up existing saves before restarting the server. Live rooms reset; saved
progress restores at the established recovery point. Refresh clients after
updating files. The menu's discreet build label identifies client/server versions.

Public character IDs and room codes cannot recover someone else's character.
Existing private browser references and recovery links remain valid. For a native
legacy save whose browser reference has been lost, its local file owner can run
`python tools/recover_local_session.py <native-save.json> --player <saved-player-key>`.
It prints a **private** recovery link; do not share it or put it in bug reports.
For very old records without a proof, supply `--output <new-copy.json>`. Stop the
server and back up the original before installing that migrated copy in its place.
The helper never overwrites the original or an existing output; it is offline and
creates no public recovery endpoint. Use `--origin` if the game address differs.

See [credits and provenance](CREDITS.md). Authoring sources, regression suites
and audit evidence remain in the full project checkout, outside this public
runtime package.

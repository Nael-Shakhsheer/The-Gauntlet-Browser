# The Gauntlet · Bxfr audio workflow

Current controller/inventory review: October 29, 2026. The user calls Bfxr “Bxfr.” Effects retain the actual
Bfxr DSP, seeded parameters and vendor notices. The small original musical score
uses a separate editable note/instrument renderer; it does not replace Bfxr effects.
The runtime remains the Python server and browser client.

October 29 finalization leaves all 198 effect WAVs, ten score WAVs, recipes,
vendor code and licensing unchanged. The event manifest now covers all 106
current active definitions (including 24 campaign skills and eight Ascensions).
Music engagement survives actual polling, each later boss can trigger victory,
interrupted victory resumes its offset, and Cinder outdoors uses the existing
dry texture. Actual summon collisions share the quiet summon bucket; Frost
Lance's cast/launch no longer duplicate its sample. Rune ducking restores on
travel as well as its scheduled release, hide and mute. Exact final tests,
owned-file hashes and limitations are in
`reports/finalization-2026-10-28/AUDIO_HANDOFF.md`. This is source readiness for
Main's integrated checks, not publication or perceptual-listening approval.

## Rebuild and review

Run from the project folder. Runtime playback needs no Node, NumPy, editor or key.
Authoring needs Node, Python and NumPy (validated with NumPy 2.3.5):

```text
node art/audio/build-sounds.cjs
python art/audio/build-music.py
python art/audio/build-review.py
python tools/audio_inventory.py
```

Open `art/audio/review.html` locally. It contains ten tracks, representative cues
and 30/40/60-second town/exploration/combat references. It has no autoplay, plays
one item at a time and pauses on hiding. References apply conservative default
bus gains but do not reproduce live compression, spatial attenuation or timing.
`review-metrics.json` retains the schedules and measurements. `preview.html`
forwards to this review; the older `build-preview.cjs` and 12-second reference are
historical October 11 artifacts, not the current review workflow.

`sounds.json` retains 198 editable recipes, seeds, Bfxr2 parameter names and notes.
Routine rebuilding uses that file. `design-bank.cjs` and `refine-bank.cjs` are
optional authoring passes; do not routinely rerun design-bank, which resets
nonmanual tuning. Edit recipes for individual changes. New material, projectile,
interaction and Ascension cues use the same retained DSP.

All effects are mono 44.1 kHz PCM16. Current bank: 3,085,562 bytes, 36.4–833.6 ms,
peak 0.16702–0.47998, RMS -27.2 to -12.85 dBFS, zero clipped samples and zero
nonzero boundary samples. `metrics.json` contains per-file durations, size, RMS,
peak, exact silence, adjacent steps and hashes. `before-overhaul-metrics.json`
retains the 95-cue baseline. Zero endpoint samples do not prove inaudible joins;
noise steps and spectral fatigue require listening.

## Protect manual work

`exports.json` fingerprints generated/installed effects. A modified or
unregistered existing WAV aborts the build before runtime files change.
`node art/audio/build-sounds.cjs --replace-modified` explicitly backs modified
files into `manual-backups/` before replacement. Never discard those backups.
For an intentional manual Bfxr export retain both source WAV and editor data:

```json
"manual": {"source": "manual/my-cue.wav", "editorData": "manual/my-cue.bfxr"}
```

Paths must stay inside art/audio. Source WAV must be canonical mono 44.1 kHz
PCM16 with a standard 44-byte header and safe boundaries. The builder copies it
rather than resynthesizing. Keep the exact editor's data; automatic recipes use
Bfxr2 JSON parameters, not legacy serialized .bfxr data.

Music has a separate SHA preflight in `build-music.py`; intentional replacement
uses `--replace-modified` and backs up changed WAVs to `music/manual-backups/`.
`music/composition.json` retains motif, arrangements and optional note overrides;
`music/scores.json` records rendered notes. Renderer code retains the synthesized
instruments. `music/metrics.json` and `static/music/manifest.json` retain hashes,
credits, loops and measurements. Ten stereo 22.05 kHz PCM16 files total 24,507,192
bytes. Peak is at most 0.30, with zero clipped samples and zero measured loop
endpoint delta. This is a modest original synthesized score, not an acoustic
performance or a complete adaptive soundtrack. No third-party samples are used.
Permission and credits are in `music/LICENSE.txt`.

## Runtime policy

See `OVERHAUL_2026-10-16.md` and `event-manifest.json` for the audit and routes.
`feedback.py` retains at most 128 ephemeral events for three seconds. Stable
scene epoch/IDs deduplicate confirmations; no event history is saved. Successful
casts come from accepted server actions. Short-lived actual launches, collisions,
restoration, warnings and outcomes are explicit events. First load, refresh,
reconnect gaps, scene changes and hidden returns baseline silently. An accepted
critical/personal cue may finish a cold load for at most 250 ms, within the
750 ms event-age bound; travel, hiding and mute invalidate pending playback.

Distance uses the local player's world position, with quadratic falloff to zero
at 800 units and pan limited to 0.65, independent of overview zoom. Ordinary
attacks, impact packs, periodic damage and summons have shared limits. Tiered
voice limits are 6/8/10; warnings and rescue can displace ordinary voices. Effects
use gentle compression and a master overload shoulder above 0.85. Effects decode
cache is 8 MiB; four normal/six urgent loads and eight pending confirmations are
bounded. Music is lazy, at most two cached decoded tracks/32 MiB and one loader,
with stale decode results discarded. Music crossfades normally over 1.6 seconds;
combat engages after sustained activity and holds five seconds. Caravan's road
intro plays once and then its refuge section loops. Mute/hidden/disconnect/defeat
stop score sources. No idle class or per-prop sound loops are added.

Atmosphere uses quiet procedural filtered beds and sparse Bfxr accents for
village, woods, underground, tower, boss and dry areas. At most two bed sources
crossfade; nearby landmarks share one positional accent. These are stylized
textures, not realistic environmental recordings. Combat suppresses optional
accents. Existing stable scenery is preserved.

Settings persist per browser/site under `gauntlet-audio`, version 3. Defaults:
master 100%, music 16%, effects 40%, ambience 12%, UI 30%. Old effects/volume,
ambience and mute preferences migrate unchanged. Master mute stops every bus.
The settings dialog offers independent levels, previews, shake Off/Reduced/Normal
and reduced decorative effects. Device reduced-motion disables optional shake.
Essential warnings, silhouettes, health and revive targets remain visible.
Trusted gestures activate Web Audio; autoplay/storage/asset failures never gate
gameplay. Menus do not pause the world.

## Checks and local fixtures

```text
node tests/test_audio.cjs
node tests/test_audio_build.cjs
node tests/test_audio_routing.cjs
node tests/test_audio_stress.cjs
node tests/test_music.cjs
node tests/test_music_transitions.cjs
node tests/test_feedback_visual.cjs
python tools/run_tests.py --pattern "test_audio*.py"
python tools/run_tests.py --report reports/audio-python-local.json
python tools/audio_preview.py --scene cave --players 4 --port 8013 --touch-controls
python tools/audio_preview.py --scene boss --players 4 --port 8014
python tools/audio_preview.py --scene caravan --players 1 --port 8015
python tools/audio_preview.py --scene ascension --players 1 --port 8016
```

Fixtures use memory-only disposable worlds and accepted actions with ordinary
combat stats. Ascension grants fixture receipts; it is not an earned playthrough.
The broader multiplayer probe uses explicitly synthetic reliability fixtures.
Reports distinguish those from browser UI checks and real-device testing.
Before restarting the real server, run `python tools/backup_saves.py --label
audio-music-overhaul`; preserve data when transferring. Refresh clients after
activation. No publishing or deployment is part of this work.

**Actual listening remains incomplete.** Browser source playback, export metrics
and tests do not establish headphone/speaker comfort, intelligibility or musical
quality. Listen to the review and an ordinary four-person session, including
physical mobile/Bluetooth audio, before treating this as perceptually validated.
See `reports/AUDIO_OVERHAUL_VALIDATION_2026-10-16.md` for exact evidence and limits.

## Retained Bfxr licenses

Five unchanged JavaScript files in vendor were retrieved October 7 from
https://github.com/osiriswd/bfxr2-cli. `vendor-hashes.json` pins the Bfxr 1.0.4 DSP,
parameter and sample-buffer source. The isolated VM provides a seeded PRNG and
minimal AudioBuffer; square, sine, triangle and white-noise waves use no sampled
wave tables. MIT license credit to Stephen Lavelle and Thomas Vian's Apache 2.0
notice for the ported SfxrSynth code, both texts and source headers remain intact.

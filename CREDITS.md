# Credits and provenance

The Gauntlet is Nael Shakhsheer's game project, developed with AI-assisted code,
art and testing workflows. Player data is not part of the distributed game.

## Artwork

The source checkout retains the owner-supplied sprite imports, project-specific
image-generation prompts, normalization scripts, export metadata and review
ledgers under `art/`. Existing stable game/content IDs identify their integrations.
The detailed campaign ledger is `art/campaign-v1/asset-manifest.json`; the current
visual pass has additional records under `art/release-visual-v5/`.

The original Knight, Minotaur, Serpent and Wizard imports are traced to retained
PixelLab character jobs and matching generation metadata. Exact job references,
32base-model export hashes and the later project-specific production chain are
recorded in the source checkout's
`reports/finalization-2026-10-28/SPRITE_PROVENANCE.md` and companion JSON. No unknown
purchased/downloaded stock pack was identified. Additional V5 originals, prompts,
exporters and scoped reviews are retained under `art/release-visual-v5/`.

PixelLab's published [terms](https://www.pixellab.ai/termsofservice), checked
October29,2026, permit use, modification and distribution of generated outputs,
subject to third-party input rights and restrictions on training other models.
No model is distributed with this game. These records identify provenance and
provider terms; they do not grant rights over unrelated third-party inputs.
Untransferred early raw sources and one missing original Wizard actions prompt
remain reproducibility gaps, with selected outputs/metadata/hashes retained.

The embedded “Gauntlet Pixel” typeface is generated from the project's own
explicit5×7 glyph patterns and TTF-table builder in `art/pixel-ui/build-font.py`.
The generated `static/font.css` records that source and rebuild command. The
source checkout preserves this authoring workflow; this is not an imported font.

## Effects and music

Sound effects use the retained Bfxr1.0.4/SfxrSynth DSP and project-specific seeded
recipes. The vendored CLI source originated from `osiriswd/bfxr2-cli`; its MIT
notice credits Stephen Lavelle, and the ported SfxrSynth carries Thomas Vian's
Apache2.0 notice. Both texts are included:

- [MIT notice](art/audio/vendor/LICENSE)
- [Apache2.0 notice](art/audio/vendor/LICENSE-APACHE-2.0.txt)

The project-specific score, note sequences, synthesized instruments and rendered
music have a separate [music notice](art/audio/music/LICENSE.txt). No external
recordings or sample libraries are used by that score's retained workflow.

The complete source checkout keeps the editable bank, DSP sources, hashes and
rebuild scripts. These notices do not replace the game owner's decision about
licensing the game itself.

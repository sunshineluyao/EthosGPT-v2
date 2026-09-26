# Featured figure sources

The two featured figure masters are editable SVGs under
[`results/figures/`](../../results/figures/); their PDF exports are supplied
for printing. Run `make featured-figures` to regenerate the SVGs from these
scripts and archived inputs:

| Figure | Source | Inputs | Provenance |
|---|---|---|---|
| [Cultural and regional audit](../../results/figures/fig1_ethos_gallery.svg) | [`make_fig1_ethos_gallery.py`](make_fig1_ethos_gallery.py) | [`data/`](data/), including country changes, eight-region summaries, signed item gaps and scenario values; [archived vector map](../../results/figures/fig1_spatial_story.svg) | [`fig1_ethos_gallery_provenance.json`](fig1_ethos_gallery_provenance.json) |
| [Values and quality-ladder mechanism](../../results/figures/fig2_value_bridge.svg) | [`make_fig2_value_bridge.py`](make_fig2_value_bridge.py) | [`data/signed_country_items.csv`](data/signed_country_items.csv), [`data/creative_eight_region_simulation.csv`](data/creative_eight_region_simulation.csv) and the [declared simulator](../../experiments/gpt55_gpt56_64country/simulate_creative_destruction.py) | [`fig2_value_bridge_provenance.json`](fig2_value_bridge_provenance.json) |

The generated [clip-art contact sheet](clip-art-set-v2/contact-sheet.svg)
and its component SVGs are editable illustrations used in Figure 1. Figure 2
explicitly distinguishes observed signed survey comparisons from uncalibrated
decision rules and simulated quality-ladder outcomes. Do not read those
simulated values as estimates of actual growth, welfare or environmental
impact. The [featured visual guide](../featured/README.md) also links the
repository teaser and its evidence-class manifest.

## Earlier analysis figure map

The offline reproduction also runs `scripts/make_visual_story_v100.py` after
the scoring and table stages. PDF and SVG are the authoritative exports; PNG
files are previews. Existing editable vector masters and provenance records
are retained alongside the new featured pair.

| Figure | Reader task | Reproducer or editable master |
|---|---|---|
| Spatial story | Framing and evidence | [`fig1_spatial_story.drawio`](../../results/figures/fig1_spatial_story.drawio), `scripts/make_visual_story_v100.py` |
| Multi-view results | Paired inference and geography | `scripts/make_visual_story_v100.py` |
| Economic margins | Exploratory theory-indexed contrasts | `scripts/make_visual_story_v100.py` |
| Supplementary sensitivity and country views | Uncertainty, design, robustness and heterogeneous profiles | `scripts/make_visual_story_v100.py` and the source files in this directory |

Ink `#18324A`, GPT-5.5 blue `#3B5CCC`, GPT-5.6 or lower error teal
`#078C82`, higher error magenta `#B33B72`, and assumption amber `#D88A24`
form the visual vocabulary. See
[`semantic_graphics_manifest.json`](semantic_graphics_manifest.json) for
per-export lineage and dimensions.

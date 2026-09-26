# Featured, editable visual assets

| Asset | Reader task | Evidence boundary |
|---|---|---|
| [Research arc](ethosgpt_release_arc.svg) | Follow the six-stage open-science path | The schematic paired marks are illustrative; the labeled global TVD result is derived from archived data. The dashed quality-ladder band is an assumption. |
| [Figure 1: cultural and regional audit](../../results/figures/fig1_ethos_gallery.svg) | Read geographic coverage, error direction and a regional example | Country measurements and exploratory region summaries are descriptive. |
| [Figure 2: six questions and country cases](../../results/figures/fig2_value_bridge.svg) | Separate Nigerian observed signed gaps from declared adviser and quality-ladder calculations | Amber arrows and 20-round outcomes are synthetic, uncalibrated scenarios. |

All three SVGs keep live text and editable vector geometry. Vector PDF
exports for Figures 1 and 2 sit beside their SVGs in `results/figures/`.
`make featured-figures` regenerates their SVG masters from the included data;
their Python sources, source CSVs and provenance JSON
are in `assets/figure_sources/`. The research arc is the editable SVG master;
its [semantic manifest](ethosgpt_release_arc_manifest.json) records the
evidence states, palette, accessible description and component IDs.

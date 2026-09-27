# Featured, editable visual assets

| Asset | Reader task | Evidence boundary |
|---|---|---|
| [Research arc](ethosgpt_release_arc.svg) | Follow the six-stage open-science path | The schematic paired marks are illustrative; the labeled global TVD result is derived from archived data. The dashed quality-ladder band is an assumption. |
| [Figure 1: cultural and regional audit](../../results/figures/fig1_ethos_gallery.svg) | Read geographic coverage, error direction and sensitivity to three declared priority weights | Country measurements and exploratory region summaries are descriptive; the triangle is a weighted-error sensitivity, not an economic outcome. |
| [Figure 2: six questions and country cases](../../results/figures/fig2_value_bridge.svg) | Separate Nigerian observed signed gaps from declared adviser and quality-ladder calculations | Amber arrows and 20-round outcomes are synthetic, uncalibrated scenarios. |
| [Regional adviser scenario](../../results/figures/figS10_regional_scenario.svg) | Follow the African–Islamic regional case from values to arrival, quality and replacement exposure | All modeled choices and outcomes are illustrative; the released SVG retains the previous case pathway. |

All four SVGs keep live text and editable vector geometry. Vector PDF
exports for Figures 1, 2 and the regional case sit beside their SVGs in `results/figures/`.
`make featured-figures` regenerates their SVG masters from the included data;
their Python sources, source CSVs and provenance JSON
are in `assets/figure_sources/`. The research arc is the editable SVG master;
its [semantic manifest](ethosgpt_release_arc_manifest.json) records the
evidence states, palette, accessible description and component IDs.

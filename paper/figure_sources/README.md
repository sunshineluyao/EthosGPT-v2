# Figure-source contract (v1.0.0)

Run `python scripts/make_visual_story_v100.py` after the analysis and supporting table-generation stages.
PDF and SVG are authoritative; PNG is preview-only. All quantitative marks map to released CSV files.

## House style

- Ink `#18324A`; GPT-5.5 `#3B5CCC`; GPT-5.6/lower error `#078C82`; higher error `#B33B72`; status `#D88A24`.
- Nimbus Roman (Times-compatible), 8 pt target and 7 pt fail-closed floor at 5.48-inch insertion width.
- White background, restrained grid, no rainbow scale, and redundant shape/line encoding.

## Figure map

| Figure | Reader task | Evidence class | Authoritative source |
|---|---|---|---|
| Figure 1 | framing/evidence | published context, descriptive reanalysis, current evidence, and theory-guided directions | `figs/fig1_spatial_story.drawio; Python child charts: scripts/make_visual_story_v100.py` |
| Figure 2 | evidence | inferential and descriptive panels | `scripts/make_visual_story_v100.py` |
| Figure 3 | implication | exploratory theory-indexed inference | `scripts/make_visual_story_v100.py` |
| Appendix Figure 4 | evidence | sensitivity analysis | `scripts/make_visual_story_v100.py` |
| Appendix Figure 5 | mechanism | methodological/conceptual | `figs/figS2_study_design.drawio` |
| Appendix Figure 8 | implication | exploratory sensitivity analysis | `scripts/make_visual_story_v100.py` |
| Appendix Figure 6 | heterogeneity | descriptive country-level sensitivity | `scripts/make_visual_story_v100.py` |
| Appendix Figure 7 | heterogeneity | descriptive country-level profile cases | `scripts/make_visual_story_v100.py` |

See `semantic_graphics_manifest.json` for per-export hashes, data lineage, final dimensions, and scientific questions.

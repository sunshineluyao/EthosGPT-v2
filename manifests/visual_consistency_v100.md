# Manuscript-wide visual consistency audit — v1.0.0

## Result

Pass. All seven figures and the main/appendix tables follow one role-based visual
system.

| Contract | Check | Result |
|---|---|---|
| Width | Every figure is 5.48 inches wide and inserted at `\linewidth`. | Pass |
| Type | Nimbus Roman matches the Times-compatible manuscript body; 8-pt target and automated 7-pt minimum across generated SVG text. | Pass |
| Model roles | GPT-5.5 is blue/circle/dashed where needed; GPT-5.6 is teal/diamond/solid. | Pass |
| Direction | Lower/near-zero/higher uses teal-down/gray-circle/magenta-up and explicit metric-specific thresholds. | Pass |
| Statistical status | Intervals are visible; marker fill, table shading, and captions identify corrected support versus uncertainty. | Pass |
| Evidence class | Published, archived, current descriptive, inferential, sensitivity, and future-research roles are explicit. | Pass |
| Grayscale | Shape, orientation, line style, fill, outline, and lightness retain meaning. | Pass |
| Export | Each displayed asset has vector PDF and live-text SVG; no displayed SVG embeds raster content. | Pass |
| Editability | Figures 1 and 5 have parseable Draw.io masters; Figure 1 nests four regenerated SVG children. | Pass |
| Source mapping | Exactly seven displayed stems match the semantic manifest and LaTeX includes. | Pass |
| Text geometry | Relaxed-padding standalone probes find zero text-to-text overlaps in all seven figure PDFs; flagged path contacts are intended marks, axes, or connectors. | Pass |
| Tables | Header bands, status colors, decimal alignment, labels, and group spacing are shared between the main and appendix. | Pass |

Main-paper pages 2 and 4 and appendix pages 7, 16–18, and 24 were inspected at
180 dpi after compilation; all seven stand-alone PNG previews were checked at
original resolution.

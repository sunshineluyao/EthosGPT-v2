# Visual redesign report — v0.8.0

## Outcome

The six displayed figures now form one evidence sequence: geographic heterogeneity,
paired statistical synthesis, bounded economic implication, uncertainty diagnosis,
study construction, and continuous sensitivity. The former spatial Figure 5 is promoted
to Figure 1. The former Figure 1 methods graphic is simplified and moved to Appendix
Figure 5.

## Visual audit

| Prior issue | Consequence | v0.8 resolution |
|---|---|---|
| The methods diagram opened the paper before readers saw empirical heterogeneity. | The visual hierarchy emphasized protocol over the scientific result. | Country-level TVD and CRG changes now open the paper as Figure 1; the methods overview is Figure 5. |
| Figure 2 compressed heterogeneous tasks into a conventional interval summary. | Magnitude, distribution, repeated-run behavior, item inference, and profile shape were difficult to compare. | Five coordinated idioms now separate those tasks: dumbbell, raincloud, slope, lollipop, and radar. |
| Economic point estimates, intervals, and weight robustness did not read as one argument. | Readers had to infer how the three evidence levels related. | Figure 3 aligns model slopes, paired BCa lollipops, and the interval-classified weight simplex. |
| Conditional uncertainty sources were not visually normalized to the primary uncertainty. | Narrow conditional intervals could be mistaken for replacements for country inference. | Figure 4 first expresses conditional SEs as percentages of country-bootstrap SE, then aligns three TVD intervals. |
| Diagram language was dense and implementation-led. | The methods figure was harder to scan than the surrounding prose. | Figure 5 uses four plain-language stages and an explicit solid/dashed evidence boundary. |
| Continuous weight sensitivity lacked a clear interval boundary and equal-weight landmark. | Point and inferential conclusions could be conflated. | Figure 6 separates the equal-point-loss contour, 95% interval boundary, and equal-weight marker. |

## Visual blueprint

| Figure | Reader task | Evidence class | Primary encoding | Source |
|---|---|---|---|---|
| 1 | Locate heterogeneity | Descriptive | Directional map marks; area for absolute change | `country_question_scores.csv`, pinned coordinates |
| 2 | Compare the update across complementary views | Mixed inferential/descriptive | Dumbbell, raincloud, slope, lollipop, radar | released domain, joint-inference, composition, and country tables |
| 3 | Read the bounded economic implication | Exploratory inference | Slopes, BCa interval lollipops, simplex classes | released economic margin and weight-surface tables |
| 4 | Separate uncertainty sources | Sensitivity | Relative-SE dumbbells and aligned intervals | conditional and country-bootstrap tables |
| 5 | Understand construction and claim boundary | Methodological/conceptual | Four-stage vector flow with solid/dashed semantics | protocol and manuscript Sections 1–4 |
| 6 | Test continuous weight sensitivity | Exploratory sensitivity | Diverging simplex surface and two distinct contours | `economic_weight_surface.csv` |

## Style contract

- Insertion width: 5.48 inches.
- Figure type: DejaVu Sans; 8-point target and 7-point fail-closed floor.
- Semantic colors: navy ink, blue GPT-5.5, teal GPT-5.6/lower error,
  magenta higher error, amber status or theory boundary, restrained gray support.
- Redundancy: circle versus diamond for models, downward versus upward triangles for
  direction, solid versus dashed lines for evidence status, and fill versus open markers
  for corrected status.
- Background: white; grid lines are light and subordinate; no rainbow scale.
- PDF and SVG are authoritative vector outputs; SVG text remains live. PNG is preview-only.

## Claim and evidence safeguards

- Figure 1 is explicitly descriptive and does not identify diffusion, spillovers, or
  culturally uniform regions.
- Figure 2 uses countries as inferential units; its raincloud and radar are identified as
  descriptive summaries.
- Figures 3 and 6 report representation loss under declared weights, not welfare or
  realized policy effects.
- Figure 4 states that conditional resampling holds countries fixed and does not replace
  country-bootstrap inference.
- Figure 5 uses a dashed final path to distinguish theory-guided interpretation from
  observed or computed evidence.

## Integration map

| Number | File | Compiled page |
|---|---|---:|
| Figure 1 | `fig1_spatial_story.pdf` | 2 |
| Figure 2 | `fig2_multiview_results.pdf` | 4 |
| Figure 3 | `fig3_economic_story.pdf` | 7 |
| Figure 4 | `figS1_uncertainty_sources.pdf` | 16 |
| Figure 5 | `figS2_study_design.pdf` | 17 |
| Figure 6 | `figS3_economic_sensitivity.pdf` | 25 |

The main body remains four pages and references begin on page 5. Figure 3 is the first
supplementary visual immediately after the references, preserving the requested
Figure 1–6 numbering sequence.

## Verification

- Six PDF/SVG/PNG export sets regenerate from `scripts/make_visual_story_v080.py`.
- Structural SVG audit passes for all six figures: live text, accessible title, unique
  IDs, no embedded raster, and no type below the declared floor.
- The semantic-graphics manifest passes the publication-asset manifest audit.
- The compiled PDF passes the submission audit: 33 pages, four-page body, references on
  page 5, embedded fonts, no Type 3 fonts, and no undefined references or citations.
- Every compiled figure page was rendered and inspected at final size.

The generic PDF collision detector reports expected false positives where map polygons
or simplex cells sit behind intentional labels and where the page-level region heuristic
includes line numbers. These warnings are recorded in
`manifests/pdf_figure_layout_audit_v080.json`; manual page inspection and the stricter
source-mapped SVG audit found no unresolved visual defect.

# EthosGPT v1.0 visual redesign record

## Visual argument

Figure 1 is a nested, editable composition rather than a monolithic chart. Its
four child modules answer: what prior studies established; how the current
paired audit is constructed; which economic, agent, and deployment questions
the evidence enables next; and how country-level changes vary across the three
predefined error classes. The first three modules occupy a protected top row,
while an enlarged country map and its three external examples occupy a deeper
evidence band. A right-side rail separates thresholds, class counts, countries,
and values from the map viewport. Solid marks represent published or current
evidence. Dashed elements identify theory-guided frontiers.

Figure 2 assigns one idiom to each distinct task: a soft-neutral raincloud for
country-level distribution and threshold classes, a slope for finite-run
persistence, an interval forest for simultaneous item inference, and a
line-only radar for profile shape. The redundant domain dumbbell was removed.
The slope endpoints use separated direct labels and short leaders so the two
remaining-error values remain readable at final paper size.

Figure 3a uses a connected horizontal dumbbell so the three economic-margin
labels sit on a categorical axis rather than inside the quantitative field.
Figure 3c uses the same continuous-surface grammar as the detailed appendix
surface. The appendix preserves the full TVD and CRG maps with external examples,
explicit rules, and a separate threshold note for all three display classes.

## Source contract

- Authoritative exports: PDF and live-text SVG.
- Editable masters: `fig1_spatial_story.drawio`, `figS2_study_design.drawio`,
  and `scripts/make_visual_story_v100.py`.
- PNG files are preview-only.
- Figure font: Nimbus Roman, matching the manuscript's Times-compatible body.
- Minimum explicit SVG font size: 7 pt.
- No embedded raster images, masks, or clipping paths in the displayed SVGs.
- Country maps are descriptive and do not encode culturally homogeneous regions,
  diffusion, spillovers, or causal geography.

## Palette and redundant encoding

- Teal: lower error / interval supports GPT-5.6.
- Magenta: higher error / opposite direction.
- Slate: near zero or uncertain.
- Amber dashed: equal-loss boundaries or theory-guided future pathways.
- Marker shape repeats the class or model identity wherever color is used.

## Threshold definition

Within each mapped metric, $\tau=0.1\max|\Delta|$. Lower means
$\Delta<-\tau$, near zero means $|\Delta|\leq\tau$, and higher means
$\Delta>\tau$. The corresponding thresholds are 0.0030 for TVD and 0.0225 for
CRG.

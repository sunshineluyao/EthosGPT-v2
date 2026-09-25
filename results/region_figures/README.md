# Eight-region descriptive figures

The camera-ready paper maintains its LaTeX and compiled manuscript in
[`EthosGPT-NeurIPS`](https://github.com/sunshineluyao/EthosGPT-NeurIPS).
This folder contains only the figure exports and their provenance; this code
repository has no manuscript source.

## Rebuild

From the root of the reproducibility repository, after installing its pinned
Python requirements:

```sh
python experiments/gpt55_gpt56_64country/plot_eight_regions.py
```

The command validates the frozen country scores against the 64-country roster,
reconciles all 16 region/metric means to the published CSV, then regenerates
two PDF/SVG vector figures and PNG previews in this folder. It does not issue
an API request or recompute uncertainty from new observations. `make assets`
and `make reproduce-offline` run it as part of the normal pipeline.

| Figure | Reader task | Marks and population |
| --- | --- | --- |
| `figS6_region_country_tvd` | Reveal the countries behind each regional TVD average | All 64 countries, one six-question mean loss difference per country; an equal-country regional mean and its published within-region BCa interval for groups with at least five countries; right-side count of countries with lower TVD. |
| `figS7_region_metric_intervals` | Compare direction of W1 and TVD on the same eight regions | Two aligned interval panels using published equal-country regional means and marginal BCa intervals; hollow marks indicate groups with fewer than five countries, with no reported interval. |

### Metric and scope dictionary

- A **country loss** averages six equally weighted question scores. A
  **region loss** averages country losses equally within one of the original
  eight cultural-map labels; regions are never assumed to have equal numbers
  of countries. The original crosswalk is used without relabeling.
- `TVD` is total variation distance between the archived model response
  distribution and the unweighted survey-derived distribution. `W1` is the
  corresponding distance that respects the ordinal order of the answers.
- `delta` is GPT-5.6 Sol loss **minus** GPT-5.5 loss. Negative means the newer
  model has lower error against this particular comparator. Changes in these
  two distance measures need not have the same sign.
- Country dots are observed country statistics. Whiskers are **marginal**, 95%
  within-region country-bootstrap BCa intervals already present in the source
  CSV (20,000 draws, seed 20260925). The eight regions and two metrics are
  exploratory and **not multiplicity adjusted**. No interval is reported when
  a region has fewer than five countries.
- The labels identify aggregate groups in a sample. They do not characterize
  individuals, claim cultural uniformity, establish normative legitimacy, or
  support causal conclusions about model updates.

### Exact source mapping

| Source file | Git blob SHA | Role |
| --- | --- | --- |
| [`country_question_scores.csv`](../../experiments/gpt55_gpt56_64country/results/country_question_scores.csv) | `89629174b97d2a7d4f8b5c6cf2e6077c9bb5c4ab` | 768 model–country–question metric records, summarized at the country level for the dot strip. |
| [`eight_region_sensitivity.csv`](../../experiments/gpt55_gpt56_64country/results/eight_region_sensitivity.csv) | `c771b33d83c0f485ae45cfcfd3a435e703018aac` | The 16 published regional point estimates and marginal intervals in both plots. |
| [`country_roster.csv`](../../experiments/gpt55_gpt56_64country/inputs/country_roster.csv) | `7d3a94e35fb28727d882dd8b316663989ad52925` | The 64-country-to-eight-label crosswalk. |

Colors repeat one meaning in both plots: blue is negative (lower loss), amber
is positive (higher loss). Shapes and zero lines retain that meaning without
color. In the country strip, fixed rank-based *vertical* offsets expose dots
that would otherwise overlap; their horizontal values are never jittered.

### Figure review (2026-09-25)

- **Country TVD strip:** evidence = descriptive; vector PDF/SVG with live
  embedded text; no raster images; 64 country dots and eight means reconcile
  with published inputs; small-group symbols are hollow; compiled page 25
  checked at paper size. Release blockers: none.
- **Two-metric intervals:** evidence = descriptive; the BCa bars and small-n
  omissions mirror the published CSV; the African-Islamic and Confucian rows
  remain distinguishable in grayscale and at paper size; compiled page 26
  checked. Release blockers: none.
- The compiled manuscript's captioned-figure geometry check passed on both
  pages. Matplotlib SVGs use standard axes clip paths; rendered PDF and SVG
  edges were inspected for clipping. The main paper occupies four pages,
  followed by references and appendices.

# Result index (archived-output replication)

This table is the short reader-facing map. The
[machine-readable release index](../manifests/result_replication_index.json)
adds every required stage, command, evidence status, data revision and
interpretation boundary. A path labeled `NOT_RELEASED` records an explicit
acquisition gap; it is not silently replaced by a processed table.

The measured question is whether archived model response distributions
represent six survey answer distributions across 64 countries. The economic
question is a separately assumed decision rule applied to the signed gaps.
The static and dynamic economic calculations are sensitivity exercises under declared mechanisms; their outputs are synthetic.

| Claim | Frozen source | Reproducer | Numeric result |
|---|---|---|---|
| Six-item W1/TVD, CRG, VDR, CSR | `outputs/*scores.jsonl`; `data/processed/human_item_distributions.parquet` | `make reproduce-offline` | [global contrasts](../experiments/gpt55_gpt56_64country/results/metric_comparisons.csv) |
| Joint 12-item W1/TVD family | same frozen outputs and human target | `score_wave1.py` | [joint inference](../experiments/gpt55_gpt56_64country/results/joint_item_inference.csv) |
| Q121 label sensitivity and full five-anchor analysis | same | `protocol_sensitivity.py` | [relabeling bounds](../experiments/gpt55_gpt56_64country/results/q121_prompt_deviation_sensitivity.csv), [five-anchor contrasts](../experiments/gpt55_gpt56_64country/results/five_anchor_metric_comparisons.csv) |
| Original eight cultural-map regions (exploratory) | [country-question scores](../experiments/gpt55_gpt56_64country/results/country_question_scores.csv) | [`eight_region_sensitivity.py`](../experiments/gpt55_gpt56_64country/eight_region_sensitivity.py) (20,000 within-region country BCa draws, seed 20260925; intervals omitted for n < 5) | [W1/TVD by region](../experiments/gpt55_gpt56_64country/results/eight_region_sensitivity.csv) |
| Cultural-region descriptive figures | [country scores](../experiments/gpt55_gpt56_64country/results/country_question_scores.csv), [country roster](../experiments/gpt55_gpt56_64country/inputs/country_roster.csv), [regional intervals](../experiments/gpt55_gpt56_64country/results/eight_region_sensitivity.csv) | [`plot_eight_regions.py`](../experiments/gpt55_gpt56_64country/plot_eight_regions.py) | [two figures and source mapping](../results/region_figures/README.md) |
| Q106, Q121 and Q108 omissions (exploratory) | [country-question scores](../experiments/gpt55_gpt56_64country/results/country_question_scores.csv) | `wording_sensitivity.py` (20,000 paired-country draws, 19,999 sign flips, seed 20260902+121106) | [wording omissions](../experiments/gpt55_gpt56_64country/results/wording_omission_sensitivity.csv) |
| Five-generation observed-pool decomposition | same frozen outputs and human target | `extended_analysis.py` | [composition summary](../experiments/gpt55_gpt56_64country/results/composition_summary.csv) |
| Exploratory economics grouping | six item losses | `extended_analysis.py` | [margin results](../experiments/gpt55_gpt56_64country/results/economic_margin_results.csv) |
| Six directed item gaps by country and original cultural region (descriptive) | [country-question scores](../experiments/gpt55_gpt56_64country/results/country_question_scores.csv), derived from the frozen outputs and unweighted survey target | [`signed_directions.py`](../experiments/gpt55_gpt56_64country/signed_directions.py); `make signed-directions` | [global means](../results/signed_directions/signed_global_items.csv), [all countries](../results/signed_directions/signed_country_items.csv), [eight regions](../results/signed_directions/signed_eight_regions.csv), and [figure guide](../results/signed_directions/README.md) |
| Conditional creative-destruction illustration (synthetic, uncalibrated) | the same [country-question scores](../experiments/gpt55_gpt56_64country/results/country_question_scores.csv) and explicitly assumed decisions and innovation parameters | [`simulate_creative_destruction.py`](../experiments/gpt55_gpt56_64country/simulate_creative_destruction.py); `make creative-destruction` | [five global scenarios](../results/creative_destruction/global_scenarios.csv), [all countries](../results/creative_destruction/country_simulation.csv), [eight regions](../results/creative_destruction/eight_region_simulation.csv), [six-facet decomposition](../results/creative_destruction/six_facet_contributions.csv), and [assumptions and figure guide](../results/creative_destruction/README.md) |
| Dynamic innovation, adjustment, changing values, and advice delay (synthetic) | Portable aggregate [distributions](../experiments/dynamic_growth/inputs/culture_distributions.csv), frozen scores, and [declared parameters](../experiments/dynamic_growth/parameters.json) | `make reproduce-dynamics`; `make mechanisms` | [24 result CSVs](../experiments/dynamic_growth/results/), [14 editable figures](../experiments/dynamic_growth/figures/), [model guide](../experiments/dynamic_growth/MODEL_GUIDE.md) |
| Featured evidence and mechanism visuals | the country, signed-item and scenario CSVs above | `make featured-figures` | [Figure 1 SVG](../results/figures/fig1_ethos_gallery.svg), [Figure 2 SVG](../results/figures/fig2_value_bridge.svg), [provenance](../assets/featured/README.md) |

The signed gaps are derived descriptions of archived outputs against the unweighted survey derivative. The creative-destruction scenarios are synthetic calculations conditional on declared, unestimated decision rules; neither their signs nor magnitudes are observed economic effects. All rows start from the same released score file or its frozen inputs.
The returned `gpt-5.6-sol` identifier is undated, so a later live call need
not reproduce these raw responses. No official population-weighted WVS or
local-language prompt result is included. A changed target or translated
elicitation requires new data, codebook alignment and independently validated
country-item coverage before a numeric sensitivity claim can be made.

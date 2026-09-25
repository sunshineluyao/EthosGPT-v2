# Result index (archived-output replication)

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

All result rows use archived outputs and the unweighted survey derivative.
The returned `gpt-5.6-sol` identifier is undated, so a later live call need
not reproduce these raw responses. No official population-weighted WVS or
local-language prompt result is included. A changed target or translated
elicitation requires new data, codebook alignment and independently validated
country-item coverage before a numeric sensitivity claim can be made.

# Camera-ready changes and provenance

This page documents the revisions to the accepted GlobalSouthAI workshop
manuscript. The four-page camera-ready body presents research findings and
limits; reviewer-facing detail belongs here and in [the response ledger](REVIEW_RESPONSE.md).

## What changed between the two model releases?

With a fixed English prompt on six survey questions for 64 countries, the
archived GPT-5.6 Sol responses had a mean TVD loss 0.0080 below GPT-5.5
(95% paired-country BCa CI [-0.0107, -0.0050]). W1 and three profile/geometry
target-loss changes were inconclusive after the five-metric correction.
Responsibility (Q108) improved under both W1 and TVD; income distribution
(Q106) improved under TVD in the joint 12-outcome family, although Q106's
recorded stem and endpoint labels disagree. Q106/Q108 account for 98.0% of the
signed global TVD reduction. Excluding Q106 yields TVD Δ = -0.00433
([-0.00698, -0.00138]); omitting Q106 and Q108 yields -0.00024
([-0.00313, 0.00286]). These omissions cannot replace corrected-prompt data.
Averaging five recorded generations removes only 1.18% to 1.31% of observed
single-run squared probability error. All comparisons use the unweighted
public survey derivative, not official population weights or user outcomes.

## Six broad groups

The Tao et al. (2024) and WVS cultural-map annotations use eight labels, and
all eight occur in the 64-country sample. This *exploratory six-group
aggregation* combines the three European labels into one broad Europe group;
it leaves African-Islamic, Confucian, English-Speaking, Latin America, and
West & South Asia unchanged. It is our coarsening, not a six-region taxonomy
claimed by Tao et al. The full crosswalk is in
[`cultural_region_crosswalk.csv`](https://github.com/sunshineluyao/EthosGPT-v1.0.0/blob/main/data/metadata/cultural_region_crosswalk.csv).

| Group | Countries | W1 Δ [95% BCa CI] | TVD Δ [95% BCa CI] |
| --- | ---: | ---: | ---: |
| African-Islamic | 15 | 0.0026 [-0.0015, 0.0068] | -0.0080 [-0.0136, -0.0026] |
| Confucian | 9 | 0.0045 [-0.0011, 0.0111] | 0.0021 [-0.0075, 0.0125] |
| English-Speaking | 6 | -0.0055 [-0.0113, -0.0010] | -0.0101 [-0.0130, -0.0064] |
| Europe | 12 | -0.0036 [-0.0074, 0.0003] | -0.0081 [-0.0136, -0.0024] |
| Latin America | 12 | -0.0038 [-0.0087, 0.0001] | -0.0089 [-0.0139, -0.0036] |
| West & South Asia | 10 | -0.0082 [-0.0114, -0.0040] | -0.0149 [-0.0202, -0.0097] |

Each country receives equal weight; changes are means across six items.
Intervals resample countries *within each group* with 20,000 BCa draws.
The six intervals are unadjusted, exploratory, and conditional on recorded
prompt wording. See the code repository's
[`six_region_sensitivity.py`](https://github.com/sunshineluyao/EthosGPT-v1.0.0/blob/main/experiments/gpt55_gpt56_64country/six_region_sensitivity.py)
and [result table](https://github.com/sunshineluyao/EthosGPT-v1.0.0/blob/main/experiments/gpt55_gpt56_64country/results/six_region_sensitivity.csv).

## Editorial decisions

- We retitled the main results section “Empirical results” and moved detailed
  version-change and reviewer-response explanation to GitHub and the appendix.
- We thank the GlobalSouthAI workshop reviewers in the manuscript.
- Prospective weighted-survey, translation, corrected-prompt, within-country,
  model-family, agent-interaction, and decision-impact studies are labeled as
  future research in Appendix J; none is presented as completed evidence.
- The final workshop PDF needs the accepted author order, affiliations, and
  funding disclosure checked against the acceptance record.

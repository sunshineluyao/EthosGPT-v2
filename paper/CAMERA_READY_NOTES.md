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

## Original eight cultural-map regions

The cited Tao et al. (2024) study and the released crosswalk use eight
cultural-map labels. The analysis below retains each original label. Results
are paired country means across the same six items; negative changes indicate
lower loss against the unweighted survey derivative.

| Original region | Countries | W1 Δ | TVD Δ | TVD 95% BCa CI |
| --- | ---: | ---: | ---: | --- |
| African-Islamic | 15 | 0.0026 | -0.0080 | [-0.0136, -0.0026] |
| Catholic Europe | 2 | -0.0083 | -0.0149 | not reported (<5 countries) |
| Confucian | 9 | 0.0045 | 0.0021 | [-0.0075, 0.0125] |
| English-Speaking | 6 | -0.0055 | -0.0101 | [-0.0130, -0.0064] |
| Latin America | 12 | -0.0038 | -0.0089 | [-0.0139, -0.0036] |
| Orthodox Europe | 6 | -0.0062 | -0.0110 | [-0.0181, -0.0034] |
| Protestant Europe | 4 | 0.0028 | -0.0001 | not reported (<5 countries) |
| West & South Asia | 10 | -0.0082 | -0.0149 | [-0.0204, -0.0097] |

The eight groups partition all 64 countries (group sizes range 2--15).
Within-group intervals use 20,000 paired-country BCa draws and are
exploratory and unadjusted. Small-group estimates are descriptive only.
W1 intervals for the remaining groups, original country mapping, and
reproduction code are in the [eight-region CSV](https://github.com/sunshineluyao/EthosGPT-v1.0.0/blob/main/experiments/gpt55_gpt56_64country/results/eight_region_sensitivity.csv),
[crosswalk](https://github.com/sunshineluyao/EthosGPT-v1.0.0/blob/main/data/metadata/cultural_region_crosswalk.csv), and
[analysis script](https://github.com/sunshineluyao/EthosGPT-v1.0.0/blob/main/experiments/gpt55_gpt56_64country/eight_region_sensitivity.py).

## Editorial decisions

- We retitled the main results section “Empirical results” and moved detailed
  version-change and reviewer-response explanation to GitHub and the appendix.
- We thank the GlobalSouthAI workshop reviewers in the manuscript.
- Prospective weighted-survey, translation, corrected-prompt, within-country,
  model-family, agent-interaction, and decision-impact studies are labeled as
  future research in Appendix J; none is presented as completed evidence.
- The final workshop PDF needs the accepted author order, affiliations, and
  funding disclosure checked against the acceptance record.

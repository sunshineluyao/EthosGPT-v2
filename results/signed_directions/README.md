# Signed answers by country and cultural region

This analysis reads the archived, five-generation
`experiments/gpt55_gpt56_64country/results/country_question_scores.csv` and the
original eight-region crosswalk. It **does not** query the models or introduce
survey weights. Run `make signed-directions` from the repository root to rebuild
the files in this directory. The command checks the global signed estimates
against the separately generated `signed_bias_inference.csv` and the region
total-variation means against `eight_region_sensitivity.csv`.

## What a sign means

Each human and model expected answer is put on a zero-to-one scale. The
orientation is fixed from the World Values Survey questionnaire:

| Item | Zero endpoint | One endpoint |
|---|---|---|
| Q48 | no freedom of choice | a great deal of freedom of choice |
| Q57 | need to be careful | most people can be trusted |
| Q106 | more incentives for individual effort | more equal incomes |
| Q108 | more government provision | more individual provision |
| Q121 | very bad contribution from immigrants | very good contribution |
| Q159 | strongly disagree on future science opportunities | strongly agree |

`signed_bias_56 = model_directed - human_directed` in a country and item. A
positive value indicates more of the named one-endpoint position than in the
unweighted survey derivative; a negative value indicates less. Zero is a
reference for *direction*, not evidence that the complete probability
distributions agree. The Q106 archived prompt's category-ten label refers to
income differences even though the official endpoint refers to incentives;
Q121 has a conflicting first-category label. Both limitations affect the
interpretation of these outputs and cannot be repaired retrospectively.

## Files

- `signed_country_items.csv`: all 64 countries × six items, both model gaps,
  their paired signed difference, human directed score, and paired W1/TVD
  changes. One row per country and question.
- `signed_eight_regions.csv`: equal-country mean gaps for both versions,
  paired signed difference, group size, number of countries with a positive
  GPT-5.6 gap, and mean TVD change. Eight source region labels × six items.
- `signed_global_items.csv`: analogous country-equal summaries over all 64
  countries. Existing `signed_bias_inference.csv` supplies the country-bootstrap
  intervals and within-model multiplicity correction for these global means.
- `fig1_argument_bridge.{pdf,svg,png}`: a conceptual grouping of six survey
  questions with measured global signed gaps and observed country variation
  in each original region. Its growth link is a research motivation, not an
  estimated causal path.
- `figS8_signed_eight_regions.{pdf,svg,png}`: two descriptive heatmaps of
  the new model's signed region gaps and the difference between versions.

Regional signs and changes are descriptive. No uncertainty interval for a
signed region-by-item cell and no familywise regional test is claimed;
Catholic Europe has two countries and Protestant Europe four. Every region
contains diverse country results and should not be read as an individual
identity, cultural essence, welfare outcome, or growth rate.

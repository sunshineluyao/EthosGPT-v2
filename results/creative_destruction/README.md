# Conditional creative-destruction illustration

Run `make creative-destruction` from the repository root after generating the
country-question scores, or `make reproduce-offline` from the archived inputs.
The Python source is
`experiments/gpt55_gpt56_64country/simulate_creative_destruction.py`.
It does **not** estimate an economic effect or forecast output, wages,
environmental sustainability, or national income. The item-level survey data
are an unweighted public derivative; Q106 and Q121 have disclosed prompt
label conflicts. All following coefficients are illustrative assumptions.

Let each zero-to-one country profile have the item order Q48 agency, Q57 trust,
Q106 income equality, Q108 individual provision, Q121 immigration contribution,
Q159 science opportunities. Under a profile `x`, hypothetical adviser choices
are `entry=.5+b*(agency+science-1)`,
`assistance=.5+b*(equality-individual_provision)`, and
`coordination=.5+b*(trust+immigration-1)`.
The baseline applies `b=.30`. A per-step innovation arrival has probability
`lambda=.05+.20*entry+.10*coordination`; an arrival replaces one incumbent
and raises frontier quality by 4%. Expected annual log frontier growth is
`lambda*log(1.04)`; expected unassisted-transition exposure is
`lambda*(1-assistance)`. Over 20 steps, expected *log* quality gains add,
under a constant-arrival assumption. A unit of exposure is a model index,
not a displaced person, firm, or job. Comparisons subtract the survey-guided
decisions from decisions that use either version's model-guided profile.

Five declared scenarios vary the unestimated slopes and quality gain. In
`omit_conflicting_Q106_Q121`, equality and immigration have neutral values
of 0.5 in both model and survey decision rules, without recomputing the
archived model responses. `no_decision_link` sets `b=0`, forcing both
contrasts to zero. These are **sensitivity examples**, not confidence
intervals. Even the direction of an economic effect could reverse with a
different decision rule, quality jump, policy objective, or social response.
No fixed mapping from survey answers to socially desirable policies is asserted.

Files:

| File | Content |
| --- | --- |
| `country_simulation.csv` | 64 countries × 2 models × 5 scenarios, inputs and both quality/transition contrasts |
| `eight_region_simulation.csv` | Equal-country means for all eight published region labels |
| `global_scenarios.csv` | Equal-country global means for all five assumed scenarios |
| `six_facet_contributions.csv` | Six signed survey gaps and their exact linear contributions to the arrival and assistance choices |
| `input_validation.csv` | Dataset dimensions asserted before analysis |
| `creative_destruction_regions.pdf`, `.svg`, `.png` | Two outcome proxies for all eight regions under the illustrative scenario |

Sustained frontier quality growth in this quality-ladder toy is one component
of possible economic development. Welfare, shared gains, actual transition
costs, and environmental durability are not observed; they require independent
study. Survey means cannot be substituted for consent from affected people.

# Data pipeline

The raw Oxford derivative is reduced to the final survey item by isolating text after the final `following question` cue. A frozen pattern dictionary assigns only unambiguous target questions; codebook labels map to non-negative WVS scores. Q108 numeric answers are reversed because the derivative reverses its printed endpoints relative to the WorldValuesBench codebook. Conflicting duplicate respondent–item pairs are excluded.

Human response distributions and model-output distributions are aggregated independently by country and item, then normalized using the same official scale endpoints. Country profiles equal-weight available items within each prespecified domain. No survey weights are available in the public derivative; all estimates are therefore unweighted and explicitly labeled as a pilot.

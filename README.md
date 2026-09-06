# EthosGPT

This repository reproduces the anonymous paper:

**EthosGPT: Whose Values Guide Technological Change? Cultural Representation,
Language-Model Updates, and Creative Destruction**

For double-blind submission, the anonymous repository URL is pending author
upload and anonymization. The manuscript reserves one access point at the
opening of the appendix; replace that line with the final anonymous URL before
submission.

The main experiment compares GPT-5.5 and GPT-5.6 Sol with unweighted
survey-derived response distributions for 64 countries on six World Values
Survey anchors. Five model generations for every country–question cell produce
3,840 validated final responses. All inference treats countries, not repeated
generations, as the independent units.

## Main findings

- GPT-5.6 lowers global total-variation error by 0.0080 (95% country-bootstrap
  BCa CI −0.0107 to −0.0050; Holm-adjusted p < .001).
- In one joint 12-outcome family, responsibility improves under W1 and TVD;
  income distribution improves under TVD. Other item changes remain uncertain.
- Global W1, CRG, VDR, and CSR target-loss changes remain uncertain after
  country resampling and multiplicity correction.
- Spatial-error and spatial-HAC estimates retain the global TVD result across
  three neighbor graphs and four distance cutoffs.
- Averaging all five observed runs removes only 1.18%--1.31% of single-run
  squared probability error. This is an exact diagnostic for the observed
  finite pool, not an asymptotic bias estimate or an interactive-agent test.
- An exploratory creative-destruction index finds the largest improvement on
  distribution and adjustment, with coordination and legitimacy uncertain;
  88.76% of the declared-weight grid has a 95% interval entirely favoring
  GPT-5.6, while 11.24% remains uncertain.
- A disclosed Q121 label conflict is addressed by five-anchor exclusion and
  relabeling bounds.
- The v1.0 visual sequence nests protocol-separated prior benchmarks, original
  technical clip art, current country heterogeneity, a continuous
  creative-destruction surface, and future research and deployment implications
  in Figure 1, with the country map and external classification rail isolated
  in a full-width lower band.
  Figure 2 uses four nonredundant idioms: a light-neutral three-type raincloud,
  repeated-output slope with separated endpoint labels, simultaneous interval
  forest, and an India-specific residual radar chosen from human-survey
  coordinates alone. Appendix Figure 7 shows deterministic profile medoids for
  the lower, near-zero, and higher CRG-change classes on the same scale.
- All figure text uses Nimbus Roman, matching the Times-compatible manuscript
  body, with an explicit 7-point floor at final insertion size.

## Reproduce offline

Python 3.12 is recommended.

    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install -r requirements.txt
    make reproduce-offline

For the full developer verification suite, run `make release-contract` after reproduction.

No API key or network access is required. The package validates the two versioned
output files, recomputes every estimate and spatial diagnostic, regenerates all
tables and figures, and compiles a venue-neutral NeurIPS workshop PDF whose main
paper occupies exactly four pages before references.

This is a **reproducible analysis package with versioned proprietary-model
outputs**. It can verify every reported result. It cannot guarantee that a new
query to the undated GPT-5.6 Sol serving identifier will reproduce the same raw
answers.

## Main files

- experiments/gpt55_gpt56_64country/: prompts, versioned model outputs, scoring,
  sensitivity, spatial analysis, and machine-readable results
- paper/: one official, anonymous, venue-neutral NeurIPS 2026 workshop source
  tree designed for either GlobalSouthAI or FAST
- scripts/make_wave1_assets.py, scripts/make_v070_assets.py, and
  scripts/make_visual_story_v100.py: figures, tables, country roster, prompt appendix,
  worked tutorial, and the publication-oriented visual narrative
- SUBMISSION_METADATA.md: title, keywords, TL;DR, and abstract
- REPRODUCIBILITY.md: complete execution and verification instructions
- DATA_LICENSE.md and AI_USAGE.md: provenance, redistribution, and responsible
  use

The published WorldValuesBench and PNAS Nexus results, plus the archived
WorldValuesBench geometry reanalysis, are retained only as protocol-separated
context; they are never pooled with the new 64-country experiment.
Country profiles are ecological summaries and must not be used for individual
eligibility, surveillance, stereotyping, political targeting, or culture
ranking.

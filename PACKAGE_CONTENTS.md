# EthosGPT reproducibility repository

This repository releases the archived outputs, data provenance, analysis code,
machine-readable results, and figure sources for the accepted NeurIPS 2026
GlobalSouthAI paper.

## Contents

- `experiments/gpt55_gpt56_64country/`: frozen model responses, study
  inputs, scoring code, sensitivity analyses, and result CSVs.
- `data/`: documented survey derivative and country/region crosswalks.
- `src/`, `scripts/`, and `tests/`: code to recompute, verify, and visualize
  results from the archived outputs.
- `assets/figure_sources/` and `results/figures/`: editable sources,
  manifest, vector figures, and previews.
- `REPRODUCIBILITY.md`: exact offline commands and evidence boundaries.

The [camera-ready paper and LaTeX source](https://github.com/sunshineluyao/EthosGPT-NeurIPS)
are maintained separately. This repository contains no manuscript source or
PDF build.

## Run

```bash
python -m pip install -r requirements.lock.txt
make reproduce-offline
make release-contract
```

These commands use the included, cryptographically validated outputs; they do
not query a live model or require an API key.

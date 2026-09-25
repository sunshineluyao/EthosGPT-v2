# Reproducibility guide

## Offline reproduction

The offline route starts from the included aggregate human comparison and the
two archived model-output files. It performs these stages:

1. validate 1,920 records per model, 64 countries, six questions, five
   generations, probability supports, model identifiers, and hashes;
2. average repeated generations within each country–question cell;
3. recompute W1, TVD, CRG, VDR, CSR, signed bias, and run instability;
4. run 20,000 country-cluster bootstrap draws, 19,999 paired sign flips, and a
   dependence-preserving 12-outcome max-$T$ family;
5. exhaustively decompose all subsets of the five observed generations into
   shared and generation-varying squared probability error;
6. estimate three theory-indexed creative-destruction margins and a 0.02
   weight-simplex sensitivity;
7. run 5,000-draw human-cell and generation sensitivities, Q121 bounds,
   pre-existing five-anchor analysis, post-review Q106/Q121/Q108 omission checks,
   leave-country/region-out checks, and human-cell-size strata;
8. run Moran, Geary, spatial-error, and spatial-HAC diagnostics;
9. regenerate all tables, figures, and appendix tutorial assets; and
10. compile and audit the single venue-neutral NeurIPS workshop PDF, enforcing
    an exact four-page body before references.

Run:

    make reproduce-offline
    make release-contract

No API key or network request is used. Archived outputs reproduce the analysis;
a later live request to an undated serving identifier is not promised to return
the same output.

## Random seeds and resampling settings

- Analysis seed: 20260902
- Post-review wording omission seed: 20260902 + 121106
- Country-bootstrap draws: 20,000
- Paired randomization draws: 19,999
- Joint item family: 12 W1/TVD outcomes with shared country signs and max-$T$
- Spatial permutation draws: 9,999
- Human-cell conditional draws: 5,000
- Five-generation conditional draws: 5,000
- Primary spatial graph: symmetric four-nearest-neighbor great-circle graph
- Spatial graph sensitivities: six and eight neighbors
- Spatial-HAC cutoffs: 1,000, 2,000, 3,000, and 5,000 km
- Economic weight grid: nonnegative weights summing to one in 0.02 steps

CSV and Parquet files are the numeric authority. The manuscript rounds only for
display. Monte Carlo standard errors are released for randomization tests.
The exploratory omission file recomputes W1/TVD from the frozen country-question
scores, using 20,000 paired-country BCa draws and 19,999 sign flips. Holm adjustment
covers W1 and TVD within each omission scenario only; it does not protect the set
of exploratory scenarios. Omission is not a rerun with corrected Q106/Q121 wording.

## What the package does and does not reproduce

| Layer | Reproduced offline? | Qualification |
|---|---:|---|
| Archived model outputs | Yes | Exact released JSONL and hashes |
| Metrics and uncertainty | Yes | Recomputed from archived outputs |
| Tables, figures, and PDF | Yes | Generated from released numeric files |
| Live proprietary inference | No guarantee | GPT-5.6 Sol has no dated public snapshot |
| Official population-weighted WVS estimates | No | Comparison uses an unweighted public derivative |

## Environment

Python dependencies are exposed through requirements.txt and pinned in
requirements.lock.txt. The manuscript uses
the supplied official NeurIPS 2026 style file and pdfLaTeX. Verification checks
undefined references, page boundaries, fonts, anonymity, and the complete
official `checklist.tex` included with the NeurIPS template.

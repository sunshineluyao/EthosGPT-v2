# Replication report — frozen experiment and v1.0.0 revision

## Frozen evidence recovered

- 1,920 valid GPT-5.5 records and 1,920 valid GPT-5.6 Sol records.
- 64 countries, six questions, and five generations in every model cell.
- 3,850 attempt-ledger rows: 3,840 first attempts plus ten successful reruns.
- Zero final failed records.
- Frozen prompt-set SHA-256:
  `d8673796bd2bdb9e7259d1548287e988d010942c808aa8d5f555735ec4a0cc73`.
- Source upload SHA-256:
  `6d2631c6a10c1436aceaa6c441edc09f009c6fed637baa5ab5a8604c14c627a8`.

## Executed route

`make reproduce-offline` completed the following path without an API key or
network request:

1. validate frozen outputs, model identifiers, prompt hashes, and pairing;
2. score W1, TVD, CRG, VDR, CSR, signed bias, and instability;
3. run country bootstrap, paired randomization, joint max-$T$, conditional
   uncertainty, prompt, cell-size, leave-country, and leave-region checks;
4. run the finite-five composition decomposition;
5. run creative-destruction margin and simplex sensitivity;
6. run Moran, Geary, spatial-error, and spatial-HAC analyses;
7. regenerate tables, vector figures, prompts, country roster, and tutorial;
8. compile and audit the one combined NeurIPS workshop PDF.

The two figure entry points now set a fixed `SOURCE_DATE_EPOCH`; two successive
asset-and-paper rebuilds produced the same PDF SHA-256.

## Verification checks

- 16 regular tests: pass.
- 3 fail-closed negative tests: pass.
- Frozen-output, prompt, coverage, multiplicity, citation, anonymity, template,
  checklist, font, page, and secret checks: pass.
- Main paper: four pages; references begin on page 5.
- Complete PDF: 33 pages; official checklist is last.
- Fonts: all embedded; no Type 3; no overfull box or unresolved citation.

## Interpretation boundary

This package reproduces reported analysis from frozen proprietary-model
outputs. It does not reproduce the unavailable provider-side model snapshot,
hardware, system routing, or live inference behavior. The human comparison is
an unweighted public derivative rather than official population-weighted WVS
microdata.

## Reviewer wording sensitivity (v1.0.0 revision)

The source score CSV has the same Git blob hash as the frozen v1.0.0 score
CSV. An independent local run of `wording_sensitivity.py` on those scores
produced the committed `wording_omission_sensitivity.csv`. The workflow now
recomputes it after `score_wave1.py`; `verify_results.py` checks the full
six-item contrast against the original result and the Q121-omission contrast
against the existing five-anchor result. The output records the seed,
20,000 country-bootstrap draws, 19,999 paired sign flips, and scenario-wise
W1/TVD Holm correction. Q106 omission leaves TVD Δ = −0.00433, 95% BCa
[−0.00698, −0.00138]; omitting both Q106 and Q108 leaves Δ = −0.00024,
[−0.00313, 0.00286]. These exploratory exclusions do not recover an
unambiguous-prompt counterfactual. The earlier verification figures above
refer to the frozen release audit; the new branch CI checks the amended route.

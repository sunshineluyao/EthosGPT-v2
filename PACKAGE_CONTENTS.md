# EthosGPT v1.0.0 release

This release provides one anonymous, venue-neutral NeurIPS 2026 workshop paper
and a fully traceable offline reproduction package.

## Deliverables

- `EthosGPT_v1.0.0_NeurIPS2026_submission.pdf`: compiled workshop manuscript.
- `EthosGPT_v1.0.0_Overleaf.zip`: clean LaTeX source with one `main.tex`, the
  official `checklist.tex`, vector figures, editable Draw.io masters, and tables.
- `EthosGPT_v1.0.0_GitHub_reproducible.zip`: versioned inputs, analysis code,
  tests, generated results, manuscript source, disclosures, and audit records.
- `EthosGPT_v1.0.0_revision_and_release_report.md`: revision ledger, numerical
  claim boundary, venue-fit review, and verification summary.

## Verified manuscript structure

- Pages 1–4 contain the complete main paper.
- References begin on page 5; technical appendices and the official checklist
  follow and do not count toward the four-page body.
- Figure 1 is an editable nested Draw.io argument with Python-generated prior,
  technical-audit, economics/frontier, and country-evidence child modules; the
  main map is enlarged and its rules, counts, and examples occupy a separate rail.
- Figure 2 contains four complementary idioms: a soft-neutral country
  raincloud, repeated-output slope with separated endpoint labels,
  simultaneous interval forest, and fixed-scale radar.
- Appendix Figure 6 retains the full TVD and CRG maps. Appendix Figure 7 shows
  reproducibly selected lower, near-zero, and higher CRG-change country profiles;
  Appendix Figure 8 retains the detailed continuous creative-destruction surface.
- Main and appendix tables use the same header, status, emphasis, and numeric
  alignment system.
- Every figure uses the same Times-compatible serif family as the manuscript,
  with live text at or above the 7-point release floor.

## Reproduction

After extracting the reproducibility ZIP, create the documented environment
and run:

    make reproduce-offline

To run the full developer verification suite:

    make release-contract

No API key or new model call is required. The release reproduces every reported
analysis from included, cryptographically validated proprietary-model outputs;
it cannot guarantee identical answers from a future provider-controlled serving
endpoint.

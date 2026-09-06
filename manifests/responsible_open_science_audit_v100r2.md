# Responsible open-science audit - v1.0.0 revision 5

## Recommendation

Ready with minor human actions. The evidence, code, manuscript, and figure
lineage are internally consistent and executable. Before submission, the human
lead should inspect the PDF and approve the bounded interpretation and
contribution claims.

## Scope and evidence level

The audit covers the anonymous 33-page PDF, exact four-page body, 3,840
versioned outputs, result tables, prompts, analysis and verification code, eight
figures, two Draw.io masters, appendix tables, checklist, metadata, and release
workflow. Executed evidence reaches E5 for the full release contract.

| Domain | Rating | Evidence and consequence |
|---|---|---|
| Claim-result consistency | Pass | Manuscript values agree with released results and tests. |
| Statistical transparency | Pass | Country bootstrap, sign flips, multiplicity families, and sensitivity status are explicit. |
| Country-case selection | Pass | India uses human-only medoid selection; three appendix cases use class-first CRG residual medoids. No visual case is an inferential unit or claim of representativeness. |
| Computational reproducibility | Pass | Release contract, 16 unit tests, three negative tests, and offline reproduction pass. |
| Data provenance | Partial | Public de-identified derivative and prompts are documented; official weights/full survey design are unavailable. Keep the estimand unweighted. |
| Model provenance | Partial | Outputs and prompts are immutable; the GPT-5.6 serving identifier is undated. |
| Community validity | Coverage gap | English-only country aggregates with no community co-design cannot support local legitimacy or Global South representativeness. |
| Agent-system validity | Coverage gap | No communication or interaction is observed; FAST contribution is a pre-interaction baseline. |
| Responsible AI disclosure | Pass | Limitations, ethics, consent/IRB applicability, AI use, and human accountability are disclosed. |

## Corrective actions completed

- Replaced latent/cultural construct language with survey representation.
- Restricted agent claims to a finite-pool pre-interaction diagnostic.
- Kept the economic surface as one descriptive sensitivity.
- Replaced the potentially canceling average radar with an outcome-independent
  country case and added transparent CRG-class medoids in the appendix.
- Preserved the full 64-country analysis as the source of estimates and
  uncertainty; the four radar cases are descriptive only.

## Remaining human action

Approve the interpretation, contribution, and release-correction gates after
reading the final PDF. No automated process has submitted the manuscript.

Passing supports transparency and reproducibility; it does not prove truth,
external validity, absence of misconduct, or acceptance.


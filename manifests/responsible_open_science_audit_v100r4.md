# Responsible open-science audit — v1.0.0 revision 6

## Recommendation

Ready after one blocking author action: upload the release package to an
anonymous repository and replace the reserved appendix access line with the
real URL. The manuscript must not be submitted with the current pending-link
text.

## Scope and evidence level

The audit covers the anonymous 33-page PDF, exact four-page body, 3,840
versioned outputs, prompts, analysis and verification code, eight figures, two
Draw.io masters, appendix tables, checklist, metadata, and clean release
workflow. The paper-critical release contract, 16 unit tests, and three
deliberate-failure tests pass.

| Domain | Rating | Evidence and consequence |
|---|---|---|
| Claim–result consistency | Pass | Wording retains the released estimates, nulls, and scope boundaries. |
| Measure transparency | Pass | W1, TVD, CRG, VDR, and CSR are defined intuitively and mathematically before Table 1; Appendix D supplies worked arithmetic. |
| Statistical transparency | Pass | Country bootstrap, paired sign flips, multiplicity families, and sensitivity analyses remain explicit. |
| Computational reproducibility | Pass | Offline rebuild, source audit, clean-room compilation, and all-page pixel comparison pass. |
| Data provenance | Partial | The public derivative is de-identified and versioned, but official weights and full survey-design provenance are unavailable. |
| Model provenance | Partial | Prompts and outputs are immutable; the GPT-5.6 serving identifier remains undated. |
| Open-science availability | Author action | The package exists and is documented; the anonymous public URL is pending upload and anonymization. |
| Community validity | Coverage gap | English country aggregates without co-design do not establish local legitimacy or Global South representativeness. |
| Agent-system validity | Coverage gap | The study observes repeated outputs, not communication or interaction. |
| Responsible AI disclosure | Pass | AI assistance, human responsibility, limitations, ethics, and prohibited uses are stated. |

## Availability-statement consistency

The abstract states that a versioned reproducibility package accompanies the
submission. Section 1 identifies its contents and points to the appendix. The
appendix begins with one URL field and a contents statement; Appendix J gives
offline commands and compute accounting. README.md, SUBMISSION_METADATA.md,
and AI_USAGE.md use the same availability boundary. No public URL has been
invented.

## Visual-audit note

The project-specific vector/source audit and full-page visual inspection pass.
The generic PyMuPDF probe's raw revision-6 output is retained because it
classifies official NeurIPS line numbers and intentional chart-axis/background
contacts as collisions; those findings are not silently reported as zero.

## Human decision gate

- Insert and verify the anonymous repository URL.
- Inspect the final PDF and public package.
- Confirm institutional/venue AI-disclosure and human-subjects requirements.
- Approve the interpretation, contribution wording, and submission.

Passing this audit supports transparency and reproducibility; it does not prove
external validity, local legitimacy, truth, or acceptance.

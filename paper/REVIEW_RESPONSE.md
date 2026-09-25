# GlobalSouthAI workshop review response and change record

This reviewer-facing page accompanies the camera-ready manuscript; it is
not part of the four-page paper. The archived model outputs are unchanged.
For a reader-facing summary, see [camera-ready changes](CAMERA_READY_NOTES.md).
The new omission calculations use the released 64-country score file. “Addressed”
means revised text or a calculated result is present; “open” means the underlying
new evidence is unavailable and no result is claimed.

## Reviewer NvQv

1. **Lower TVD does not imply better advice, individual representation, or welfare — addressed.**
   The abstract and Sections 1, 2, and 4 identify the outcome as agreement with
   country-level response distributions from an unweighted derivative. They
   explicitly rule out downstream user, individual, and welfare claims.
2. **WVS is not cultural ground truth — addressed.** Section 2 reports the
   derivative and cell counts (median 30.5, range 4–96). Sections 1 and 4
   distinguish the measurement target from national cultures and local validity.

## Reviewer kR6F

1. **Readability and duplicated Table 1 numbers — addressed in text.**
   Section 3 now names the one corrected global result and focuses on Q106/Q108
   concentration; Appendix G gives the omission checks. Section 4 opens with a direct
   answer and ends with a concrete validation sequence.
2. **Thin comparison to prior work — addressed.** Section 1 now explicitly
   credits WorldValuesBench's four-system benchmark and Tao et al.'s five-version
   and country-prompt comparisons. It identifies this study's narrower paired
   estimand under one fixed survey, prompt, and probability-output protocol;
   Appendix I preserves a side-by-side protocol comparison.
3. **Only one vendor, six questions, English, and country means — addressed as
   limits, not generalized away.** The abstract, Sections 1, 2, and 4 scope all
   claims accordingly. No cross-vendor or within-country result is asserted.
4. **English-only prompting may measure stereotypes — addressed as a main-text
   threat.** Sections 1, 2, and 4 identify English prompts and questionnaire
   familiarity in training as alternative explanations. A translated-prompt
   experiment is open pending new model outputs and language validation.
5. **Creative-destruction framing exceeds observed evidence — addressed.**
   Section 4 calls the three-margin grouping exploratory and says it measures
   survey error, not decisions. Appendix H identifies the quadratic bridge as
   hypothetical, with unestimated parameters and no welfare inference.
6. **Improvement is concentrated in two items — addressed quantitatively.**
   Q106/Q108 contribute 98.0% of the signed six-item TVD point difference.
   The post hoc Q106 omission leaves TVD Δ = −0.00433 (95% BCa
   [−0.00698, −0.00138]); excluding both Q106/Q108 leaves Δ = −0.00024
   ([−0.00313, 0.00286]). Appendix G and the GitHub change record report the limited result.
7. **Unweighted second-hand WVS target and possible memorization — partially
   addressed.** Methods now state provenance, cell sizes, and training-data
   ambiguity. An official weighted WVS spot check is still open because the
   archived release contains no matched official microdata and weights; a
   numeric weighted estimate is not claimed. It requires a licensed/downloaded
   official file, country and wave mapping, and harmonized missing-value and
   response-category rules before comparison.

## Reviewer uobd

1. **Language and country-level scope — addressed.** Main-text and abstract
   limitations name both and do not infer within-country linguistic diversity.
2. **Economic bridge — addressed.** Section 4 and Appendix H separate the
   measured survey losses from hypothetical decision mappings.
3. **Q106 and Q121 prompt discrepancies — addressed with an important
   qualification.** Section 2 and Appendix C now disclose both precisely.
   The released Q121 five-anchor and relabeling sensitivities remain. New
   paired-country W1/TVD exclusions omit Q106, Q121, both, Q108, or Q106/Q108.
   Q106's item-specific benefit remains conditional on its recorded inconsistent
   prompt; omission cannot prove what corrected wording would elicit.
4. **Three economic margins are judgmental rather than validated choices —
   addressed.** Section 4 calls the grouping exploratory and disclaims
   decision or welfare validity; Appendix H explicitly marks the model's
   parameters unestimated.
5. **Compressed main text and dense Figure 1 — partially addressed.**
   The main-text narrative and Figure 1 caption are shorter and indicate which
   panels are observed versus contextual or forward-looking. A complete visual
   redraw has not been performed in this revision.
6. **Two proprietary releases and undated GPT-5.6 endpoint — addressed as a
   reproducibility limit.** Sections 2 and 4 and the code README separate
   exact recomputation from archived responses from non-guaranteed live
   re-querying; no model-family generalization is made.
7. **Would local-language prompts reduce CRG or worsen VDR? — open.** Neither
   translated country prompts nor their responses exist in this release.
   Directional predictions would be speculation; a paired translated-prompt
   experiment with independently checked translations is required.
8. **How would official survey weights change ΔTVD? — open.** The archived
   target is unweighted. No compatible official weighted comparison is included,
   so no weighted ΔTVD or claimed direction of change is given.

## Reproduction and inferential scope

Run `make reproduce-offline` in the code repository. The added
`experiments/gpt55_gpt56_64country/wording_sensitivity.py` reproduces
`results/wording_omission_sensitivity.csv` from
`results/country_question_scores.csv`; `scripts/verify_results.py` checks its
six-item point estimate against the primary result and its Q121-omission
estimate against the earlier five-anchor analysis. It uses 20,000 country BCa
draws, 19,999 paired sign flips, and W1/TVD Holm adjustment within each
omission scenario. These post hoc scenarios are not jointly adjusted and
cannot identify outcomes under repaired prompts.

## Camera-ready additions after this response draft

- Appendix G reports the original eight cultural-map regions without merging
  labels. The country-group sizes, W1/TVD results, and reproducible CSV are in
  the code repository; small groups receive descriptive point estimates only.
- The four-page paper now presents empirical results without the review-style
  heading; detailed release contrasts and reviewer point-by-point notes remain
  on GitHub. The workshop reviewers are acknowledged in the PDF.
- Unimplemented extensions are explicitly identified as future research in
  Appendix J.

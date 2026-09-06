# Manuscript-wide visual consistency audit - v1.0.0 revision 5

## Result

Pass. The main paper and appendix use one role-based visual system across eight
figures and all tables.

| Contract | Verified implementation | Result |
|---|---|---|
| Typography | Nimbus Roman matches the paper's Times-compatible body; target 8 pt, floor 7 pt. | Pass |
| Layout | Every figure is 5.48 inches wide and inserted at full column width; headings, legends, labels, and captions occupy protected zones. | Pass |
| Model roles | GPT-5.5 is blue/hollow-circle/dashed; GPT-5.6 is teal/filled-diamond/solid; human survey is a black zero ring in residual radars. | Pass |
| Change classes | Lower, near zero, and higher use teal-down, gray-circle, and magenta-up with printed rules and thresholds. | Pass |
| Country cases | Main radar is selected from human survey values only; appendix profiles are selected after CRG classification. | Pass |
| Statistical status | Confidence intervals, corrected support, and descriptive/inferential/sensitivity status remain explicit. | Pass |
| Evidence status | Published context, archived reanalysis, current evidence, and future tests are visually separated. | Pass |
| Grayscale | Shape, orientation, line style, fill, outline, and lightness preserve distinctions. | Pass |
| Tables | Main and appendix tables share header bands, restrained status shading, spacing, and pagination protection. | Pass |
| Export/editability | Every figure has vector PDF and live-text SVG; Figures 1 and 5 retain Draw.io masters. | Pass |

## Final-size inspection

- Main pages 1-4 have no clipped title, abstract, caption, figure, or conclusion;
  references begin on page 5.
- Figure pages 2, 4, 7, 16-18, 23, and 25 have no confirmed overlap, cropping,
  unreadable type, orphan legend, or ambiguous order.
- Figure 1 uses its former empty width for a larger map and external examples.
- Figure 2a uses a soft neutral distribution region; 2b separates endpoints; 2d
  shows one country on a signed -0.20 to +0.20 residual scale.
- Appendix Figure 7 applies exactly the same radar scale and encoding to all
  three CRG classes, so panel area cannot imply different magnitudes.
- The checklist and declaration remain complete and legible on pages 27-33.

The generic page-object audit is retained as a diagnostic because it interprets
intended axes, fills, borders, table backgrounds, and line numbers as collisions.
Figure-aware checks plus rendered-page inspection found zero release-blocking
visual defects.


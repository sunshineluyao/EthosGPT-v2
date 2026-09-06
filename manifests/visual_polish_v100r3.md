# Final visual-system polish - v1.0.0 revision 5

## Outcome

The final pass resolves the manuscript-wide type mismatch, Figure 1 crowding,
Figure 2 panel collisions, the overly saturated distribution summary, and the
scientific weakness of a cross-country averaged radar.

## Visual decisions

- Nimbus Roman matches the Times-compatible manuscript body.
- Every displayed figure is 5.48 inches wide, targets 8 pt, and fails below 7 pt.
- GPT-5.5 is blue/hollow/dashed; GPT-5.6 is teal/diamond/solid.
- Lower, near-zero, and higher change use teal-down, gray-circle, and magenta-up.
- Observed/computed evidence is solid; prospective paths and declared
  equal-loss boundaries are dashed amber.
- PDF and SVG are authoritative; PNG is preview-only.

## Radar redesign

Figure 2d no longer averages countries. India is selected as the medoid of the
six standardized human-survey coordinates, with model outcomes excluded. The
panel shows exact signed model-minus-human residuals on a symmetric -0.20 to
+0.20 scale and reports CRG 0.756 to 0.732.

Appendix Figure 7 adds one profile medoid per threshold-defined CRG-change class:
Greece (lower), Indonesia (near zero), and Argentina (higher). All three panels
share the same residual scale. This displays heterogeneity without presenting a
hand-picked success/failure example or implying that a country represents a
region or culture.

## Inspection record

Eight standalone figures and compiled pages 2, 4, 7, 16-18, 23, and 25 were
reviewed. No clipped title, truncated label, legend collision, text-to-text
overlap, or panel collision remained. Exact source/profile ledgers and regression
assertions verify selection, transformation, axis limits, and model draw order.

No inferential result, interval, multiplicity decision, threshold, or sample size
was changed.


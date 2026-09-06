# Technical release gate - v1.0.0 revision 5

## Status

Technical pass. Human submission authorization remains pending.

- Source/result/PDF lineage receipt: pass.
- Meta-science structural audit: pass with zero errors or warnings.
- Responsible open-science record: valid; ready with minor human actions.
- End-to-end release contract: pass.
- Immutable input, prompt, and result assertions: pass.
- Tests: 16 unit tests and three deliberate-failure tests passed.
- Main body: exactly four pages; references begin on page 5.
- Full PDF: 33 letter-size pages.
- PDF SHA-256: 325da03db9c1549d5e3c7551fd03e384595b7d824d5bcc228e9e32c309d83900.
- LaTeX: zero errors, overfull boxes, unresolved references, or unresolved
  citations; 20 benign underfull-box notices.
- Fonts: embedded; no Type 3 faces.
- Visual source map: eight vector figures and two parseable Draw.io masters.
- Figure 2d: India is the human-only profile medoid; exact model-minus-human
  residuals use -0.20 to +0.20, with both models visible and CRG 0.756 to 0.732.
- Appendix Figure 7: Greece, Indonesia, and Argentina are deterministic medoids
  of lower, near-zero, and higher CRG-change classes on the same residual scale.
- Figure inspection: pages 2, 4, 7, 16-18, 23, and 25; no confirmed clipping or
  unreadable overlap.
- Overleaf archive: 121 files; clean compilation is
  byte-identical and pixel-identical across all 33 pages.
- Overleaf ZIP SHA-256: 9fad485d7a9114dd070e902bc7daa1c66cf919ccfb3b59a9feb0ef34b3feb8c8.
- GitHub archive: 327 files; the complete release contract passes
  after fresh extraction.

The meta-science release validator correctly withholds a formal release pass
until the human lead approves interpretation, contribution, and release gates.
No submission was performed.

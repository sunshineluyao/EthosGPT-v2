# Overleaf build

Upload the ZIP contents so main.tex is at the project root and compile with
pdfLaTeX. The source uses the supplied official NeurIPS 2026 style and requires
no shell escape or external download.

Build the single anonymous, venue-neutral workshop version prepared for either
GlobalSouthAI or FAST:

    latexmk -pdf -halt-on-error -interaction=nonstopmode main.tex

The `\workshoptitle{NeurIPS 2026 Workshop Submission}` declaration uses the
official `dblblindworkshop` option without naming a venue inside the submitted
PDF. The title, exact four-page main body, references, technical appendix, and
the supplied official `checklist.tex` are contained in this one PDF. Keep
metadata.tex anonymous during review.

All eight figures use vector PDF and live-text SVG outputs; Figures 1 and 5 also
include editable Draw.io masters. Prompt and code blocks
use Latin Modern Mono within restrained tcolorbox frames, while figures use a
consistent Times-compatible Nimbus Roman family. Figure 2d uses India's
outcome-independent human-profile medoid, and Appendix Figure 7 supplies one
deterministic profile medoid per CRG-change class. SUBMISSION_METADATA.md
contains the title, comma-separated keywords, TL;DR, and abstract for
OpenReview.

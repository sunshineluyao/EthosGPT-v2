# Camera-ready manuscript build

Compile `main.tex` with pdfLaTeX using the supplied NeurIPS 2026 style:

    latexmk -pdf -halt-on-error -interaction=nonstopmode main.tex

The accepted GlobalSouthAI workshop manuscript uses the official
`dblblindworkshop,final` options and `\\workshoptitle{GlobalSouthAI}`.
The main paper occupies four pages before references; the technical appendix
and official checklist follow the bibliography. The sole author name currently
shown in `metadata.tex` is Luyao Zhang, taken from the public EthosGPT
project record; confirm the final author order, affiliations, and funding
disclosure against the accepted submission before delivery.

Detailed changes to this manuscript and the exploratory six-group analysis
are described in [CAMERA_READY_NOTES.md](CAMERA_READY_NOTES.md) and
[REVIEW_RESPONSE.md](REVIEW_RESPONSE.md). The executable replication package
is [EthosGPT-v1.0.0](https://github.com/sunshineluyao/EthosGPT-v1.0.0).

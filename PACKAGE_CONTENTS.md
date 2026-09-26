# EthosGPT code and data package

This repository contains the archived model outputs, survey derivative,
analysis code, numeric results and editable visual assets for the NeurIPS 2026
GlobalSouthAI study. It does not contain manuscript source files or the paper
PDF.

| Entry | Contents |
|---|---|
| [`experiments/gpt55_gpt56_64country/`](experiments/gpt55_gpt56_64country/) | Study inputs, frozen outputs, scoring and uncertainty code, and result tables |
| [`data/`](data/) | Documented unweighted survey derivative and country/region crosswalks |
| [`src/`](src/), [`scripts/`](scripts/), [`tests/`](tests/) | Processing, offline reproduction, integrity gates and tests |
| [`assets/`](assets/) and [`results/`](results/) | Editable figure sources, manifests, vector figures and previews |
| [`manifests/result_replication_index.json`](manifests/result_replication_index.json) | Six-stage map of each headline result, including acquisition gaps |
| [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md) | Exact commands, frozen inputs and evidence boundaries |

From Python 3.12 with the pinned dependencies installed, run:

```bash
make release-smoke
make reproduce-offline
make release-contract
```

The commands start from included, cryptographically validated archived
outputs. They do not call a live model or require an API key. The original
authenticated collection client is not bundled; exact prompts, ledgers,
collection receipts and frozen outputs document that boundary.

# Replication report — archived 64-country comparison

## Frozen evidence

- 1,920 valid GPT-5.5 records and 1,920 valid GPT-5.6 Sol records.
- 64 countries, six questions, five generations in every model cell.
- 3,850 attempt-ledger rows: 3,840 first attempts plus ten successful reruns.
- Frozen prompt-set SHA-256:
  `d8673796bd2bdb9e7259d1548287e988d010942c808aa8d5f555735ec4a0cc73`.
- Source upload SHA-256:
  `6d2631c6a10c1436aceaa6c441edc09f009c6fed637baa5ab5a8604c14c627a8`.

## Offline route

`make reproduce-offline` validates archived records and prompt hashes,
recomputes W1/TVD/CRG/VDR/CSR, 20,000-country-draw bootstrap intervals,
paired randomization and joint inference, Q106/Q121/Q108 omission checks,
the original eight cultural-map region contrasts, signed item positions by
country and region, spatial and economic sensitivities, the explicitly assumed
quality-ladder scenarios, and the released vector figures. `make release-contract`
runs the code, numerical, negative-path, and visual checks.

The authoritative regional output is
[`eight_region_sensitivity.csv`](../experiments/gpt55_gpt56_64country/results/eight_region_sensitivity.csv).
Its original labels are retained; intervals are exploratory and omitted when
a group has fewer than five countries. The [result index](result_index.md)
points to all six signed country and region item results and the separate,
synthetic quality-ladder calculations. The latter have no estimated causal
parameters or observed growth, employment, welfare, or environmental outcome.

## Scope

Offline replication starts with frozen proprietary-model outputs and an
unweighted survey derivative. It cannot reproduce the provider-side
snapshot or a population-weighted WVS estimate. Manuscript sources and the
compiled workshop PDF are maintained in the
[paper repository](https://github.com/sunshineluyao/EthosGPT-NeurIPS).

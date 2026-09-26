# EthosGPT reference verification ledger — v0.5.0

Audit date: 2026-09-02  
Scope: all 23 works cited in the 64-country manuscript.  
Evidence ceiling: authoritative publisher, repository, dataset, documentation, or official institutional records were inspected. The audit verifies bibliographic identity and whether each citation supports the sentence in which it appears; it does not independently reproduce the cited studies.

The bibliography is maintained with the manuscript. This code release keeps
source URLs and claim boundaries in this ledger without a BibTeX or LaTeX
file.

## Reference-by-reference verification

| BibTeX key | Verified URL | What the source does | How this manuscript uses it | Support |
|---|---|---|---|---|
| `schumpeter1942capitalism` | https://archive.org/details/in.ernet.dli.2015.190072 | Develops the classic account of capitalism as an evolutionary process in which innovation displaces incumbent products, firms, and routines. | Defines the historical meaning of creative destruction. It does not supply a universal cultural optimum. | Direct |
| `aghion1992model` | https://doi.org/10.2307/2951599 | Formalizes endogenous growth through vertical innovation, temporary monopoly rents, and obsolescence of prior intermediate goods. | Grounds the quality-ladder mechanism and motivates the explicit bridge from representation error to innovation-support and adjustment choices. | Direct |
| `mokyr2002gifts` | https://www.jstor.org/stable/j.ctt7rz25 | Distinguishes propositional from prescriptive useful knowledge and studies institutions that make technological knowledge cumulative. | Supplies the knowledge and institutional side of sustained technological progress. | Direct |
| `nobel2025` | https://www.nobelprize.org/prizes/economic-sciences/2025/press-release/ | Officially announces the 2025 economics prize to Joel Mokyr, Philippe Aghion, and Peter Howitt for explaining innovation-driven economic growth, including growth through creative destruction. | Verifies the laureates, the prize rationale, and the connection between knowledge prerequisites, innovation, displacement, and sustained growth. | Direct |
| `haerpfer2022wvs` | https://doi.org/10.14281/18241.24 | Documents the final World Values Survey Wave 7 country-pooled data release and survey context. | Provides WVS7 survey context. It is not used to claim that the public derivative preserves official weights or full upstream provenance. | Direct/qualified |
| `wvs7masterquestionnaire` | https://access.gesis.org/dbk/69555?download_purpose=-99 | Provides the official English WVS7 master questionnaire, including question wording and response choices. | Supplies the reference wording against which the six frozen API prompts are printed and deviation-audited in Appendix C. | Direct |
| `evswvs2024joint` | https://doi.org/10.4232/1.14320 | Harmonizes EVS 2017 and WVS7 into the Joint EVS/WVS 2017–2022 dataset, version 5.0.0. | Places the public derivative in the broader survey ecosystem and motivates future population-weighted replication. It is not substituted for the actually parsed derivative. | Direct/qualified |
| `oxfordllmswvs` | https://huggingface.co/datasets/oxford-llms/world_values_survey_2017_2022_sft | Hosts the pinned public WVS-derived instruction-tuning repository parsed for the human comparison cells. | Establishes the exact derivative and commit used to construct the 65-country human table. It does not by itself prove official survey weights or exact upstream lineage. | Direct/qualified |
| `wvs2023culturalmap` | https://www.worldvaluessurvey.org/WVSNewsShow.jsp?ID=467 | Publishes the Inglehart–Welzel cultural map for the latest joint survey round. | Supplies descriptive cultural-region annotations in the country roster. Regions are not inferred clusters, rankings, or independent sampling units. | Qualified |
| `zhao2024worldvaluesbench` | https://aclanthology.org/2024.lrec-main.1539/ | Introduces WorldValuesBench, a WVS7-derived multicultural value-awareness benchmark and its Wasserstein-based evaluation. | Provides archived benchmark context, the task lineage, and the historical 63-country comparison discussed only in the appendix. | Direct |
| `tao2024cultural` | https://doi.org/10.1093/pnasnexus/pgae346 | Compares five language models with cross-national survey values and studies country prompting as a cultural-alignment intervention. | Establishes prior evidence of cultural bias and prompt-sensitive alignment; it supports the literature position formerly assigned to the removed EthosGPT 2025 self-citation. | Direct |
| `algan2010inherited` | https://doi.org/10.1257/aer.100.5.2060 | Uses inherited trust among descendants of immigrants to study the relationship between trust and growth. | Motivates treating trust as a distinct economic coordination channel. Its causal design is not transported to model outputs. | Qualified |
| `acemoglu2001colonial` | https://doi.org/10.1257/aer.91.5.1369 | Studies institutions and comparative development using historical settler mortality as an instrument. | Motivates the institutional and responsibility channel in the economic interpretation. The paper does not reuse the instrument or infer causal development effects from language-model responses. | Qualified |
| `nekoto2020participatory` | https://aclanthology.org/2020.findings-emnlp.195/ | Demonstrates participatory research for low-resource African machine translation and releases multilingual resources. | Supports local-language participation and co-design as validity conditions beyond country coverage. | Direct |
| `mohamed2020decolonial` | https://doi.org/10.1007/s13347-020-00405-8 | Applies decolonial theory to AI as sociotechnical foresight, emphasizing power, vulnerable communities, and critical technical practice. | Grounds the discussion of local data authority, community authority, and anti-essentialist governance. | Direct |
| `sen1999development` | https://global.oup.com/academic/product/development-as-freedom-9780198297581 | Frames development as expansion of substantive capabilities and freedoms rather than income alone. | Limits the economic implications bridge: innovation growth or aggregate utility cannot exhaust social evaluation. | Direct |
| `openai2026models` | https://openai.com/index/gpt-5-6/ | Officially documents the GPT-5.6 family and public Sol label. | Verifies the public model family and label. The empirical provenance comes from frozen API request/response records, not the product page. | Direct/qualified |
| `openai2026changelog` | https://developers.openai.com/api/docs/changelog | Records dated model releases and distinguishes dated snapshots from moving identifiers. | Supports the exact GPT-5.5 snapshot notation and the disclosed absence of a dated public GPT-5.6 Sol snapshot. | Direct/qualified |
| `moran1950notes` | https://doi.org/10.1093/biomet/37.1-2.17 | Introduces Moran's statistic for spatial autocorrelation in continuous stochastic phenomena. | Defines one of two global spatial-association diagnostics applied to country-level model-version contrasts. | Direct |
| `geary1954contiguity` | https://doi.org/10.2307/2986645 | Introduces the contiguity ratio now known as Geary's C for spatially arranged observations. | Defines the complementary local-difference-sensitive spatial diagnostic used with permutation inference. | Direct |
| `conley1999gmm` | https://doi.org/10.1016/S0304-4076(98)00084-0 | Develops inference robust to cross-sectional dependence that decays with distance. | Grounds the Bartlett-kernel spatial-HAC sensitivity intervals at four distance cutoffs. | Direct |
| `anselin1988spatial` | https://doi.org/10.1007/978-94-015-7799-1 | Systematizes spatial-lag and spatial-error econometric models and their assumptions. | Grounds the maximum-likelihood spatial-error robustness specifications. The models are descriptive here, not causal spillover estimates. | Direct/qualified |
| `naturalearth` | https://www.naturalearthdata.com/ | Releases public-domain vector and raster geographic data. | Supplies country centroids and map boundaries used to construct great-circle neighbor graphs and figures. | Direct |

## High-risk interpretation boundaries retained

1. WVS cultural regions are descriptive annotations, not fixed cultural essences or inferential clusters.
2. The pinned Oxford derivative is the actual human-data source; official WVS/EVS records document the survey ecosystem but cannot restore missing survey weights or prove every upstream transformation.
3. The economic literature motivates channels linking innovation, distribution, trust, institutions, and adjustment. It does not validate a causal economic outcome from the six language-model value anchors.
4. Moran's I, Geary's C, spatial-error models, and spatial-HAC intervals diagnose cross-sectional geographic dependence. With one collection wave and two model versions, the study is not a spatiotemporal panel and does not identify diffusion or spillovers.
5. OpenAI documentation verifies public identifiers and release metadata; the released request/response ledger is the authoritative record of these calls.

## Changes in v0.4.0

1. Added the official WVS7 questionnaire, Moran, Geary, Conley, Anselin, and Natural Earth records required by the expanded appendix and spatial analysis.
2. Replaced the Nobel popular-information URL with the official 2025 press-release URL requested by the author.
3. Removed five unused bibliography records so the release contains only works cited in the paper.
4. The manuscript bibliography records a URL for each of the 23 cited works; compilation is checked in the paper repository.
5. Retained a fail-closed check that rejects the removed EthosGPT 2025 citation key and arXiv identifier.

## Author sign-off checklist

- [ ] Open all 23 URLs and approve the displayed title, authors, year, and source.
- [ ] Confirm that the linked editions of the three books are the intended editions.
- [ ] Confirm that the official-questionnaire quotations and the disclosed prompt deviations are exact.
- [ ] Approve the non-causal use of the creative-destruction, trust, and institutions literature.
- [ ] Confirm the GPT-5.5/GPT-5.6 API identifier wording against the retained execution ledger.
- [ ] Approve this manuscript as the version that supersedes, rather than cites, EthosGPT 2025.

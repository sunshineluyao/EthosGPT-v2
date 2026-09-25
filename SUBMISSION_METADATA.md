# Submission metadata

## Title

EthosGPT: Whose Values Guide Technological Change? Cultural Representation, Language-Model Updates, and Creative Destruction

## Keywords

survey representation, language model evaluation, model updates, agent systems, World Values Survey, creative destruction, responsible AI

## TL;DR

Across 64 countries, a paired model update lowers total-variation error against an unweighted survey derivative, while other corrected measures remain inconclusive; the audit separates average fidelity from representational structure.

## Author

Luyao Zhang
Duke Kunshan University
8 Duke Ave., Kunshan, Suzhou, China
lz183@duke.edu

## Abstract

Language models can frame discussions of technological change, yet updates may shift which survey responses their country-conditioned answers resemble. Prior benchmarks show that model choice and country prompting matter; whether a paired update improves average survey agreement while preserving cross-country differences under a fixed protocol remains unclear. We ask this question for AI assistants discussing innovation, distribution, and social adjustment across settings. We compare archived GPT-5.5 and GPT-5.6 Sol distributions for six World Values Survey items in 64 countries (five outputs per model–country–item) with an unweighted public survey derivative. GPT-5.6 reduces mean total-variation error by 0.0080 (95% country-bootstrap BCa CI [-0.0107,-0.0050]), while globally corrected changes in ordered error, country-profile error, and cross-country relational measures remain inconclusive. The reduction concentrates in income distribution and responsibility; prompt-label inconsistencies limit item-level interpretation, and exploratory region contrasts differ. Tracing disagreement from answer categories to country profiles and relations separates average fidelity from representational structure without equating survey fit with welfare. This audit identifies questions and settings that merit scrutiny before using country-conditioned outputs. Population-weighted survey targets, local-language prompts, and community validation can test how far these patterns generalize.

## Open science

The companion repository archives outputs and offline reproduction code.

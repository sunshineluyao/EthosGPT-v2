# Submission metadata

## Title

EthosGPT: Whose Values Guide Technological Change? Cultural Representation, Language-Model Updates, and Creative Destruction

## Keywords

survey representation, language model evaluation, model updates, agent systems, World Values Survey, creative destruction, responsible AI

## TL;DR

For the archived unweighted survey derivative, GPT-5.6 reduces mean TVD chiefly on Q106/Q108; other corrected global metrics remain uncertain, and prompt wording limits interpretation.

## Abstract

Model updates can change country-conditioned answers to survey questions. Prior benchmarks compared models and versions; here we compare GPT-5.5 and GPT-5.6 Sol under one fixed English elicitation on six World Values Survey items in 64 countries, with five archived generations per cell. The comparison target is an unweighted public derivative of country responses, not a measure of culture, individual benefit, or welfare. GPT-5.6 lowers mean total-variation distance (TVD) by $0.0080$ (95% BCa CI $[-0.0107,-0.0050]$); the other four corrected global metric contrasts are inconclusive. The reduction concentrates in income distribution (Q106) and responsibility (Q108). Excluding Q106 leaves a TVD contrast of $-0.00433$ (CI $[-0.00698,-0.00138]$), while excluding both Q106 and Q108 leaves $-0.00024$ (CI $[-0.00313,0.00286]$). Q106 and Q121 have disclosed prompt-label discrepancies; item omissions cannot recover results from corrected prompts. Averaging five observed outputs removes only 1.18--1.31% of single-run squared probability error. An exploratory grouping by economic theme describes survey mismatch, not downstream decisions. Archived outputs and code permit offline recomputation; official survey weighting, translated prompts, and user outcomes require separate evidence.

## Open science

The companion repository archives outputs and offline reproduction code.

# Submission metadata

## Title

EthosGPT: Whose Values Guide Technological Change? Cultural Representation, Language-Model Updates, and Creative Destruction

## Keywords

survey representation, language model evaluation, model updates, agent systems, World Values Survey, creative destruction, responsible AI

## TL;DR

For the archived unweighted survey derivative, GPT-5.6 reduces mean TVD chiefly on Q106/Q108; other corrected global metrics remain uncertain, and prompt wording limits interpretation.

## Abstract

When language models are updated, the survey responses they assign to a named country may change. We compare two archived model releases, GPT-5.5 and GPT-5.6 Sol, using one English elicitation of six World Values Survey items in 64 countries, with five generations per item and country. Against an unweighted public derivative of survey responses, GPT-5.6 lowers mean total-variation distance (TVD) by $0.0080$ (95% country-bootstrap BCa CI $[-0.0107,-0.0050]$); the other four globally corrected metric contrasts are inconclusive. Most of the signed TVD reduction comes from income distribution (Q106) and responsibility (Q108). Q106 and Q121 contain documented prompt-label discrepancies, which limit interpretation of item-specific changes. Five-run averaging removes only 1.18--1.31% of single-run squared probability error among the observed outputs. An exploratory six-group geographic aggregation shows heterogeneous changes. These measurements describe agreement with a particular survey derivative, not individual benefit, cultural ground truth, or economic welfare. Archived model outputs enable offline replication.

## Open science

The companion repository archives outputs and offline reproduction code.

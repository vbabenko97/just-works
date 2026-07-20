# Scientific rigor and source routing

## Contents

- Evidence hierarchy
- Evidence ledger
- Citation and identifier checks
- Data provenance
- Computational reproducibility
- Statistical and analytical checks
- Figures and manuscripts
- Domain source routing
- Safety, privacy, and ethics
- Uncertainty and stopping rules

## Evidence hierarchy

Match the source to the claim rather than treating all citations as interchangeable.

1. Prefer original datasets, primary studies, official database records, protocols, standards, and regulatory or institutional documents for decisive factual claims.
2. Use systematic reviews, meta-analyses, consensus statements, and authoritative guidelines to establish the broader evidence state.
3. Use reputable narrative reviews and secondary sources for orientation, terminology, and discovery of primary sources.
4. Use preprints, conference abstracts, vendor material, and model predictions only with clear labels and independent verification proportionate to the claim.
5. Do not cite a search-result snippet, generated summary, or secondary description as though it were the underlying source.

For current or unstable facts, record the access date and verify the source live. For historical findings, use the original publication and any later correction, retraction, or replication that materially changes interpretation.

## Evidence ledger

For substantial research, maintain a compact ledger with these fields:

- Claim ID and concise claim.
- Claim type: observation, reported result, calculation, inference, hypothesis, or recommendation.
- Source title and source class.
- Stable identifier: DOI, PMID, PMCID, accession, trial ID, database ID, standard number, or canonical URL.
- Exact supporting location: page, section, figure, table, line, record field, or query result.
- Population, system, assay, dataset, or conditions to which the claim applies.
- Effect estimate, units, denominator, uncertainty, and direction when quantitative.
- Contradicting or qualifying evidence.
- Confidence and the reason for it.
- Verification status and reviewer notes.

A ledger is useful only when it links claims to inspectable evidence. A decorative bibliography stapled to confident prose is not an evidence system.

## Citation and identifier checks

Require the reviewer to verify that:

- The cited source exists and the identifier resolves.
- The source supports the exact claim, not merely the general topic.
- The direction, magnitude, units, population, and timeframe match the source.
- A review article is not used to obscure a weak or missing primary source.
- Retracted, corrected, superseded, or duplicated records are identified.
- Preprints and non-peer-reviewed material are labeled.
- Database records include release/version and access date when the record can change.
- Gene, transcript, protein, compound, variant, structure, and disease identifiers are not conflated across namespaces or species.

Never infer a DOI, PMID, accession, or record ID from a title pattern. Verify it.

## Data provenance

For every dataset, capture:

- Origin, owner or custodian, license, consent or permitted use, and access restrictions.
- Download or extraction date, release, accession, query, filters, and raw file names.
- Checksums or immutable references when practical.
- Schema, units, coding conventions, sample and feature identifiers, missing-value conventions, and reference assembly or ontology versions.
- Inclusion, exclusion, deduplication, linkage, and label-generation rules.
- Every transformation from raw input to analysis-ready data.
- The location and status of intermediate and final artifacts.

Keep raw inputs immutable. Do not overwrite them with cleaned or normalized data. When proprietary or sensitive data cannot be copied, record a reproducible query or manifest without exposing protected content.

## Computational reproducibility

For computed work, require:

- Executable scripts, notebooks, commands, workflow definitions, and configuration files.
- Environment specification and exact package, model, database, reference, and runtime versions.
- Random seeds, deterministic settings, hardware-sensitive settings, and known nondeterminism.
- Logged parameters, resource requests, warnings, failures, retries, and manual interventions.
- Unit tests or sanity checks for fragile transformations and calculations.
- Checksums or hashes for important inputs and final artifacts.
- A concise run order or entrypoint that a qualified researcher can follow.
- A statement of what could not be reproduced from the available environment or permissions.

For HPC or remote jobs, include scheduler configuration, requested resources, wall time, storage locations, and output retrieval steps. Ask before expensive runs or use of restricted infrastructure.

## Statistical and analytical checks

Select checks based on the data-generating process and method. Common checks include:

- Experimental unit versus measurement unit and the risk of pseudoreplication.
- Sample size, missingness, censoring, attrition, class imbalance, and selection effects.
- Randomization, blinding, batch structure, site effects, temporal drift, and confounding.
- Train-validation-test separation, feature leakage, target leakage, and repeated-subject leakage.
- Model assumptions, calibration, convergence, identifiability, overfitting, and extrapolation.
- Multiple comparisons, selective reporting, subgroup multiplicity, and data-dependent analysis choices.
- Effect sizes, uncertainty intervals, denominators, absolute versus relative effects, and practical significance.
- Sensitivity to preprocessing, thresholds, priors, model class, inclusion rules, and influential observations.
- External validation, replication, negative controls, positive controls, and baseline comparisons.

Do not treat a p-value, benchmark score, or cross-validation average as a complete scientific result. Require context, uncertainty, and failure analysis.

## Figures and manuscripts

For numerical figures:

- Generate the figure from retained code and traceable data.
- Verify labels, units, scales, transformations, uncertainty displays, sample counts, and legends.
- Avoid misleading axis truncation, inappropriate smoothing, hidden exclusions, and color encodings that obscure groups or accessibility.
- Ensure every plotted statistic matches the manuscript and evidence ledger.
- Include enough caption detail to identify the population, statistic, uncertainty, model or test, and major preprocessing.

For manuscripts:

- Keep claim-level citations and avoid citation dumping at paragraph ends.
- Make methods sufficient for a qualified reader to reproduce the analysis.
- Distinguish prespecified, confirmatory, exploratory, and post hoc analyses.
- Report negative, null, and conflicting findings that affect interpretation.
- Align abstract, main text, tables, figures, supplements, and conclusions.
- Prevent causal language when the design supports only association.
- Ensure limitations are specific and connected to the claims they constrain.

## Domain source routing

Choose only sources relevant to the question. The following are common routes, not a command to query everything.

### General literature and scholarly records

- PubMed or Europe PMC for biomedical literature discovery and identifiers.
- Crossref and publisher records for DOI and publication metadata.
- Trial registries and official study records for registration, status, outcomes, and protocol information.
- Retraction and correction notices from publishers and indexing services.

### Genes, genomes, variants, and expression

- Ensembl and NCBI resources for genome, gene, transcript, and reference sequence context.
- ClinVar for clinical variant assertions, including review status and conflicts.
- GEO and other primary repositories for expression and functional genomics datasets.
- Appropriate organism-specific databases when they are authoritative for the species.

Record assembly, annotation release, transcript, genome build, and species. Never compare coordinates or variant descriptions across builds without conversion and validation.

### Proteins, pathways, and structures

- UniProt for protein records, function, sequence, and annotation evidence.
- PDB for experimentally determined structures and associated metadata.
- Reactome and other curated pathway resources for pathway context.
- Appropriate structure-prediction sources when experimental structures are unavailable, clearly labeling predictions and confidence.

Distinguish isoforms, species, experimental structures, homology models, and predictions.

### Compounds, targets, and cheminformatics

- ChEMBL for bioactivity and target-linked compound data.
- PubChem and authoritative chemical registries for identifiers and properties.
- Primary assay publications and protocol records for context behind activity values.

Track salt form, stereochemistry, assay type, units, endpoint, target construct, species, and measurement conditions. Do not compare IC50, EC50, Ki, Kd, and percent inhibition as interchangeable values.

### Single-cell and omics analysis

Use original repository records, study metadata, reference annotations, and established packages appropriate to the modality. Preserve sample-level design, donor identity, batch, chemistry, reference build, filtering, normalization, dimensionality reduction, clustering, annotation method, and differential analysis settings.

Avoid treating cells as independent biological replicates when donors or samples are the experimental units. Check ambient contamination, doublets, batch effects, overclustering, annotation circularity, and pseudobulk or mixed-model alternatives.

### Clinical and translational questions

Use primary studies, systematic reviews, current professional guidelines, official regulatory information, and trial records. Weight evidence by study design, population relevance, endpoint quality, risk of bias, and recency.

Do not turn a research synthesis into patient-specific diagnosis or treatment advice. Require qualified clinical review and state when evidence does not support a clinical action.

## Safety, privacy, and ethics

Prompts should establish boundaries appropriate to the work:

- Use only data and systems the user is authorized to access.
- Minimize movement of personal, controlled, proprietary, or sensitive data.
- Follow consent, data-use agreements, IRB/IACUC, biosafety, export-control, licensing, and institutional requirements.
- Do not bypass access controls or safety review to make a workflow appear complete.
- Require human review before operationalizing clinical, regulatory, environmental, or experimental recommendations with material consequences.
- Separate computational hypothesis generation from authorization to conduct an experiment.

## Uncertainty and stopping rules

Require the output to identify:

- What is known directly from evidence.
- What was calculated and from which inputs.
- What is inferred and under which assumptions.
- What remains unknown or disputed.
- Which missing evidence most affects the conclusion.
- What result or new evidence would change the decision.

Stop or narrow the claim when:

- Essential data or metadata are unavailable.
- Source identity or citation support cannot be verified.
- The method is invalid for the available design or sample.
- Tool output is incomplete, inconsistent, or outside its documented scope.
- Permissions, privacy, safety, ethics, or cost boundaries are unresolved.
- The requested confidence exceeds what the evidence can support.

Report the blocker, attempted work, effect on confidence, and smallest defensible next step. Do not patch a scientific gap with eloquence. Nature has remained stubbornly unimpressed by formatting.

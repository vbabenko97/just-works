# Medical imaging and clinical-AI red-team checklist

Apply when the proposal uses retrospective clinical data, imaging, survival/prognostic modelling, foundation models, representation learning, radiomics, or AI intended to inform health research.

## Clinical question and estimand
- Define target population and clinical setting.
- Define index time/prediction time unambiguously.
- Separate diagnostic, prognostic, causal, and treatment-response questions.
- Name the outcome and horizon; avoid changing them after looking at results.
- For repeated scans, state whether the estimand is conditional on receiving repeat imaging and address informative observation.

## Data provenance and leakage
- Split by patient, not image, when multiple scans belong to a patient.
- For temporal validation, keep post-cutoff patients and information out of every development step, including self-supervised pretraining if the claimed validation requires that separation.
- Fit imputation, scaling, dimensionality reduction, feature selection, and tuning inside development folds only.
- Check whether text reports leak outcomes, future treatment, post-index events, or labels.
- Audit duplicated examinations, near-duplicates, and derived records.

## Outcome, censoring, missingness
- Establish outcome ascertainment and administrative cutoff.
- Do not treat unavailable follow-up as benign missingness.
- State censoring assumptions and diagnostics for IPCW/time-dependent metrics.
- Consider selection into the analysable cohort and sensitivity analyses.
- Separate all-cause mortality from cause-specific outcomes; missing cause does not affect all-cause mortality but matters for cause-specific endpoints.

## Sample size and model complexity
- Justify model complexity against sample size and event information, not total image count.
- For repeated-landmark data, count unique patients/deaths and clustered effective information, not just rows.
- Predefine dimensionality reduction/regularisation strategy.
- Keep identical tuning budgets for fair incremental comparisons where appropriate.

## Evaluation
- Compare learned representations against strong clinical and explicit-imaging baselines, not straw-man baselines.
- Use paired comparisons on identical held-out patients when claiming incremental value.
- Report discrimination and calibration; include prediction error when appropriate.
- For clinical utility claims, consider decision-analytic evidence. Do not infer utility from AUC alone.
- Use uncertainty intervals and predefine how effect size will be interpreted.
- Make null/neutral findings publishable and scientifically meaningful.

## Temporal, scanner, site, and spectrum shift
- Test scanner/protocol effects and scanner-calendar-time confounding.
- Distinguish temporal validation from external validation.
- Do not call a disease-specific public dataset a full validation of an all-comer heterogeneous primary estimand if variables/population differ.
- State transportability limitations and what a future multi-centre validation would need.

## Interpretability and safety
- Do not overstate post-hoc saliency/attribution as mechanistic explanation.
- Prefer anatomically or clinically structured outputs when methodologically justified.
- State that research-stage models are not clinical decision systems unless deployment is genuinely part of the project.
- Consider memorisation/privacy tests before releasing weights trained on sensitive data.

## Sex, gender, age, diversity
- Distinguish biological sex from social/cultural gender.
- If only sex is recorded, say so.
- Prespecify subgroup calibration/discrimination where sample support allows.
- Describe clinically selected referral populations honestly; “all-comer” within a PET/CT service is not the general population.

## Reporting and governance
- Use current prediction-model reporting/risk-of-bias standards when applicable, e.g. TRIPOD+AI and PROBAST+AI.
- Keep patient-level data in the approved environment.
- Align open science with GDPR, ethics, consent/legal basis, IP, and hospital governance.

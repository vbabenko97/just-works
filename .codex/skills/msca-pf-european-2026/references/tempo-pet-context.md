# TEMPO-PET context snapshot

Snapshot assembled from user-supplied files dated through 29 August 2026. This is context, not a live status file. Always read newer uploads/correspondence before acting on an open item.

## Proposal identity

- Acronym: TEMPO-PET.
- European Postdoctoral Fellowship, 24 months, Austria.
- Beneficiary: Medical University of Vienna (MedUni Vienna).
- Host: Department of Biomedical Imaging and Image-Guided Therapy, Division of Nuclear Medicine.
- Supervisor: Dr Clemens Spielvogel, Junior Group Leader / Spielvogel Lab.
- Primary Part A descriptor: Life Sciences -> Diagnostic tools, therapies and public health -> Radiology, nuclear medicine and medical imaging.
- Project title: Incremental Prognostic Value and Dynamic Risk Updating from Learned Whole-Body FDG PET/CT Representations in a 15-Year Clinical Cohort.

## Scientific spine

Central question: whether learned whole-body FDG PET/CT representations add prognostic value for all-cause mortality beyond clinical/oncological variables and explicit imaging biomarkers, and whether serial scans allow risk to be updated over time.

Current B-1 structure:
- O1 cohort, feasibility, baselines.
- O2 multimodal self-supervised representation learning with PET/CT ablations and representation trajectories.
- O3 incremental-value comparison on a temporal hold-out.
- O4 scan-driven dynamic risk updating plus an external-validation package/conditional validation route.

Primary design snapshot:
- retrospective routine-care cohort;
- approximately 20,000 FDG PET/CT examinations from approximately 10,000 patients over approximately 15 years;
- first eligible scan as index;
- all-cause mortality, 2-year primary horizon, 1-year secondary, 5-year exploratory conditional on feasibility;
- primary comparison: all predictors vs clinical/oncological + explicit imaging biomarkers on identical temporal hold-out patients;
- primary measure: paired difference in cumulative/dynamic time-dependent AUC at 2 years with IPCW;
- calibration and prediction-error measures co-reported;
- repeated scans evaluated with scan-driven landmarking.

Do not assume any statistical choice marked for specialist confirmation is settled until the latest source says so.

## Researcher profile relevant to fit

- PhD in Computer Science awarded 04/08/2025; dissertation on hierarchical classification for pathology diagnosis from multimodal medical images.
- Medical-imaging ML experience spanning ultrasound, CT, MRI-related workflows and clinical validation.
- Research outputs include medical-imaging/clinical-AI work and physiological time-series collaboration.
- Production AI/ML engineering experience adds large-scale pipelines, systematic evaluation, software reliability, observability, and reproducible engineering.
- Fellowship narrative: transition from strong ML engineering + biomedical-imaging research toward independent EU clinical-AI research, with added survival biostatistics, clinical prediction methodology, nuclear-medicine expertise, grant leadership, and network development.

## Training/transfer spine

Host -> fellow:
- PET/CT physics/acquisition/interpretation;
- survival biostatistics including landmarking/competing risks;
- clinical prediction methodology;
- research leadership, grant writing, open science.

Fellow -> host:
- reproducible ML engineering and leakage control;
- production-quality pipeline practices;
- automated text processing / information extraction;
- code review and technical collaboration with students.

## Dated open-item snapshot

The 29 August status/checklist files reported six unresolved markers across the canonical B-1/B-2 package: three owned by Clemens, two by Research Service, one by a host statistician. Examples included statistical sign-off on horizons/primary measure, host continuation wording, Pfizer naming, and Research Service wording for inter-relationship / PIC-department relation. The status file also treated the B2 submission gate as red because working/editorial material remained.

The user subsequently supplied review copies and a Part-A-copy-v4. Therefore, never quote “six open markers” as current without re-reading the latest files. Review copies may intentionally suppress editorial markers and do not prove the canonical questions are resolved.

## Current proposal strengths to preserve during editing

- Clear incremental-value question rather than “AI predicts outcome” in isolation.
- Strong temporal/leakage-control emphasis.
- Explicit feasibility gates and fallbacks.
- Honest conditional external-validation route.
- Operational training / two-way transfer matrix.
- Career transition has a credible before/after logic.
- Impact messaging is restrained by the need for external/prospective evaluation before clinical use.

## High-value red-team pressure points

- Statistical sign-off and exact censoring/AUC estimator choices.
- Whether dataset/cohort counts and annual-volume statements are host-confirmed.
- Whether “first/to our knowledge” novelty survives a fresh literature search in late August/early September 2026.
- Whether external-validation Route B is described as transportability/exploratory rather than equivalent to the primary estimand.
- Scanner-calendar-time confounding and follow-up support.
- Exact distinction between sex and gender data.
- Host/supervisor commitments during supervisor's temporary research stay abroad.
- Part A/B ethics and non-EU activity wording.
- Submission version provenance and removal of all working/editorial material.

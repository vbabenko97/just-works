# Sources and authorship

Package: `ml-provenance-and-handoff` · Version 1.0.0 · Sources reviewed 2026-10-13

## Authorship

Written for this repository in October 2026. The workflow, templates, and evaluation cases are original. The design draws on a private research brief, which is not distributed, and on the primary sources below. The brief identified [Emily2040/data-science-agent-skills](https://github.com/Emily2040/data-science-agent-skills) as a related design; it could not confirm that repository's license, so no text from it is included.

## Sources

| Source | URL | Used for |
|---|---|---|
| PyTorch: Reproducibility | https://docs.pytorch.org/docs/stable/notes/randomness.html | Limits of fixed seeds; deterministic algorithms |
| Hugging Face Transformers: Trainer and TrainingArguments | https://huggingface.co/docs/transformers/main_classes/trainer | `seed`, `data_seed`, `full_determinism`, `model_init` |
| scikit-learn: Common pitfalls, Controlling randomness | https://scikit-learn.org/stable/common_pitfalls.html | Seeds for estimators and splitters |
| Agent Skills specification | https://agentskills.io/specification | Package layout |

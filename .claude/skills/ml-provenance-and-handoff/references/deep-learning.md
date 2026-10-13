# Deep-learning provenance

Add these items to the `config`, `environment`, `seeds`, and `artifacts` sections of the run record.

| Item | Record |
|---|---|
| Base model | Hub ID or path plus the exact revision (a commit hash, not a moving name such as `main`) |
| Tokenizer or processor | Its own ID and revision |
| Software stack | Exact versions of the framework (for example PyTorch), the model library, CUDA, cuDNN, and the GPU driver |
| Hardware | GPU model and count; distributed setup (world size, strategy) |
| Precision | fp32, fp16, bf16, or mixed precision, and any loss scaling |
| Optimization | Optimizer, learning-rate schedule and warmup, per-device batch size, gradient accumulation, effective batch size, steps or epochs |
| Seeds | Initialization seed, data-order seed (for example `data_seed` in Hugging Face `TrainingArguments`), and split seed |
| Determinism settings | Whether deterministic algorithms were enforced, and the speed cost observed |
| Checkpoints | Save interval, the selection rule (for example best validation macro-F1), the selected step, and the checkpoint hash |
| Resumption | Whether the run resumed from a checkpoint, and which one |

## Limits of seeds

A fixed seed makes a run repeatable at best on the same software and hardware. PyTorch documents that completely reproducible results are not guaranteed across releases, individual commits, or platforms, nor between CPU and GPU executions, even with identical seeds. Some GPU operations and reduced-precision arithmetic are nondeterministic unless deterministic algorithms are enforced, and enforcing them costs speed.

Consequences:

- Do not claim exact reproducibility. Report the difference observed when a run is repeated.
- A difference between two configurations, each trained with one seed, says little when seed-to-seed variation can be as large. Repeat both configurations over several seeds that vary initialization and data order, and compare the distributions. The number of seeds follows from the observed spread and the compute budget.
- Selecting a checkpoint by its validation score makes that score optimistic. Report the selected checkpoint on separate evaluation data.

Sources: [PyTorch, Reproducibility](https://docs.pytorch.org/docs/stable/notes/randomness.html); [Hugging Face Transformers, Trainer and TrainingArguments](https://huggingface.co/docs/transformers/main_classes/trainer) (`seed`, `data_seed`, `full_determinism`, `model_init`).

---
name: ml-provenance-and-handoff
description: Use when setting up an ML experiment before its first material training run, when resuming or auditing earlier ML runs, and when reporting or handing off a model result. Records each run in a plain JSON file (data identity, split, code revision and dirty state, environment, configuration, seeds, metrics, artifacts), keeps failed runs, and assembles a result note with reproduction commands, assumptions, limitations, and reproduction status. Covers classical ML and deep-learning checkpoints. Not for ML system design documents or production deployment.
---

# ML provenance and handoff

Make every reported number traceable to the data, code, split, environment, and configuration that produced it.

## When to set up

Set up records before the first material run: a run whose result can inform a decision or appear in a report. Exploration before that point needs no records, but its numbers are not reported. When resuming work, read the existing run records first and reuse the complete ones.

## Run records

Use the project's existing run location and format if it has one, including MLflow or DVC when the project already uses them. Otherwise create `runs/<run-id>/run.json` from [assets/run.json](assets/run.json) and keep predictions, logs, and other artifacts in the same directory. Plain files are enough; do not add tracking servers, registries, or other services for this. For an exploratory question, the default is one script or notebook, one run record per run, and a short report; add structure only when the existing project already needs it.

Write the record when the run starts (status `running`) and update it when the run ends. Record failed and aborted runs with their failure. Do not delete them or keep only the winners.

Capture each field from evidence:

| Field | How to capture |
|---|---|
| Code revision | `git rev-parse HEAD` |
| Dirty state and source snapshot | `git status --porcelain`. When it lists changes, save `git diff HEAD` in the run directory, and copy every untracked file the run uses (code, configuration) into a source snapshot there, with each file's hash. A list of untracked file names cannot reproduce their content. Outside git, snapshot every source file the run uses. |
| Data identity | `sha256sum` or `shasum -a 256` for files; a snapshot ID, or the query with an as-of timestamp, for warehouse tables; an existing DVC or lakeFS reference |
| Split identity | Hash of the persisted split assignments named in the split configuration |
| Environment | Interpreter version; the lock file and its hash, or a frozen package list (`uv pip freeze`, `pip freeze`, `conda env export`); operating system; hardware |
| Configuration and seeds | The fully resolved configuration, every seed used (model, data order, split), and the command line |
| Metrics | Per fold or forecast origin as well as aggregates, labeled with the evaluation set |
| Artifacts | Path and sha256 of each model file, prediction file, and log |

Write `null` or "unknown" for anything that could not be captured. Never fill a field with a guessed value.

Remove credentials before writing anything to the run directory. In commands, configuration, environment captures, URLs, and copied source, replace tokens, passwords, and keys with the name of the variable or secret that holds them.

## Missing provenance

A result that cannot be traced to its code, data, split, and configuration is not reproducible and not ready for handoff, whatever its score; say so plainly. Reconstruct provenance only from evidence such as commit history, saved logs, and file timestamps. When that fails, re-run from a committed revision with full records, and re-run the baseline under the same conditions before comparing the two.

## Reproduction

Re-run decisive results when practical within the authorized compute budget, and record the outcome: reproduced with the observed difference, not reproduced with the reason, or skipped with the reason. Many GPU and mixed-precision setups do not guarantee exact reproduction; report the observed variability instead of claiming it. For deep-learning runs, read [references/deep-learning.md](references/deep-learning.md).

## Handoff

Assemble [assets/result-handoff.md](assets/result-handoff.md):

- the claim and its status: validated, exploratory, not reproducible, or no improvement over baseline;
- the evidence chain from run ID to code revision, data, split, configuration, and artifacts;
- exact commands that check out the recorded revision, apply the saved tracked-file diff when present, restore the untracked source snapshot, and reproduce the result, with credentials replaced by variable names;
- assumptions, limitations, known failure modes, reproduction status, and checks not run.

The claim matches the evidence. A result with contaminated evaluation or incomplete provenance is reported as exploratory, not validated. Notebooks are fine for exploration; a reported result needs a repeatable, non-manual way to run it.

## Outputs

| Output | Template |
|---|---|
| Run record | [assets/run.json](assets/run.json) |
| Result and handoff note | [assets/result-handoff.md](assets/result-handoff.md) |

Template filenames are defaults; use the project's existing locations when it has them. Sources and authorship: [SOURCES.md](SOURCES.md).

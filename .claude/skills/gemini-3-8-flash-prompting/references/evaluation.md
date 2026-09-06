# Evaluation procedure

The package includes offline structural checks and manual behavioral test cases.
It contains no live Gemini evaluation runner and no claims of measured uplift.

## Evaluate two different things

First, test the **prompt-authoring skill**: invoke it with a case from
`tests/cases.json` and review the returned prompt and notes against the case's
acceptance criteria. These cases are instructions for a human or an authorized
agent evaluator, not completed experiments.

Second, test the **generated prompt** on Gemini with actual task inputs, only
when the user authorizes remote execution and supplies the appropriate access.
Do not transmit private documents or incur API charges merely to validate a skill.

## Controlled comparison

Save the original and revised prompt. Keep the model ID, API surface, tool set,
input data, thinking level, and output limits fixed while comparing wording.
Then test settings separately. Include ordinary cases, missing evidence,
conflicting requirements, malformed input, and instruction-like source material.
Repeat enough samples to expose variability before treating a small difference
as an improvement. Record failures, not just successful examples.

Suggested dimensions: task correctness, constraint compliance, evidence support,
parse/schema validity, appropriate tool use, missing-data handling, and answer
length. For real runs, also record observed latency, token usage, and tool counts.
Do not substitute subjective preference for task correctness.

## Results record

Use an honest status: `not_run`, `passed`, `failed`, or `inconclusive`.
Record the prompt revision, test input, expected result, actual result, model,
API surface, run date, settings, and evaluator. Do not fabricate unavailable
latency, cost, confidence, or accuracy measurements.

## Offline commands (optional; Python 3.9+)

From the extracted package directory:

```bash
python3 scripts/validate.py
python3 -B tests/test_installer.py
```

These use only the Python standard library and local files. They do not call an
LLM. Installer tests use temporary home directories and do not install the skill
into the real home directory. They invoke local Bash and the checksum utility.
The installer itself does not require Python.

# Current Anthropic guidance for Claude Science prompting

Last reviewed: 2026-07-20

Use this reference when the task depends on current Claude Science behavior, current Claude model guidance, research mode, tool use, connectors, skills, or API settings. Verify the live official source whenever web access is available. Product beta behavior, model names, parameters, and feature availability can change.

## Claude Science product behavior

Anthropic announced Claude Science on 2026-06-30 as a beta scientific workbench for macOS and Linux. The announcement describes:

- A coordinating agent with curated scientific skills and connectors.
- Specialist and user-created agents.
- Integration with literature, scientific databases, local or remote compute, SSH, and HPC workflows.
- Rich scientific artifacts such as figures, manuscripts, structures, and tracks together with the code and environment that created them.
- Auditable message and artifact history for validation and reproduction.
- A reviewer agent that checks citations, calculations, untraceable numbers, and consistency between figures and underlying code.
- Approval before reaching new resources or submitting compute jobs, with the ability to review or revoke decisions.
- Local or lab-infrastructure operation intended to keep large or sensitive datasets in their existing environment while sending only needed context to Claude.
- More than 60 scientific databases and early emphasis on biology and biomedical research, including resources such as UniProt, PDB, Ensembl, Reactome, ClinVar, ChEMBL, and GEO.
- Support for reusable lab pipelines as skills and preferred tools as connectors.

Prompting implication: specify the scientific contract and review criteria. Do not recreate the entire orchestration layer in prose or require every database, skill, agent, and compute resource to be used.

Official source:
https://www.anthropic.com/news/claude-science-ai-workbench

## Prompt engineering prerequisites

Anthropic's prompt engineering overview says prompt iteration should begin with:

1. Clear success criteria.
2. A way to test against those criteria.
3. A first draft prompt.

Not every failure should be fixed with prompt text. Model selection, tool design, data quality, or system architecture may be the better intervention.

Official source:
https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview

## General Claude prompting guidance

The current best-practices reference emphasizes:

- Clear, direct instructions and explicit output requirements.
- Context or rationale for unusual instructions.
- Relevant, diverse, structured examples when examples are genuinely needed.
- Descriptive XML tags for complex prompts with mixed instructions, materials, examples, and variable inputs.
- Long documents near the beginning and the decisive query near the end for long-context tasks.
- Positive formatting instructions rather than long lists of prohibitions.
- Explicit but calibrated tool guidance.
- Parallel tool use for independent calls and sequential calls for dependencies.
- Adaptive thinking and effort configuration for current models where supported, rather than legacy manual thinking budgets.
- Self-checking against concrete criteria.
- Structured research with success criteria, source verification, competing hypotheses, confidence tracking, and persistent research notes for complex work.
- Natural subagent orchestration, with explicit limits when simple or stateful work should remain direct.
- Prompt chaining when intermediate outputs must be inspected or a controlled pipeline is required.

Model-specific behavior differs. Verify the current model page before recommending settings or migration changes.

Official source:
https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

## Evaluations

Anthropic's evaluation guidance recommends success criteria that are specific, measurable, achievable, and relevant. Evaluation sets should mirror real task distributions, include edge cases, automate grading when practical, and use detailed rubrics. Code-based grading is preferred for exact checks; human or validated LLM grading is used for nuanced scientific judgments.

Prompting implication: production prompt work should include representative scientific cases and should not claim improvement from wording alone.

Official source:
https://platform.claude.com/docs/en/test-and-evaluate/develop-tests

## Tool use

Claude decides whether to call a tool from the user's request, current context, tool description, and tool-choice configuration. Tool triggering can be steered through the prompt, but hard guarantees belong in tool configuration when supported. Tool schemas and descriptions should state the capability, inputs, outputs, and boundary precisely. Independent tool calls can run in parallel; dependent calls should remain sequential.

Prompting implication: name tools that matter, state when they should be used, and define approval or failure behavior. Avoid “always use every tool.”

Official source:
https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview

## Research mode

Anthropic describes Claude Research as an agentic, iterative search process that explores multiple angles and returns cited findings. Web search must be enabled for web research, and connected internal sources can also be included when available.

Prompting implication: direct Research toward a bounded question, relevant source classes, explicit citation verification, and a stopping criterion. Do not use a long-horizon research workflow for a question answerable by one authoritative source.

Official source:
https://support.claude.com/en/articles/11088861-use-research-on-claude

## Skills and connectors

Anthropic describes skills as reusable specialized knowledge and workflows and connectors as MCP-based access to external tools and data. Availability and behavior depend on product, plan, organization settings, code execution, and connection mode.

Prompting implication: refer to an enabled skill or connector by its actual capability. Do not assume a connector, database, or permission exists merely because Claude Science can support it in principle.

Official sources:
https://support.claude.com/en/articles/12512180-use-skills-in-claude
https://claude.com/docs/connectors/overview

## Version-sensitive recommendations

When generating an API split or runtime suggestion:

- Verify the current supported model names and exact model strings.
- Verify whether thinking is always on, adaptive, optional, or unsupported for the chosen model.
- Verify effort values, tool versions, beta headers, strict-schema support, and permission controls.
- Keep runtime settings out of the natural-language prompt when they belong in API configuration.
- Do not recommend maximum effort, every tool, or many subagents without evaluation evidence.
- State the date of verification for production configurations.

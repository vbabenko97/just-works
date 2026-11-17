---
name: csharp-code-writer
description: Use when C# (.cs) work is delegated as an independent workstream, such as one of several parallel changes. Applies project C# standards and runs quality checks. For other C# edits the main session loads the csharp-coding skill and edits directly.
tools: Write, Read, Edit, Bash, Glob, Grep, Skill
model: inherit
skills:
  - csharp-coding
  - minimal-coding
---

Write clean, type-safe C# following project standards.

## Before Writing

Read the files you will change before making edits. For single-file edits, reading the target file is sufficient. For cross-cutting changes, read the directly affected modules. Check the relevant .csproj for target framework, nullable settings, and project conventions.

When adding or changing HTTP API endpoints, load the `rest-api` skill with the Skill tool.

## Quality

Write code that passes the project's build, formatter, and analyzers. After editing, discover them from project config (`.csproj`, `.editorconfig`) and run `dotnet build` on the affected project plus `dotnet format` if configured, unless a project hook already does it.

## Report

End with a short report: files changed, checks run with their results, checks skipped and why, and assumptions made.

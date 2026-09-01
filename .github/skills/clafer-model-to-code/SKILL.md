---
name: clafer-model-to-code
description: "Use when translating app requirements and Clafer architecture into generated artifacts, implementation interfaces, and scenario-traceable tests."
---

# Clafer Model to Code

## Purpose

Use this workflow when an app provides:
- Requirements in `.lando`
- Clafer model files (`prelude.cfr`, `architecture.cfr`)

Generate and validate:
- `requirements.generated.cfr`
- assembled model and Clafer instances
- JSON instance artifacts
- traceability PlantUML and Markdown report
- requirement coverage check
- executable Kotlin tests

## Expected App Inputs

- `apps/<app-name>/requirements/*.lando`
- `apps/<app-name>/model/prelude.cfr`
- `apps/<app-name>/model/architecture.cfr`
- `apps/<app-name>/source/`

## Standard Commands

From repository root (single Makefile workflow; no per-app Makefile required):

```bash
make generate APP=<app-name>
make verify APP=<app-name>
make clean APP=<app-name>
```

Example:

```bash
make verify APP=token
```

## Quality Gates

- Clafer model parses and instantiates
- At least one JSON instance is produced (default target is 10)
- Traceability artifacts are regenerated from fresh instances
- Coverage check passes for generated requirements vs architecture links
- Kotlin tests pass

## Notes

- SysML generation is intentionally excluded.
- PNG rendering needs host `plantuml` and `dot`; otherwise only `.plantuml` is generated.

# rde-framework

Tooling repository meant to make specification-driven development easier. Inspired by FreeAndFair's [Rigorous Digital Engineering](https://rde.freeandfair.us/Rigorous%20Digital%20Engineering%20for%20VoteSecure%20-%20Full%20Article.pdf) handbook.

## Relevant Technologies

- [Lando DSL](https://github.com/GaloisInc/BESSPIN-Lando): requirements language used for `.lando` requirement files
- [Clafer](https://github.com/gsdlab/clafer): modeling and constraint language used for architecture definitions and instance generation
- [Choco Solver](https://choco-solver.org/): solver backend used by Clafer for instance generation
- [PlantUML](https://plantuml.com/) and [Graphviz](https://graphviz.org/): traceability diagram generation and rendering
- [Kotlin](https://kotlinlang.org/), [Maven](https://maven.apache.org/), and [JUnit 5](https://junit.org/junit5/): executable source/test harness under `source/kotlin`

Each app can define:
- Requirements in Lando syntax
- Architecture in Clafer
- Generated assets (instances, traceability diagrams/reports)
- Source assets and tests in `source/`

## Layout

- `apps/<app-name>`: one folder per app following the same workflow
- `apps/token`: reference app showing end-to-end workflow
- `.github/skills/clafer-model-to-code`: workflow skill for requirements/model-to-assets generation
- `scripts`: shared generation and validation tooling
- `Makefile`: single entry point for all app workflows

## Standard Commands

List apps:

```bash
make apps
```

Regenerate artifacts for one app:

```bash
make generate APP=token
```

Regenerate artifacts and run tests for one app:

```bash
make verify APP=token
```

Run tests only:

```bash
make test APP=token
```

Clean generated outputs:

```bash
make clean APP=token
```

## Workflow Split

Use `make` for model and verification automation:
- `make generate APP=<app-name>`: regenerate requirements-derived and model-derived artifacts
- `make verify APP=<app-name>`: run generation plus tests
- `make clean APP=<app-name>`: remove generated outputs

Use the skill file for implementation materials generation:
- `.github/skills/clafer-model-to-code/SKILL.md` defines how to generate and refresh specs, Kotlin code skeletons, and scenario-traceable tests from requirements and Clafer architecture.

App authorship pattern:
- write or update `apps/<app-name>/requirements/*.lando`
- write or update `apps/<app-name>/model/prelude.cfr` and `apps/<app-name>/model/architecture.cfr`
- run `make generate APP=<app-name>` to refresh generated artifacts from requirements + model
- use `.github/skills/clafer-model-to-code/SKILL.md` to develop/update `apps/<app-name>/source/**`
- run `make verify APP=<app-name>` to validate generation outputs and tests together

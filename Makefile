APP ?= token
APP_DIR := apps/$(APP)
MODEL_NAME ?= $(APP)

OUT_DIR := $(APP_DIR)/out
OUT_FILE := $(OUT_DIR)/$(MODEL_NAME).cfr
MODEL_DIR := $(APP_DIR)/model
GENERATED_DIR := $(APP_DIR)/generated
INSTANCES_DIR := $(APP_DIR)/instances
INSTANCES_JSON_DIR := $(APP_DIR)/instances-json
TRACEABILITY_DIR := $(APP_DIR)/traceability
REPORT_DIR := $(APP_DIR)/reports

LANDO_REQS ?= $(firstword $(wildcard $(APP_DIR)/requirements/*.lando))
GENERATED_REQS := $(GENERATED_DIR)/requirements.generated.cfr
PRELUDE := $(MODEL_DIR)/prelude.cfr
ARCHITECTURE := $(MODEL_DIR)/architecture.cfr

PYTHON ?= python3
VENV_DIR ?= $(APP_DIR)/.venv
VENV_PYTHON := $(VENV_DIR)/bin/python3
PYTHON_CMD = $(if $(wildcard $(VENV_PYTHON)),$(VENV_PYTHON),$(PYTHON))
PYTHON_REQUIREMENTS := $(APP_DIR)/requirements.txt
REPO_SCRIPTS_DIR := scripts

LANDO_TO_CFR := $(REPO_SCRIPTS_DIR)/lando_requirements_to_cfr.py
INSTANCES_TO_JSON := $(REPO_SCRIPTS_DIR)/choco_to_json.py
TRACEABILITY_PLANTUML_GEN := $(REPO_SCRIPTS_DIR)/instance_traceability_plantuml.py
TRACEABILITY_REPORT_GEN := $(REPO_SCRIPTS_DIR)/instance_traceability_report.py
TRACEABILITY_COVERAGE_CHECK := $(REPO_SCRIPTS_DIR)/check_traceability_coverage.py

KOTLIN_DIR := $(APP_DIR)/source/kotlin
JAVA11_HOME ?= $(shell /usr/libexec/java_home -v 11 2>/dev/null)
JAVA_HOME ?= $(JAVA11_HOME)

DOCKER ?= docker
PLE_IMAGE ?= freeandfair/de-ple-e2eviv:latest
IMAGE_PLATFORM ?=
DOCKER_PLATFORM_ARG := $(if $(strip $(IMAGE_PLATFORM)),--platform=$(strip $(IMAGE_PLATFORM)),)
USE_DOCKER ?= no
FORCE_DOCKER := $(if $(filter yes YES true TRUE 1,$(USE_DOCKER)),yes,)
CLAFER_DOCKER_BIN := /opt/clafer/bin/clafer
CHOCOSOLVER_DOCKER_BIN := /opt/clafer/clafer-tools-0.5.1/chocosolver
HOST_PLANTUML := $(shell command -v plantuml 2>/dev/null)
HOST_DOT := $(shell command -v dot 2>/dev/null)

DOCKER_RUN_TOOL = $(DOCKER) run --rm $(DOCKER_PLATFORM_ARG) -v "$(CURDIR)":/workspace -w /workspace --entrypoint $(1) $(PLE_IMAGE)
CLAFER_DOCKER_CMD = $(call DOCKER_RUN_TOOL,$(CLAFER_DOCKER_BIN))
CHOCOSOLVER_DOCKER_CMD = $(call DOCKER_RUN_TOOL,$(CHOCOSOLVER_DOCKER_BIN))
CLAFER_CMD = $(if $(FORCE_DOCKER),$(CLAFER_DOCKER_CMD),$(if $(shell command -v clafer 2>/dev/null),clafer,$(CLAFER_DOCKER_CMD)))
CHOCOSOLVER_CMD = $(if $(FORCE_DOCKER),$(CHOCOSOLVER_DOCKER_CMD),$(if $(shell command -v chocosolver 2>/dev/null),chocosolver,$(CHOCOSOLVER_DOCKER_CMD)))

CHOCO_SCOPE ?= 8
CHOCO_MININT ?= 0
CHOCO_MAXINT ?= 1000
CHOCO_INSTANCES ?= 10
CHOCO_OPTS ?= --scope $(CHOCO_SCOPE) --minint $(CHOCO_MININT) --maxint $(CHOCO_MAXINT) -n $(CHOCO_INSTANCES)

DEFAULT_INSTANCE_JSON := $(INSTANCES_JSON_DIR)/instances.1.json
TRACEABILITY_PLANTUML := $(TRACEABILITY_DIR)/$(MODEL_NAME)-traceability.plantuml
TRACEABILITY_PNG := $(TRACEABILITY_DIR)/$(MODEL_NAME)-traceability.png
TRACEABILITY_REPORT := $(REPORT_DIR)/$(MODEL_NAME)-traceability.md

SOURCES := $(PRELUDE) $(GENERATED_REQS) $(ARCHITECTURE)

.PHONY: help apps list verify generate check assemble generate-requirements instances instances-json traceability-artifacts traceability-plantuml traceability-report traceability-coverage test python-venv python-check clean-generated clean require-app require-lando

help:
	@echo "rde-framework tooling repo"
	@echo "selected app: $(APP)"
	@echo "targets:"
	@echo "  make apps                     - list app folders"
	@echo "  make list APP=<name>          - show app folder structure"
	@echo "  make generate APP=<name>      - regenerate app artifacts"
	@echo "  make verify APP=<name>        - regenerate artifacts + run tests"
	@echo "  make test APP=<name>          - run app tests only"
	@echo "  make clean APP=<name>         - clean app outputs and venv"

apps:
	@find apps -mindepth 1 -maxdepth 1 -type d -exec basename {} \; | sort

list: require-app
	@echo "app contents: $(APP_DIR)"
	@find $(APP_DIR) -maxdepth 2 -type d | sort

verify: generate test
	@echo "$(APP) verify completed successfully"

generate: clean-generated python-venv check instances instances-json traceability-artifacts traceability-coverage
	@echo "$(APP) generation completed successfully"

assemble: $(OUT_FILE)

check: require-app $(OUT_FILE)
	@$(CLAFER_CMD) $(OUT_FILE)

generate-requirements: $(GENERATED_REQS)

instances: check
	@mkdir -p $(INSTANCES_DIR)
	@$(CHOCOSOLVER_CMD) $(CHOCO_OPTS) --file=$(OUT_FILE) --output $(INSTANCES_DIR)/instances.txt

instances-json: python-check $(INSTANCES_DIR)/instances.txt
	@mkdir -p $(INSTANCES_JSON_DIR)
	@$(PYTHON_CMD) $(INSTANCES_TO_JSON) --file $(INSTANCES_DIR)/instances.txt --output-dir $(INSTANCES_JSON_DIR)

traceability-artifacts: traceability-plantuml traceability-report

traceability-plantuml: python-check $(DEFAULT_INSTANCE_JSON)
	@mkdir -p $(TRACEABILITY_DIR)
	@$(PYTHON_CMD) $(TRACEABILITY_PLANTUML_GEN) --input $(DEFAULT_INSTANCE_JSON) --output $(TRACEABILITY_PLANTUML)
	@if [ -n "$(HOST_PLANTUML)" ] && [ -n "$(HOST_DOT)" ]; then \
		GRAPHVIZ_DOT="$(HOST_DOT)" "$(HOST_PLANTUML)" $(TRACEABILITY_PLANTUML); \
	else \
		rm -f $(TRACEABILITY_PNG); \
		echo "Traceability PlantUML source generated; PNG render skipped because host PlantUML and Graphviz dot are not both available."; \
	fi

traceability-report: python-check $(DEFAULT_INSTANCE_JSON)
	@mkdir -p $(REPORT_DIR)
	@$(PYTHON_CMD) $(TRACEABILITY_REPORT_GEN) --input $(DEFAULT_INSTANCE_JSON) --output $(TRACEABILITY_REPORT)

traceability-coverage: python-check $(GENERATED_REQS) $(ARCHITECTURE)
	@$(PYTHON_CMD) $(TRACEABILITY_COVERAGE_CHECK) --requirements $(GENERATED_REQS) --architecture $(ARCHITECTURE)

test: require-app
	@if [ -n "$(JAVA_HOME)" ]; then \
		cd $(KOTLIN_DIR) && JAVA_HOME="$(JAVA_HOME)" mvn test; \
	else \
		cd $(KOTLIN_DIR) && mvn test; \
	fi

python-venv: require-app
	@$(PYTHON) -m venv $(VENV_DIR)
	@$(VENV_PYTHON) -m pip install --upgrade pip
	@$(VENV_PYTHON) -m pip install -r $(PYTHON_REQUIREMENTS)

python-check:
	@$(PYTHON_CMD) -c "import lark" >/dev/null 2>&1 || (echo "missing Python dependency: lark" && echo "run: make python-venv APP=$(APP)" && exit 1)

$(GENERATED_REQS): require-app require-lando $(LANDO_TO_CFR)
	@mkdir -p $(GENERATED_DIR)
	@$(PYTHON_CMD) $(LANDO_TO_CFR) --input $(LANDO_REQS) --output $(GENERATED_REQS)

$(OUT_FILE): require-app $(SOURCES)
	@mkdir -p $(OUT_DIR)
	@cat $(SOURCES) > $(OUT_FILE)
	@echo "Assembled $(OUT_FILE)"

require-app:
	@test -d "$(APP_DIR)" || (echo "error: app folder not found: $(APP_DIR)" >&2; exit 1)

require-lando:
	@test -n "$(LANDO_REQS)" || (echo "error: no requirements .lando file found under $(APP_DIR)/requirements/" >&2; exit 1)

clean-generated: require-app
	@rm -rf $(GENERATED_DIR)
	@rm -rf $(OUT_DIR)
	@rm -rf $(INSTANCES_DIR)
	@rm -rf $(INSTANCES_JSON_DIR)
	@rm -rf $(TRACEABILITY_DIR)
	@rm -rf $(REPORT_DIR)

clean: clean-generated
	@rm -rf $(VENV_DIR)
	@rm -rf $(KOTLIN_DIR)/target

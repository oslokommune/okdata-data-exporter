.DEV_PROFILE := okdata-dev
.PROD_PROFILE := okdata-prod

GLOBAL_PY := python3
BUILD_VENV ?= .build_venv
BUILD_PY := $(BUILD_VENV)/bin/python

.PHONY: init
init: $(BUILD_VENV)

$(BUILD_VENV):
	$(GLOBAL_PY) -m venv $(BUILD_VENV)
	$(BUILD_PY) -m pip install -U pip

.PHONY: format
format: $(BUILD_VENV)/bin/black
	$(BUILD_PY) -m black .

.PHONY: test
test: $(BUILD_VENV)/bin/tox
	$(BUILD_PY) -m tox -p auto -o

.PHONY: upgrade-deps
upgrade-deps: $(BUILD_VENV)/bin/pip-compile
	$(BUILD_VENV)/bin/pip-compile -U

.PHONY: deploy
deploy: login-dev init format test
	@echo "\nDeploying to stage: dev\n"
	sam build
	sam validate --lint
	sam deploy --config-env dev \
		--no-confirm-changeset \
		--no-fail-on-empty-changeset \
		--parameter-overrides "Stage=dev GitRev=$$(git rev-parse --abbrev-ref HEAD):$$(git rev-parse HEAD)" \
		--tags "GIT_REV=$$(git rev-parse --abbrev-ref HEAD):$$(git rev-parse HEAD)" \
		--profile $(.DEV_PROFILE)

.PHONY: deploy-prod
deploy-prod: login-prod init format is-git-clean test
	@echo "\nDeploying to stage: prod\n"
	sam build
	sam validate --lint
	sam deploy --config-env prod \
		--no-confirm-changeset \
		--no-fail-on-empty-changeset \
		--parameter-overrides "Stage=prod GitRev=$$(git rev-parse --abbrev-ref HEAD):$$(git rev-parse HEAD)" \
		--tags "GIT_REV=$$(git rev-parse --abbrev-ref HEAD):$$(git rev-parse HEAD)" \
		--profile $(.PROD_PROFILE)

.PHONY: undeploy
undeploy: login-dev init
	@echo "\nUndeploying stage: dev\n"
	sam delete --config-env dev --profile $(.DEV_PROFILE)

.PHONY: undeploy-prod
undeploy-prod: login-prod init
	@echo "\nUndeploying stage: prod\n"
	sam delete --config-env prod --profile $(.PROD_PROFILE)

.PHONY: login-dev
login-dev: init
	aws sts get-caller-identity --profile $(.DEV_PROFILE) || aws sso login --profile=$(.DEV_PROFILE)

.PHONY: login-prod
login-prod: init
	aws sts get-caller-identity --profile $(.PROD_PROFILE) || aws sso login --profile=$(.PROD_PROFILE)

.PHONY: is-git-clean
is-git-clean:
	@status=$$(git fetch origin && git status -s -b) ;\
	if test "$${status}" != "## main...origin/main"; then \
		echo; \
		echo Git working directory is dirty, aborting >&2; \
		false; \
	fi


###
# Python build dependencies
##

$(BUILD_VENV)/bin/pip-compile: $(BUILD_VENV)
	$(BUILD_PY) -m pip install -U pip-tools

$(BUILD_VENV)/bin/%: $(BUILD_VENV)
	$(BUILD_PY) -m pip install -U $*

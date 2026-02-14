# NBNE Platform — Development & Release Helpers
# See docs/versioning.md for full release process.

BACKEND_DIR = backend
MANAGE = python $(BACKEND_DIR)/manage.py

# ---------------------------------------------------------------------------
# Development
# ---------------------------------------------------------------------------

.PHONY: test
test: ## Run Django test suite
	cd $(BACKEND_DIR) && python manage.py test --parallel

.PHONY: lint
lint: ## Run flake8 linter
	cd $(BACKEND_DIR) && python -m flake8 --max-line-length=120 --exclude=migrations .

.PHONY: check
check: ## Django system checks (deployment mode)
	cd $(BACKEND_DIR) && python manage.py check --deploy

.PHONY: migrations-check
migrations-check: ## Verify no missing migrations
	cd $(BACKEND_DIR) && python manage.py makemigrations --check --dry-run

.PHONY: validate
validate: migrations-check test check ## Full pre-release validation

# ---------------------------------------------------------------------------
# Release
# ---------------------------------------------------------------------------

.PHONY: tag
tag: ## Create an annotated tag. Usage: make tag VERSION=v0.9.1 MSG="description"
ifndef VERSION
	$(error VERSION is required. Usage: make tag VERSION=v0.9.1 MSG="description")
endif
ifndef MSG
	$(error MSG is required. Usage: make tag VERSION=v0.9.1 MSG="description")
endif
	@echo "Tagging $(VERSION) on current branch..."
	git tag -a $(VERSION) -m "$(VERSION): $(MSG)"
	git push origin $(VERSION)
	@echo "✅ Tag $(VERSION) pushed to origin."

.PHONY: release-merge
release-merge: ## Merge main into release branch
	git checkout release
	git pull origin release
	git merge main
	git push origin release
	git checkout main
	@echo "✅ main merged into release and pushed."

# ---------------------------------------------------------------------------
# Info
# ---------------------------------------------------------------------------

.PHONY: tags
tags: ## List all tags
	git tag -l --sort=-v:refname

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help

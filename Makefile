HUGO ?= hugo

# LightTag redirect operations. Override these when testing a different stack
# or distribution; production region/profile defaults are explicit. Change-set
# name and type intentionally have no defaults and must be supplied by an owner.
LIGHTTAG_REDIRECT_DIR ?= infra/lighttag-redirects
LIGHTTAG_REDIRECT_TEMPLATE ?= $(LIGHTTAG_REDIRECT_DIR)/template.yaml
LIGHTTAG_REDIRECT_VALIDATOR ?= $(LIGHTTAG_REDIRECT_DIR)/validate.py
LIGHTTAG_REDIRECT_REGION ?= us-east-1
LIGHTTAG_REDIRECT_PROFILE ?= local agent
LIGHTTAG_REDIRECT_STACK ?= lighttag-redirects
LIGHTTAG_REDIRECT_CHANGE_SET ?=
LIGHTTAG_REDIRECT_CHANGE_SET_TYPE ?=
LIGHTTAG_REDIRECT_LIVE_ARGS ?= --live
LIGHTTAG_REDIRECT_PARAMETERS ?=
INDEXNOW_SCRIPT ?= scripts/submit_indexnow.py
INDEXNOW_SITEMAP_URL ?= https://talperry.com/sitemap.xml
INDEXNOW_KEY_FILE ?= static/indexnow-key.txt
INDEXNOW_KEY_LOCATION ?= https://talperry.com/indexnow-key.txt
INDEXNOW_CONFIRM ?=

.PHONY: build serve clean validate-social validate-share validate-seo validate-art indexnow-test validate \
	art-review art-review-serve \
	lighttag-redirect-test lighttag-redirect-validate \
	lighttag-redirect-local-test lighttag-redirect-local-validate \
	lighttag-redirect-cfn-check lighttag-redirect-cfn-validate \
	lighttag-redirect-cfn-lint \
	lighttag-redirect-change-set lighttag-redirect-cfn-change-set \
	lighttag-redirect-deploy lighttag-redirect-live-test submit-indexnow

build:
	$(HUGO)

serve:
	$(HUGO) server -D --disableFastRender --gc

clean:
	rm -rf public resources

validate-social: build
	uv run scripts/validate_social_meta.py

validate-share:
	uv run scripts/validate_share_pack.py

validate-seo: build
	uv run scripts/validate_technical_seo.py

validate-art:
	uv run --project tools/editorial-images editorial-images --validate

art-review:
	uv run --project tools/editorial-images editorial-images --review

art-review-serve: art-review
	uv run --project tools/editorial-images python -m http.server 4174 --directory artifacts/editorial-image-review

indexnow-test:
	uv run scripts/test_submit_indexnow.py

validate: validate-social validate-share validate-seo validate-art indexnow-test

# The validator is kept as an overridable path so local development can use a
# checked-out validator while CI or a future layout can select another one.
lighttag-redirect-test:
	@if test -f "$(LIGHTTAG_REDIRECT_VALIDATOR)"; then \
		uv run "$(LIGHTTAG_REDIRECT_VALIDATOR)"; \
	elif test -f "scripts/validate_lighttag_redirects.py"; then \
		uv run scripts/validate_lighttag_redirects.py; \
	else \
		echo "Missing redirect validator; set LIGHTTAG_REDIRECT_VALIDATOR=..." >&2; exit 2; \
	fi

lighttag-redirect-validate: lighttag-redirect-test

lighttag-redirect-local-test: lighttag-redirect-test

lighttag-redirect-local-validate: lighttag-redirect-validate

lighttag-redirect-cfn-check:
	@test -f "$(LIGHTTAG_REDIRECT_TEMPLATE)" || (echo "Missing $(LIGHTTAG_REDIRECT_TEMPLATE)" >&2; exit 2)
	uvx cfn-lint "$(LIGHTTAG_REDIRECT_TEMPLATE)"

lighttag-redirect-cfn-lint: lighttag-redirect-cfn-check

lighttag-redirect-cfn-validate:
	@test -f "$(LIGHTTAG_REDIRECT_TEMPLATE)" || (echo "Missing $(LIGHTTAG_REDIRECT_TEMPLATE)" >&2; exit 2)
	AWS_DEFAULT_REGION="$(LIGHTTAG_REDIRECT_REGION)" aws cloudformation validate-template \
		--template-body "file://$(LIGHTTAG_REDIRECT_TEMPLATE)" \
		--region "$(LIGHTTAG_REDIRECT_REGION)" --profile "$(LIGHTTAG_REDIRECT_PROFILE)"

lighttag-redirect-change-set: lighttag-redirect-test lighttag-redirect-cfn-check lighttag-redirect-cfn-validate
	@test -f "$(LIGHTTAG_REDIRECT_TEMPLATE)" || (echo "Missing $(LIGHTTAG_REDIRECT_TEMPLATE)" >&2; exit 2)
	@test -n "$(LIGHTTAG_REDIRECT_CHANGE_SET)" || (echo "Set LIGHTTAG_REDIRECT_CHANGE_SET to a unique non-empty name" >&2; exit 2)
	@test "$(LIGHTTAG_REDIRECT_CHANGE_SET_TYPE)" = CREATE || test "$(LIGHTTAG_REDIRECT_CHANGE_SET_TYPE)" = UPDATE || (echo "Set LIGHTTAG_REDIRECT_CHANGE_SET_TYPE=CREATE or UPDATE" >&2; exit 2)
	AWS_DEFAULT_REGION="$(LIGHTTAG_REDIRECT_REGION)" aws cloudformation create-change-set \
		--stack-name "$(LIGHTTAG_REDIRECT_STACK)" \
		--change-set-name "$(LIGHTTAG_REDIRECT_CHANGE_SET)" \
		--change-set-type "$(LIGHTTAG_REDIRECT_CHANGE_SET_TYPE)" \
		--template-body "file://$(LIGHTTAG_REDIRECT_TEMPLATE)" \
		$(LIGHTTAG_REDIRECT_PARAMETERS) \
		--region "$(LIGHTTAG_REDIRECT_REGION)" --profile "$(LIGHTTAG_REDIRECT_PROFILE)"

lighttag-redirect-cfn-change-set: lighttag-redirect-change-set

lighttag-redirect-deploy:
	@test -n "$(LIGHTTAG_REDIRECT_CHANGE_SET)" || (echo "Set LIGHTTAG_REDIRECT_CHANGE_SET to the reviewed change-set name" >&2; exit 2)
	@set -eu; \
	stack_status=$$(AWS_DEFAULT_REGION="$(LIGHTTAG_REDIRECT_REGION)" aws cloudformation describe-stacks \
		--stack-name "$(LIGHTTAG_REDIRECT_STACK)" --query 'Stacks[0].StackStatus' --output text \
		--region "$(LIGHTTAG_REDIRECT_REGION)" --profile "$(LIGHTTAG_REDIRECT_PROFILE)" 2>/dev/null) || { \
		echo "Could not read stack status; an executable change set requires an existing REVIEW_IN_PROGRESS or stable stack" >&2; exit 2; \
	}; \
	case "$$stack_status" in \
		REVIEW_IN_PROGRESS) change_set_type=CREATE ;; \
		CREATE_COMPLETE|UPDATE_COMPLETE|UPDATE_ROLLBACK_COMPLETE|IMPORT_COMPLETE|IMPORT_ROLLBACK_COMPLETE) change_set_type=UPDATE ;; \
		*) echo "Stack status $$stack_status is not safe for change-set execution" >&2; exit 2 ;; \
	esac; \
	if test -n "$(LIGHTTAG_REDIRECT_CHANGE_SET_TYPE)" && test "$(LIGHTTAG_REDIRECT_CHANGE_SET_TYPE)" != "$$change_set_type"; then \
		echo "Supplied change-set type disagrees with stack status ($(LIGHTTAG_REDIRECT_CHANGE_SET_TYPE) vs $$change_set_type from $$stack_status)" >&2; exit 2; \
	fi; \
	AWS_DEFAULT_REGION="$(LIGHTTAG_REDIRECT_REGION)" aws cloudformation execute-change-set \
		--stack-name "$(LIGHTTAG_REDIRECT_STACK)" \
		--change-set-name "$(LIGHTTAG_REDIRECT_CHANGE_SET)" \
		--region "$(LIGHTTAG_REDIRECT_REGION)" --profile "$(LIGHTTAG_REDIRECT_PROFILE)"; \
	case "$$change_set_type" in \
		CREATE) waiter=stack-create-complete ;; \
		UPDATE) waiter=stack-update-complete ;; \
	esac; \
	AWS_DEFAULT_REGION="$(LIGHTTAG_REDIRECT_REGION)" aws cloudformation wait "$$waiter" \
		--stack-name "$(LIGHTTAG_REDIRECT_STACK)" \
		--region "$(LIGHTTAG_REDIRECT_REGION)" --profile "$(LIGHTTAG_REDIRECT_PROFILE)"; \
	AWS_DEFAULT_REGION="$(LIGHTTAG_REDIRECT_REGION)" aws cloudformation update-termination-protection \
		--enable-termination-protection --stack-name "$(LIGHTTAG_REDIRECT_STACK)" \
		--region "$(LIGHTTAG_REDIRECT_REGION)" --profile "$(LIGHTTAG_REDIRECT_PROFILE)"; \
	distribution_id=$$(AWS_DEFAULT_REGION="$(LIGHTTAG_REDIRECT_REGION)" aws cloudformation describe-stack-resource \
		--stack-name "$(LIGHTTAG_REDIRECT_STACK)" --logical-resource-id LightTagDistribution \
		--query 'StackResourceDetail.PhysicalResourceId' --output text \
		--region "$(LIGHTTAG_REDIRECT_REGION)" --profile "$(LIGHTTAG_REDIRECT_PROFILE)"); \
	AWS_DEFAULT_REGION="$(LIGHTTAG_REDIRECT_REGION)" aws cloudfront wait distribution-deployed \
		--id "$$distribution_id" --region "$(LIGHTTAG_REDIRECT_REGION)" \
		--profile "$(LIGHTTAG_REDIRECT_PROFILE)"; \
	AWS_DEFAULT_REGION="$(LIGHTTAG_REDIRECT_REGION)" aws cloudformation describe-stacks \
		--stack-name "$(LIGHTTAG_REDIRECT_STACK)" --query 'Stacks[0].Outputs' --output table \
		--region "$(LIGHTTAG_REDIRECT_REGION)" --profile "$(LIGHTTAG_REDIRECT_PROFILE)"

lighttag-redirect-live-test:
	@if test -f "$(LIGHTTAG_REDIRECT_VALIDATOR)"; then \
		uv run "$(LIGHTTAG_REDIRECT_VALIDATOR)" $(LIGHTTAG_REDIRECT_LIVE_ARGS); \
	elif test -f "scripts/validate_lighttag_redirects.py"; then \
		uv run scripts/validate_lighttag_redirects.py $(LIGHTTAG_REDIRECT_LIVE_ARGS); \
	else \
		echo "Missing redirect validator; set LIGHTTAG_REDIRECT_VALIDATOR=..." >&2; exit 2; \
	fi

# Deliberately excluded from validate and CI: this target contacts IndexNow.
# The exact confirmation phrase prevents an accidental third-party submission.
submit-indexnow:
	@test "$(INDEXNOW_CONFIRM)" = "SUBMIT INDEXNOW" || (echo "Set INDEXNOW_CONFIRM='SUBMIT INDEXNOW' to authorize the external submission" >&2; exit 2)
	uv run "$(INDEXNOW_SCRIPT)" --submit --confirm "$(INDEXNOW_CONFIRM)" \
		--sitemap-url "$(INDEXNOW_SITEMAP_URL)" \
		--key-file "$(INDEXNOW_KEY_FILE)" \
		--key-location "$(INDEXNOW_KEY_LOCATION)"

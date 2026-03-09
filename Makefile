HUGO ?= hugo

.PHONY: build serve clean validate-social validate-share validate

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

validate: validate-social validate-share

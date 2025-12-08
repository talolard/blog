HUGO ?= hugo

.PHONY: build serve clean

build:
	$(HUGO)

serve:
	$(HUGO) server -D --disableFastRender --gc

clean:
	rm -rf public resources

PYTHON ?= python3

.PHONY: bootstrap test run
bootstrap:
	$(PYTHON) scripts/factory.py bootstrap

test:
	$(PYTHON) -m unittest discover -s tests -v
	node --experimental-strip-types tests/pi_observer.test.mjs

run:
	$(PYTHON) scripts/factory.py run

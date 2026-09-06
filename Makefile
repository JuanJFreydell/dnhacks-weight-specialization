PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)
SIM ?= icarus
WAVES ?= 0
WAVE_FLAG = $(if $(filter 1 yes true,$(WAVES)),--waves,)

.PHONY: generate generate-expert test-generic test-fixed test test-f2-generic test-f2-fixed test-f2 test-expert-generic test-expert-fixed test-expert waves clean

generate:
	$(PYTHON) scripts/generate_artifacts.py
	$(PYTHON) scripts/generate_fixed_rtl.py

generate-expert:
	$(PYTHON) inference_core/scripts/generate_artifacts.py
	$(PYTHON) inference_core/scripts/generate_fixed_rtl.py

test-generic: generate
	$(PYTHON) tests/run.py generic --sim "$(SIM)" $(WAVE_FLAG)

test-fixed: generate
	$(PYTHON) tests/run.py fixed --sim "$(SIM)" $(WAVE_FLAG)

test: test-generic test-fixed

test-f2-generic: generate
	$(PYTHON) tests/run_f2.py generic --sim "$(SIM)"

test-f2-fixed: generate
	$(PYTHON) tests/run_f2.py fixed --sim "$(SIM)"

test-f2: test-f2-generic test-f2-fixed

test-expert-generic: generate-expert
	$(PYTHON) inference_core/tests/run.py generic --sim "$(SIM)" $(WAVE_FLAG)

test-expert-fixed: generate-expert
	$(PYTHON) inference_core/tests/run.py fixed --sim "$(SIM)" $(WAVE_FLAG)

test-expert: test-expert-generic test-expert-fixed

waves:
	$(MAKE) WAVES=1 test

clean:
	rm -rf sim_build results-generic.xml results-fixed.xml

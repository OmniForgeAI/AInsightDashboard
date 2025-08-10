VENV=.venv
ifeq ($(OS),Windows_NT)
BIN=$(VENV)/Scripts
PY=$(BIN)/python.exe
PIP=$(BIN)/pip.exe
STREAMLIT=$(BIN)/streamlit.exe
PYTEST=$(BIN)/pytest.exe
else
BIN=$(VENV)/bin
PY=$(BIN)/python
PIP=$(BIN)/pip
STREAMLIT=$(BIN)/streamlit
PYTEST=$(BIN)/pytest
endif

.PHONY: setup data test run clean

setup:
	python -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "✔ Env ready. Next: 'make data' then 'make run'"

data:
	$(PY) -m app.data_loader --generate-sample

test:
	$(PYTEST) -q

run:
	$(STREAMLIT) run app/main.py

clean:
	@if [ -d "$(VENV)" ]; then rm -rf $(VENV); fi
	@if [ -d "data/processed" ]; then rm -rf data/processed/*.parquet; fi
	@if [ -d "data/samples" ]; then rm -rf data/samples/*.parquet; fi
	@if [ -d ".pytest_cache" ]; then rm -rf .pytest_cache; fi
	@if [ -f ".coverage" ]; then rm -f .coverage; fi

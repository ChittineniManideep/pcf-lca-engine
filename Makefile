.PHONY: install validate test run sql scenarios all

install:
	pip install -e ".[dev]"

validate:
	python -m pcf validate

test:
	pytest -q

run:
	python -m pcf run

sql:
	python scripts/run_sql_local.py

scenarios:
	for s in recycled_aluminium pcr_plastics renewable_assembly no_air_freight combined; do \
		python -m pcf run --scenario $$s --mc-runs 2000; done

all: validate test run sql

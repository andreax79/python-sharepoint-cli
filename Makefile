SHELL=/bin/bash -e

help:
	@echo - make build
	@echo - make clean
	@echo - make coverage
	@echo - make lint
	@echo - make test
	@echo - make typecheck
	@echo - make release

coverage:
	python3 -m coverage run --source=sharepointcli test.py && python3 -m coverage report -m

test:
	python3 setup.py test

typecheck:
	mypy --strict --no-warn-unused-ignores sharepointcli

lint:
	python3 setup.py flake8

build: clean doc
	python3 setup.py bdist_wheel
	python3 setup.py sdist bdist_wheel

release: build
	twine upload -r pypi dist/*

doc:
	-cat docs/header.md > README.md
	-cat docs/installation.md > README.md
	-cat docs/configuration.md >> README.md
	-cat docs/usage.md >> README.md
	-./spo.py --raw help authenticate >> README.md
	-./spo.py --raw help configure >> README.md
	-./spo.py --raw help cp >> README.md
	-./spo.py --raw help help >> README.md
	-./spo.py --raw help ls >> README.md
	-./spo.py --raw help mkdir >> README.md
	-./spo.py --raw help rm >> README.md
	-./spo.py --raw help rmdir >> README.md
	-./spo.py --raw help version >> README.md
	-cat docs/tests.md >> README.md
	-cat docs/license.md >> README.md
	-cat docs/links.md >> README.md

clean:
	-rm -rf build dist
	-rm -rf *.egg-info

venv:
	-rm -rf bin lib share
	python3 -m virtualenv .
	. bin/activate; pip install -Ur requirements.txt
	. bin/activate; pip install -Ur requirements-dev.txt

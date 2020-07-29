SHELL=/bin/bash -e

help:
	@echo - make coverage
	@echo - make test
	@echo - make typecheck
	@echo - make lint
	@echo - make release
	@echo - make clean

coverage:
	python3 -m coverage run --source=sharepointcli test.py && python3 -m coverage report -m

test:
	python3 setup.py test

typecheck:
	mypy --strict --no-warn-unused-ignores sharepointcli

lint:
	python3 setup.py flake8

release:
	make doc
	python3 ./setup.py bdist_wheel

doc:
	-cat docs/header.md > README.md
	-cat docs/installation.md > README.md
	-cat docs/configuration.md >> README.md
	-cat docs/usage.md >> README.md
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


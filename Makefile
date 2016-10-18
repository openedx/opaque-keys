.DEFAULT_GOAL := test

.PHONY: html_coverage quality requirements types

html_coverage:
	coverage html && open htmlcov/index.html

quality:
	pep8 --config=.pep8 opaque_keys
	pylint --rcfile=pylintrc opaque_keys

requirements:
	pip install -r requirements.txt

test:
	tox

types:
	tox -e types-2 -e types-3

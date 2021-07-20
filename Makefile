.PHONY: clean-pyc clean-tests clean docs

all: clean-pyc clean-tests clean test-functional docs

clean-all: clean-pyc clean-tests clean

test-all: test-functional test-scenario

test-functional:
	tox -e py3-unit

test-scenario:
	tox -e py3-scenario

clean:
	rm -rf *.egg
	rm -rf *.egg-info
	rm -rf docs/_build
	rm -rf docs/.examples
	rm -rf .cache
	rm -rf .tox
	rm -rf build
	rm -rf dist

clean-tests:
	rm -rf tests/.coverage*
	rm -rf tests/.cache
	rm -rf tests/coverage
	rm -rf tests/localhost_scenario/.teflo
	rm -rf tests/localhost_scenario/.ansible
	rm -rf tests/functional/coverage
	rm -rf tests/functional/.ansible
	rm -rf tests/functional/.coverage*

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

docs:
	tox -e docs

docs-wiki:
	./shell_tox.sh

bump-major: bumpversion major --commit

bump-minor:
	bumpversion minor --commit

bump-patch:
	bumpversion patch --commit

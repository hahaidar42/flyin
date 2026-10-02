install
run
debug
clean
lint
lint-strict


PYTHON = python3
PIP = pip3
MAIN = a_maze_ing.py
CONFIG = config.txt

.PHONY: install run debug clean lint lint-strict


build:
	$(PYTHON) -m build

install:
	export PYENV_DISABLE_REHASH=1; \
	$(PIP) install --force-reinstall "the file you want to install" || true

run:
	$(PYTHON) $(MAIN) $(CONFIG)

debug:
	$(PYTHON) -m pdb $(MAIN) $(CONFIG)

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	rm -f maze.txt

lint:
	flake8 .
	python3 -m mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	flake8 .
	python3 -m mypy . --strict
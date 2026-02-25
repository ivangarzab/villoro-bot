.PHONY: help install test coverage coverage-html clean run run-fresh update-brain

# Environment variables
export ENV=dev
VENV = .venv
PYTHON = $(VENV)/bin/python3
PIP = $(VENV)/bin/pip

help:
	@echo "--- VilloroBot: Command Shortcuts ---"
	@echo "install        : Create venv and install all dependencies"
	@echo "update-brain   : Force update kluvs-brain from remote repo"
	@echo "test           : Run tests using venv"
	@echo "coverage       : Run tests with terminal coverage report"
	@echo "coverage-html  : Generate HTML coverage report"
	@echo "run            : Run the bot using the virtual environment"
	@echo "run-fresh      : Update kluvs-brain and run the bot"
	@echo "clean          : Remove venv, cache, and coverage files"

$(VENV)/bin/activate: requirements.txt
	@echo "Creating virtual environment..."
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install coverage
	@touch $(VENV)/bin/activate

install: $(VENV)/bin/activate
	@echo "Environment is ready."

test: install
	$(PYTHON) -m unittest discover -v -s ./tests -p "test_*.py"

coverage: install
	$(PYTHON) -m coverage run --source=. -m unittest discover -s ./tests -p "test_*.py"
	$(PYTHON) -m coverage report -m

coverage-html: install
	$(PYTHON) -m coverage run --source=. -m unittest discover -s ./tests -p "test_*.py"
	$(PYTHON) -m coverage html
	@echo "Report generated: open htmlcov/index.html"

run: install
	$(PYTHON) main.py

update-brain:
	@echo "Updating kluvs-brain from remote repository..."
	$(PIP) install --upgrade --force-reinstall git+https://github.com/ivangarzab/kluvs-brain.git
	@echo "kluvs-brain updated successfully!"

run-fresh: update-brain run
	@echo "Bot running with latest kluvs-brain!"

clean:
	rm -rf __pycache__ */__pycache__ tests/__pycache__
	rm -rf $(VENV)
	rm -f .coverage coverage.xml
	rm -rf htmlcov/

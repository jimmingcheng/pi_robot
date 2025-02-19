VENV_DIR := ./venv
PYTHON := python3.12
POETRY := $(VENV_DIR)/bin/poetry

venv: poetry.lock
	$(PYTHON) -m venv $(VENV_DIR)
	$(VENV_DIR)/bin/pip install poetry
	PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring $(POETRY) install

.PHONY: test
test: venv
	$(VENV_DIR)/bin/mypy pi_robot/

.PHONY: clean
clean:
	rm -fr $(VENV_DIR)

# Variables
POETRY=poetry

.PHONY: all install clean test run

# Default target
all: install

# Install dependencies
install:
	${POETRY} install

# Clean up everything
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf **/__pycache__
	rm -rf .pytest_cache
	${POETRY} env remove --all

run:
	${POETRY} run python -m src

api:
	${POETRY} run uvicorn src.api:app --reload --host 0.0.0.0 --port 8000


test:
	${POETRY} run pytest tests/

frontend-install:
	cd frontend && npm install

frontend-dev:
	cd frontend && npm run dev
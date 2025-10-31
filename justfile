default:
    @just --list

metrics fy *args:
    @poetry run python -m src.cli metrics --fy {{fy}} {{args}}

mine fy *args:
    @poetry run python -m src.cli mine --fy {{fy}} {{args}}

clean:
    @echo "Cleaning taxing..."
    @rm -rf dist build .pytest_cache .ruff_cache __pycache__ .venv htmlcov
    @find . -type d -name "__pycache__" -exec rm -rf {} +
    @find . -type d -name ".pytest_cache" -exec rm -rf {} +

install:
    @poetry lock
    @poetry install --with dev

ci:
    @poetry run ruff format . -q
    @poetry run ruff check . --fix --unsafe-fixes -q
    @poetry run pytest tests/ -q
    @poetry build -q

test:
    @poetry run pytest tests/

build:
    @poetry build

cov:
    @poetry run pytest tests/ --cov=src --cov-report=term-missing

format:
    @poetry run ruff format .

lint:
    @poetry run ruff check .

fix:
    @poetry run ruff check . --fix --unsafe-fixes

type:
    @echo "Note: Python type checking can be added with pyright or mypy"

repomix:
    repomix

commits:
    @git --no-pager log --pretty=format:"%h | %ar | %s"

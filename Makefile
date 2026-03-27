setup:
	git config core.hooksPath .githooks

format:
	uv run ruff format app/ main.py tests/

check:
	uv run ruff check app/ main.py tests/
	uv run pyright app/ main.py

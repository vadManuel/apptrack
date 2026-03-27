# Applications

A CLI tool that visualizes job application timelines in the terminal. Reads application data from `flow.yaml` and `applications.yaml` and renders a color-coded Gantt-style chart showing the progression of each application through its stages.

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)

## Setup

```sh
make setup
uv sync
```

## Run

```sh
uv run apptrack --apps applications.example.yaml
```

### CLI Options

| Flag     | Default              | Description                      |
| -------- | -------------------- | -------------------------------- |
| `--flow` | `flow.yaml`          | Path to flow config YAML         |
| `--apps` | -                    | Path to applications YAML        |

```sh
uv run apptrack --flow custom-flow.yaml --apps my-apps.yaml
```

Set `NO_COLOR=1` to disable ANSI color output:

```sh
NO_COLOR=1 uv run apptrack
```

## Development

### Lint, Format & Type Check

```sh
uv run ruff format app/ main.py tests/  # format code
uv run ruff check app/ main.py tests/   # lint
uv run ruff check --fix app/ main.py    # auto-fix lint issues
uv run pyright app/ main.py             # type check
```

### Test

```sh
uv run pytest
```

## Data

Stage definitions are stored in `flow.yaml` (committed). Application data is stored in `applications.yaml` (not committed — personal data).

### Setting up `applications.yaml`

Create an `applications.yaml` file in the project root. See [`applications.example.yaml`](applications.example.yaml) for the expected format. JSON schemas for both files are in the `schemas/` directory for IDE autocompletion.

Stage keys are defined in `flow.yaml`:

#### Flow stages (in order)

| Key | Label               |
| --- | ------------------- |
| S   | Submitted           |
| C   | Recruiter Scheduled |
| A   | Assessment          |
| L   | Interview Loop      |
| W   | Awaiting Feedback   |
| R   | Received Offer      |

#### Terminal stages

| Key | Label        |
| --- | ------------ |
| F   | Withdrawn    |
| X   | Denied       |
| U   | Filtered Out |

# Applications

A CLI tool that visualizes job application timelines in the terminal. Reads application data from `flow.yaml` and `applications.yaml` and renders a color-coded Gantt-style chart showing the progression of each application through its stages.

## Prerequisites

- Python 3.13+
- [Poetry](https://python-poetry.org/)

## Install

```sh
poetry install
```

## Run

```sh
poetry run python main.py
```

## Lint & Format

```sh
poetry run ruff format .      # format code
poetry run ruff check .       # lint
poetry run ruff check --fix . # auto-fix lint issues
```

## Data

Stage definitions are stored in `flow.yaml` (committed). Application data is stored in `applications.yaml` (not committed — personal data).

### Setting up `applications.yaml`

Create an `applications.yaml` file in the project root:

```yaml
applications:
  - company: Acme
    roles:
      - position: Senior Software Engineer
        note: Optional note # optional
        stages:
          S: 3/1/2026
          C: 3/5/2026
```

Each entry under `applications` has:

- **`company`** — the company name
- **`roles`** — a list of positions applied to at that company
  - **`position`** — the role title
  - **`note`** *(optional)* — any extra context
  - **`stages`** — a map of stage keys to dates (`M/D/YYYY`)

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

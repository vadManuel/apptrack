"""YAML file I/O for flow configuration and application data."""

import re
from datetime import datetime
from typing import NoReturn

import yaml

from app.models import DATE_FORMAT, ConfigError, FlowConfig, RawRole

HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


def _fail(file: str, message: str) -> NoReturn:
    """Raise a ConfigError with the file name and message."""
    raise ConfigError(file, message)


def _validate_stage_entry(file: str, section: str, i: int, entry: object) -> None:
    """Validate a single stage entry in a flow or terminal section."""
    pos = f'entry {i + 1} in "{section}"'
    if not isinstance(entry, dict):
        _fail(file, f"{pos} must be a mapping, got {type(entry).__name__}")
    for field in ("key", "label", "color"):
        if field not in entry:
            _fail(file, f'{pos} is missing required field "{field}"')
        if not isinstance(entry[field], str):
            _fail(file, f'{pos}: "{field}" must be a string')
    color = entry["color"]
    if not HEX_COLOR_RE.match(color):
        _fail(
            file,
            f'{pos}: color "{color}" must be hex (e.g. "#a1b2c3")',
        )


def load_flow(path: str = "flow.yaml") -> FlowConfig:
    """Load and validate flow stage definitions from a YAML file."""
    with open(path) as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        _fail(path, "file must contain a YAML mapping")

    for section in ("flow", "terminal"):
        if section not in data:
            _fail(path, f'missing required key "{section}"')
        if not isinstance(data[section], list):
            _fail(path, f'"{section}" must be a list')

    seen_keys: set[str] = set()
    config = FlowConfig()

    for i, entry in enumerate(data["flow"]):
        _validate_stage_entry(path, "flow", i, entry)
        key = entry["key"]
        if key in seen_keys:
            _fail(path, f'duplicate stage key "{key}"')
        seen_keys.add(key)
        config.stage_map[key] = entry["label"]
        config.colors[entry["label"]] = entry["color"]
        config.flow_order.append(key)

    for i, entry in enumerate(data["terminal"]):
        _validate_stage_entry(path, "terminal", i, entry)
        key = entry["key"]
        if key in seen_keys:
            _fail(path, f'duplicate stage key "{key}"')
        seen_keys.add(key)
        config.stage_map[key] = entry["label"]
        config.colors[entry["label"]] = entry["color"]
        config.terminal_states.append(key)

    return config


def _deduplicate_position(position: str, existing: list[RawRole]) -> str:
    """Append a numeric suffix if a position name already exists in the list.

    Examples: "Engineer" → "Engineer (1)" → "Engineer (2)"
    """
    increment = 0
    for role in existing:
        if role.position == position:
            increment += 1
        else:
            pattern = rf"^{re.escape(position)} \((\d+)\)$"
            m = re.match(pattern, role.position)
            if m:
                inc = int(m.group(1))
                if inc >= increment:
                    increment = inc + 1
    if increment > 0:
        position = f"{position} ({increment})"
    return position


def load_applications(
    valid_stage_keys: set[str],
    path: str = "applications.yaml",
) -> dict[str, list[RawRole]]:
    """Load and validate application data from a YAML file."""
    with open(path) as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        _fail(path, "file must contain a YAML mapping")
    if "applications" not in data:
        _fail(path, 'missing required key "applications"')
    if not isinstance(data["applications"], list):
        _fail(path, '"applications" must be a list')

    apps: dict[str, list[RawRole]] = {}

    for ci, company_entry in enumerate(data["applications"]):
        if not isinstance(company_entry, dict):
            _fail(path, f"application entry {ci + 1} must be a mapping")
        if "company" not in company_entry:
            _fail(
                path,
                f'application entry {ci + 1} is missing "company"',
            )
        company = company_entry["company"]
        if not isinstance(company, str):
            _fail(path, f'application entry {ci + 1}: "company" must be a string')

        if "roles" not in company_entry:
            _fail(path, f'"{company}": missing required field "roles"')
        if not isinstance(company_entry["roles"], list):
            _fail(path, f'"{company}": "roles" must be a list')

        apps[company] = []

        for ri, role in enumerate(company_entry["roles"]):
            if not isinstance(role, dict):
                _fail(path, f'"{company}" role {ri + 1} must be a mapping')
            if "position" not in role:
                _fail(
                    path,
                    f'"{company}" role {ri + 1} is missing "position"',
                )

            position = role["position"]
            if not isinstance(position, str):
                _fail(path, f'"{company}" role {ri + 1}: "position" must be a string')

            stages = role.get("stages", {})
            if not isinstance(stages, dict):
                _fail(path, f'"{company}" / "{position}": "stages" must be a mapping')

            ctx = f'"{company}" / "{position}"'
            for key, date_str in stages.items():
                if key not in valid_stage_keys:
                    valid = ", ".join(sorted(valid_stage_keys))
                    _fail(
                        path,
                        f'{ctx}: unknown stage key "{key}". Valid keys: {valid}',
                    )
                if not isinstance(date_str, str):
                    _fail(
                        path,
                        f'{ctx}: stage "{key}" date must be a string (M/D/YYYY)',
                    )
                try:
                    datetime.strptime(date_str, DATE_FORMAT)
                except ValueError:
                    _fail(
                        path,
                        f'{ctx}: invalid date "{date_str}"'
                        f' for stage "{key}".'
                        " Expected format: M/D/YYYY",
                    )

            note = role.get("note")
            if note is not None and not isinstance(note, str):
                _fail(path, f'"{company}" / "{position}": "note" must be a string')

            position = _deduplicate_position(position, apps[company])

            apps[company].append(
                RawRole(
                    position=position,
                    attrs=stages,
                    note=note,
                )
            )

    return apps

import pytest

from app.loader import load_applications, load_flow
from app.models import ConfigError

# --- load_flow ---


def test_load_flow_valid(tmp_path):
    flow_file = tmp_path / "flow.yaml"
    flow_file.write_text(
        """\
flow:
  - key: S
    label: Submitted
    color: "#8294a8"
terminal:
  - key: X
    label: Denied
    color: "#d46a6a"
"""
    )
    config = load_flow(str(flow_file))

    assert config.flow_order == ["S"]
    assert config.terminal_states == ["X"]
    assert config.stage_map == {"S": "Submitted", "X": "Denied"}
    assert config.colors["Submitted"] == "#8294a8"
    assert config.colors["Denied"] == "#d46a6a"


def test_load_flow_missing_file():
    with pytest.raises(FileNotFoundError):
        load_flow("nonexistent.yaml")


@pytest.mark.parametrize(
    ("yaml_content", "error_fragment"),
    [
        # missing terminal section
        (
            "flow:\n  - key: S\n    label: Sub\n    color: '#aabbcc'\n",
            'missing required key "terminal"',
        ),
        # invalid hex color
        (
            "flow:\n  - key: S\n    label: Submitted\n    color: 'red'\nterminal: []\n",
            'color "red" must be hex',
        ),
        # duplicate key
        (
            "flow:\n"
            "  - key: S\n    label: Submitted\n    color: '#aabbcc'\n"
            "  - key: S\n    label: Duplicate\n    color: '#112233'\n"
            "terminal: []\n",
            'duplicate stage key "S"',
        ),
        # missing required field
        (
            "flow:\n  - key: S\n    label: Submitted\nterminal: []\n",
            'missing required field "color"',
        ),
    ],
    ids=["missing-terminal", "invalid-color", "duplicate-key", "missing-field"],
)
def test_load_flow_invalid(tmp_path, yaml_content, error_fragment):
    flow_file = tmp_path / "flow.yaml"
    flow_file.write_text(yaml_content)
    with pytest.raises(ConfigError, match=error_fragment):
        load_flow(str(flow_file))


# --- load_applications ---


VALID_KEYS = {"S", "X"}


def test_load_applications_valid(tmp_path):
    apps_file = tmp_path / "apps.yaml"
    apps_file.write_text(
        """\
applications:
  - company: Acme
    roles:
      - position: Engineer
        stages:
          S: "1/10/2026"
          X: "1/20/2026"
        note: "Great team"
"""
    )
    result = load_applications(VALID_KEYS, str(apps_file))

    assert "Acme" in result
    assert len(result["Acme"]) == 1
    role = result["Acme"][0]
    assert role.position == "Engineer"
    assert role.attrs == {"S": "1/10/2026", "X": "1/20/2026"}
    assert role.note == "Great team"


@pytest.mark.parametrize(
    ("yaml_content", "error_fragment"),
    [
        # unknown stage key
        (
            "applications:\n  - company: Acme\n    roles:\n"
            "      - position: Engineer\n        stages:\n          Z: '1/10/2026'\n",
            'unknown stage key "Z"',
        ),
        # invalid date format
        (
            "applications:\n  - company: Acme\n    roles:\n"
            "      - position: Engineer\n        stages:\n          S: '2026-01-10'\n",
            'invalid date "2026-01-10"',
        ),
        # missing company field
        (
            "applications:\n  - roles:\n"
            "      - position: Engineer\n        stages:\n          S: '1/10/2026'\n",
            'missing "company"',
        ),
    ],
    ids=["unknown-key", "invalid-date", "missing-company"],
)
def test_load_applications_invalid(tmp_path, yaml_content, error_fragment):
    apps_file = tmp_path / "apps.yaml"
    apps_file.write_text(yaml_content)
    with pytest.raises(ConfigError, match=error_fragment):
        load_applications(VALID_KEYS, str(apps_file))


def test_load_applications_deduplicates_positions(tmp_path):
    apps_file = tmp_path / "apps.yaml"
    apps_file.write_text(
        """\
applications:
  - company: Acme
    roles:
      - position: Engineer
        stages:
          S: "1/10/2026"
      - position: Engineer
        stages:
          S: "2/10/2026"
      - position: Engineer
        stages:
          S: "3/10/2026"
"""
    )
    result = load_applications(VALID_KEYS, str(apps_file))
    positions = [r.position for r in result["Acme"]]
    assert positions == ["Engineer", "Engineer (1)", "Engineer (2)"]


def test_load_applications_empty_list(tmp_path):
    apps_file = tmp_path / "apps.yaml"
    apps_file.write_text("applications: []\n")
    result = load_applications(VALID_KEYS, str(apps_file))
    assert result == {}

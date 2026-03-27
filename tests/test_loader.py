import pytest

from app.loader import load_applications, load_flow

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


def test_load_flow_missing_section(tmp_path):
    flow_file = tmp_path / "flow.yaml"
    flow_file.write_text("flow:\n  - key: S\n    label: Sub\n    color: '#aabbcc'\n")
    with pytest.raises(SystemExit):
        load_flow(str(flow_file))


def test_load_flow_invalid_color(tmp_path):
    flow_file = tmp_path / "flow.yaml"
    flow_file.write_text(
        """\
flow:
  - key: S
    label: Submitted
    color: "red"
terminal: []
"""
    )
    with pytest.raises(SystemExit):
        load_flow(str(flow_file))


def test_load_flow_duplicate_key(tmp_path):
    flow_file = tmp_path / "flow.yaml"
    flow_file.write_text(
        """\
flow:
  - key: S
    label: Submitted
    color: "#aabbcc"
  - key: S
    label: Duplicate
    color: "#112233"
terminal: []
"""
    )
    with pytest.raises(SystemExit):
        load_flow(str(flow_file))


def test_load_flow_missing_field(tmp_path):
    flow_file = tmp_path / "flow.yaml"
    flow_file.write_text(
        """\
flow:
  - key: S
    label: Submitted
terminal: []
"""
    )
    with pytest.raises(SystemExit):
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


def test_load_applications_unknown_stage_key(tmp_path):
    apps_file = tmp_path / "apps.yaml"
    apps_file.write_text(
        """\
applications:
  - company: Acme
    roles:
      - position: Engineer
        stages:
          Z: "1/10/2026"
"""
    )
    with pytest.raises(SystemExit):
        load_applications(VALID_KEYS, str(apps_file))


def test_load_applications_invalid_date(tmp_path):
    apps_file = tmp_path / "apps.yaml"
    apps_file.write_text(
        """\
applications:
  - company: Acme
    roles:
      - position: Engineer
        stages:
          S: "2026-01-10"
"""
    )
    with pytest.raises(SystemExit):
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


def test_load_applications_missing_company(tmp_path):
    apps_file = tmp_path / "apps.yaml"
    apps_file.write_text(
        """\
applications:
  - roles:
      - position: Engineer
        stages:
          S: "1/10/2026"
"""
    )
    with pytest.raises(SystemExit):
        load_applications(VALID_KEYS, str(apps_file))

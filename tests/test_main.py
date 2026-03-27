import subprocess
import sys


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "main", *args],
        capture_output=True,
        text=True,
        cwd=None,
    )


def test_missing_flow_file(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "main", "--flow", str(tmp_path / "nope.yaml")],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "Missing file" in result.stderr


def test_missing_apps_file(tmp_path):
    flow = tmp_path / "flow.yaml"
    flow.write_text(
        "flow:\n  - key: S\n    label: Submitted\n    color: '#aabbcc'\n"
        "terminal:\n  - key: X\n    label: Denied\n    color: '#dd0000'\n"
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "main",
            "--flow",
            str(flow),
            "--apps",
            str(tmp_path / "nope.yaml"),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "Missing file" in result.stderr


def test_invalid_flow_config(tmp_path):
    flow = tmp_path / "flow.yaml"
    flow.write_text("flow:\n  - key: S\n    label: Submitted\n")  # missing terminal
    result = subprocess.run(
        [sys.executable, "-m", "main", "--flow", str(flow)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "Error in" in result.stderr


def test_malformed_yaml(tmp_path):
    flow = tmp_path / "flow.yaml"
    flow.write_text(":\n  - [\ninvalid yaml{{{\n")
    result = subprocess.run(
        [sys.executable, "-m", "main", "--flow", str(flow)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "YAML parse error" in result.stderr or "Error in" in result.stderr


def test_full_pipeline(tmp_path):
    flow = tmp_path / "flow.yaml"
    flow.write_text(
        "flow:\n"
        "  - key: S\n    label: Submitted\n    color: '#8294a8'\n"
        "terminal:\n"
        "  - key: X\n    label: Denied\n    color: '#d46a6a'\n"
    )
    apps = tmp_path / "apps.yaml"
    apps.write_text(
        "applications:\n"
        "  - company: Acme\n"
        "    roles:\n"
        "      - position: Engineer\n"
        "        stages:\n"
        "          S: '1/10/2026'\n"
        "          X: '1/20/2026'\n"
    )
    result = subprocess.run(
        [sys.executable, "-m", "main", "--flow", str(flow), "--apps", str(apps)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Acme" in result.stdout
    assert "Engineer" in result.stdout
    assert "Summary:" in result.stdout


def test_help_flag():
    result = subprocess.run(
        [sys.executable, "-m", "main", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--flow" in result.stdout
    assert "--apps" in result.stdout


def test_empty_applications(tmp_path):
    flow = tmp_path / "flow.yaml"
    flow.write_text(
        "flow:\n"
        "  - key: S\n    label: Submitted\n    color: '#8294a8'\n"
        "terminal:\n"
        "  - key: X\n    label: Denied\n    color: '#d46a6a'\n"
    )
    apps = tmp_path / "apps.yaml"
    apps.write_text("applications: []\n")
    result = subprocess.run(
        [sys.executable, "-m", "main", "--flow", str(flow), "--apps", str(apps)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "No applications to display" in result.stdout

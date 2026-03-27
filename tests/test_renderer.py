from datetime import date

from app.models import Application, Segment, StageStat
from app.renderer import render


def _make_stats() -> list[StageStat]:
    return [
        StageStat("S", "Submitted", "#8294a8", 0, 0.0, 0.0),
        StageStat("X", "Denied", "#d46a6a", 0, 0.0, 0.0),
    ]


def test_render_empty_apps(capsys):
    render([], _make_stats(), {})
    output = capsys.readouterr().out

    assert "Summary:" in output
    assert "No applications to display." in output
    # Should NOT print timeline header
    assert "Timeline" not in output


def test_render_summary_counts(capsys):
    stats = [
        StageStat("S", "Submitted", "#8294a8", 3, 60.0, 5.0),
        StageStat("X", "Denied", "#d46a6a", 2, 40.0, 10.0),
    ]
    render([], stats, {})
    output = capsys.readouterr().out

    # total comes from len(apps), not sum of stats
    assert "0 total applications" in output
    assert "60.0%" in output
    assert "40.0%" in output


def test_render_with_apps(capsys):
    apps = [
        Application(
            company="Acme",
            position="Engineer",
            submit_date=date(2026, 1, 1),
            segments=[
                Segment("Submitted", date(2026, 1, 1), date(2026, 1, 15)),
                Segment("Denied", date(2026, 1, 15), date(2026, 1, 15)),
            ],
            last_stage="Denied",
        ),
    ]
    stats = [
        StageStat("S", "Submitted", "#8294a8", 0, 0.0, 0.0),
        StageStat("X", "Denied", "#d46a6a", 1, 100.0, 0.0),
    ]
    colors = {"Submitted": "#8294a8", "Denied": "#d46a6a"}

    render(apps, stats, colors)
    output = capsys.readouterr().out

    assert "Acme (1)" in output
    assert "Engineer" in output
    assert "Denied" in output
    assert "Timeline" in output


def test_render_with_note(capsys):
    apps = [
        Application(
            company="Beta",
            position="Designer",
            submit_date=date(2026, 2, 1),
            segments=[
                Segment("Submitted", date(2026, 2, 1), date(2026, 2, 10)),
            ],
            last_stage="Submitted",
            note="Referral from friend",
        ),
    ]
    stats = [
        StageStat("S", "Submitted", "#8294a8", 1, 100.0, 9.0),
    ]
    colors = {"Submitted": "#8294a8"}

    render(apps, stats, colors)
    output = capsys.readouterr().out

    assert "Referral from friend" in output

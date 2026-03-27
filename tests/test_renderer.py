from datetime import date

import pytest

from app.models import Application, Segment, StageStat
from app.renderer import (
    RESET,
    _format_bar,
    _format_summary,
    hex_to_ansi_bg,
    render,
)

# --- hex_to_ansi_bg ---


@pytest.mark.parametrize(
    ("hex_color", "expect_dark_fg"),
    [
        ("#ffffff", True),  # white bg → dark (black) text
        ("#000000", False),  # black bg → light (white) text
        ("#8294a8", True),  # medium-light → dark text
        ("#1a1a1a", False),  # very dark → light text
    ],
)
def test_hex_to_ansi_bg_foreground_contrast(hex_color, expect_dark_fg):
    result = hex_to_ansi_bg(hex_color)
    if expect_dark_fg:
        assert "\033[30m" in result  # black foreground
    else:
        assert "\033[97m" in result  # white foreground
    assert "\033[48;2;" in result  # 24-bit background


def test_hex_to_ansi_bg_rgb_values():
    result = hex_to_ansi_bg("#ff8800")
    assert "255;136;0" in result


# --- _format_summary ---


def test_format_summary_content():
    stats = [
        StageStat("S", "Submitted", "#8294a8", 3, 60.0, 5.0),
        StageStat("X", "Denied", "#d46a6a", 2, 40.0, 10.0),
    ]
    output = _format_summary(stats, 5)
    assert "Summary:" in output
    assert "5 total applications" in output
    assert "60.0%" in output
    assert "40.0%" in output
    assert "Submitted" in output
    assert "Denied" in output


def test_format_summary_zero_total():
    stats = [StageStat("S", "Submitted", "#8294a8", 0, 0.0, 0.0)]
    output = _format_summary(stats, 0)
    assert "0 total applications" in output


# --- _format_bar ---


def test_format_bar_single_segment():
    segments = [Segment("Submitted", date(2026, 1, 1), date(2026, 1, 31))]
    colors = {"Submitted": "#8294a8"}
    bar = _format_bar(segments, colors, lambda d: (d - date(2026, 1, 1)).days, 60)
    # Bar should contain colored cells (ANSI escapes) and dot filler
    assert RESET in bar


def test_format_bar_fallback_color():
    """Unknown stage label falls back to gray."""
    segments = [Segment("Unknown", date(2026, 1, 1), date(2026, 1, 10))]
    bar = _format_bar(segments, {}, lambda d: (d - date(2026, 1, 1)).days, 30)
    assert RESET in bar


# --- render (integration) ---


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
    assert "Timeline" not in output


def test_render_summary_counts(capsys):
    stats = [
        StageStat("S", "Submitted", "#8294a8", 3, 60.0, 5.0),
        StageStat("X", "Denied", "#d46a6a", 2, 40.0, 10.0),
    ]
    render([], stats, {})
    output = capsys.readouterr().out

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

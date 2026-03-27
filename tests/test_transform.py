from datetime import date

from app.models import Application, RawRole, Segment
from app.transform import (
    build_timeline_data,
    compute_summary,
    group_by_company,
    sort_applications,
)

# --- build_timeline_data ---


def test_build_timeline_basic(config):
    raw_apps = {
        "Acme": [
            RawRole("Engineer", {"S": "1/10/2026", "R": "1/20/2026", "X": "2/1/2026"}),
        ],
    }
    apps = build_timeline_data(raw_apps, config, today=date(2026, 3, 1))

    assert len(apps) == 1
    app = apps[0]
    assert app.company == "Acme"
    assert app.position == "Engineer"
    assert app.submit_date == date(2026, 1, 10)
    assert app.last_stage == "Denied"
    # S -> R -> X (terminal)
    assert len(app.segments) == 3
    assert app.segments[0].stage_label == "Submitted"
    assert app.segments[0].start == date(2026, 1, 10)
    assert app.segments[0].end == date(2026, 1, 20)
    assert app.segments[1].stage_label == "Recruiter"
    assert app.segments[2].stage_label == "Denied"


def test_build_timeline_active_app(config):
    """App with no terminal state uses today as end date."""
    raw_apps = {
        "Beta": [RawRole("Designer", {"S": "2/1/2026"})],
    }
    today = date(2026, 3, 15)
    apps = build_timeline_data(raw_apps, config, today=today)

    assert len(apps) == 1
    assert apps[0].segments[-1].end == today
    assert apps[0].last_stage == "Submitted"


def test_build_timeline_skips_empty_stages(config):
    """A role with no matching flow stages is skipped."""
    raw_apps = {
        "Ghost": [RawRole("PM", {"Z": "1/1/2026"})],
    }
    apps = build_timeline_data(raw_apps, config, today=date(2026, 3, 1))
    assert apps == []


def test_build_timeline_multiple_companies(config):
    """Multiple companies produce multiple applications."""
    raw_apps = {
        "Acme": [RawRole("Eng", {"S": "1/1/2026"})],
        "Beta": [RawRole("PM", {"S": "2/1/2026"})],
    }
    apps = build_timeline_data(raw_apps, config, today=date(2026, 3, 1))
    assert len(apps) == 2
    assert {a.company for a in apps} == {"Acme", "Beta"}


# --- compute_summary ---


def test_compute_summary_basic(config):
    apps = [
        Application(
            company="Acme",
            position="Eng",
            submit_date=date(2026, 1, 1),
            segments=[
                Segment("Submitted", date(2026, 1, 1), date(2026, 1, 11)),
                Segment("Denied", date(2026, 1, 11), date(2026, 1, 11)),
            ],
            last_stage="Denied",
        ),
    ]
    stats = compute_summary(apps, config)

    assert len(stats) == 4  # S, R, A, X
    denied = next(s for s in stats if s.key == "X")
    assert denied.count == 1
    assert denied.percentage == 100.0
    assert denied.avg_days == 0.0

    submitted = next(s for s in stats if s.key == "S")
    assert submitted.count == 0
    assert submitted.avg_days == 0.0


def test_compute_summary_stage_with_zero_apps(config):
    """Stages with zero applications should not KeyError."""
    stats = compute_summary([], config)

    for stat in stats:
        assert stat.count == 0
        assert stat.percentage == 0.0
        assert stat.avg_days == 0.0


# --- sort_applications ---


def test_sort_active_before_terminal(config):
    active = Application(
        company="A",
        position="Eng",
        submit_date=date(2026, 1, 1),
        segments=[Segment("Submitted", date(2026, 1, 1), date(2026, 2, 1))],
        last_stage="Submitted",
    )
    terminal = Application(
        company="B",
        position="PM",
        submit_date=date(2026, 1, 1),
        segments=[
            Segment("Submitted", date(2026, 1, 1), date(2026, 1, 15)),
            Segment("Denied", date(2026, 1, 15), date(2026, 1, 15)),
        ],
        last_stage="Denied",
    )
    result = sort_applications([terminal, active], config)
    assert result[0].last_stage == "Submitted"
    assert result[1].last_stage == "Denied"


def test_sort_later_stage_first(config):
    early = Application(
        company="A",
        position="Eng",
        submit_date=date(2026, 1, 1),
        segments=[Segment("Submitted", date(2026, 1, 1), date(2026, 2, 1))],
        last_stage="Submitted",
    )
    late = Application(
        company="B",
        position="PM",
        submit_date=date(2026, 1, 1),
        segments=[
            Segment("Submitted", date(2026, 1, 1), date(2026, 1, 10)),
            Segment("Recruiter", date(2026, 1, 10), date(2026, 2, 1)),
        ],
        last_stage="Recruiter",
    )
    result = sort_applications([early, late], config)
    assert result[0].last_stage == "Recruiter"
    assert result[1].last_stage == "Submitted"


# --- group_by_company ---


def test_group_by_company():
    apps = [
        Application("Acme", "Eng", date(2026, 1, 1), [], "Submitted"),
        Application("Acme", "PM", date(2026, 1, 2), [], "Submitted"),
        Application("Beta", "Designer", date(2026, 1, 3), [], "Submitted"),
    ]
    grouped = group_by_company(apps)
    assert list(grouped.keys()) == ["Acme", "Beta"]
    assert len(grouped["Acme"]) == 2
    assert len(grouped["Beta"]) == 1

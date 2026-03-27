"""Shared test fixtures."""

import pytest

from app.models import FlowConfig


@pytest.fixture()
def config() -> FlowConfig:
    """Standard flow config used across test files."""
    return FlowConfig(
        stage_map={
            "S": "Submitted",
            "R": "Recruiter",
            "A": "Assessment",
            "X": "Denied",
        },
        colors={
            "Submitted": "#8294a8",
            "Recruiter": "#5b9bd5",
            "Assessment": "#70ad47",
            "Denied": "#787878",
        },
        flow_order=["S", "R", "A"],
        terminal_states=["X"],
    )

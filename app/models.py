"""Data models for the applications tracker."""

from dataclasses import dataclass, field
from datetime import date

DATE_FORMAT = "%m/%d/%Y"
"""Date format used in YAML files (M/D/YYYY)."""


class ConfigError(Exception):
    """Raised when a YAML config file contains invalid data."""

    def __init__(self, file: str, message: str) -> None:
        self.file = file
        self.message = message
        super().__init__(f"Error in {file}: {message}")


@dataclass(frozen=True)
class RawRole:
    """A role as parsed from YAML, before timeline construction."""

    position: str
    attrs: dict[str, str]  # stage_key → date_string
    note: str | None = None


@dataclass(frozen=True)
class Segment:
    """A time span within a single pipeline stage."""

    stage_label: str
    start: date
    end: date


@dataclass(frozen=True)
class Application:
    """A fully resolved job application with its timeline segments."""

    company: str
    position: str
    submit_date: date
    segments: list[Segment]
    last_stage: str
    note: str | None = None


@dataclass(frozen=True)
class StageStat:
    """Aggregate statistics for a single pipeline stage."""

    key: str
    label: str
    color: str
    count: int
    percentage: float
    avg_days: float


@dataclass
class FlowConfig:
    """Pipeline configuration loaded from flow.yaml."""

    stage_map: dict[str, str] = field(default_factory=dict)  # key → label
    colors: dict[str, str] = field(default_factory=dict)  # label → hex color
    flow_order: list[str] = field(default_factory=list)  # ordered flow keys
    terminal_states: list[str] = field(default_factory=list)  # terminal keys

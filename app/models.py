from dataclasses import dataclass, field
from datetime import date


@dataclass
class RawRole:
    position: str
    attrs: dict[str, str]
    note: str | None = None


@dataclass
class Segment:
    stage_label: str
    start: date
    end: date


@dataclass
class Application:
    company: str
    position: str
    submit_date: date
    segments: list[Segment]
    last_stage: str
    note: str | None = None


@dataclass
class StageStat:
    key: str
    label: str
    color: str
    count: int
    percentage: float
    avg_days: float


@dataclass
class FlowConfig:
    stage_map: dict[str, str] = field(default_factory=dict)
    colors: dict[str, str] = field(default_factory=dict)
    flow_order: list[str] = field(default_factory=list)
    terminal_states: list[str] = field(default_factory=list)

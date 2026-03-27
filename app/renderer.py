"""ANSI terminal rendering for the Gantt-style timeline."""

import os
from collections.abc import Callable
from datetime import date

from app.models import Application, Segment, StageStat
from app.transform import group_by_company

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
ITALIC = "\033[3m"

# Layout constants
SUFFIX_WIDTH = 30  # space reserved for "  Stage (Xd)" suffix column
MIN_LABEL_WIDTH = 30
MAX_LABEL_WIDTH = 70
LABEL_WIDTH_RATIO = 2 / 5  # fraction of remaining width for labels
FALLBACK_COLUMNS = 180  # used when terminal size can't be detected
LUMINANCE_THRESHOLD = 128  # above this → dark text, below → light text
FALLBACK_STAGE_COLOR = "#888888"


def _get_dimensions() -> tuple[int, int]:
    """Compute label and bar widths from the current terminal size."""
    try:
        columns = os.get_terminal_size().columns
    except OSError:
        columns = FALLBACK_COLUMNS
    remaining = columns - SUFFIX_WIDTH
    raw = int(remaining * LABEL_WIDTH_RATIO)
    label_width = min(MAX_LABEL_WIDTH, max(MIN_LABEL_WIDTH, raw))
    bar_width = remaining - label_width
    return label_width, bar_width


def hex_to_ansi_bg(hex_color: str) -> str:
    """Convert a hex color to an ANSI background escape sequence.

    Automatically picks a black or white foreground based on the
    perceived luminance of the background (ITU-R BT.601 formula).
    """
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    fg = "\033[30m" if lum > LUMINANCE_THRESHOLD else "\033[97m"
    return f"\033[48;2;{r};{g};{b}m{fg}"


def _format_summary(stats: list[StageStat], total: int) -> str:
    """Render the summary table with per-stage counts, percentages, and averages."""
    lines = [
        "",
        f"{BOLD}Summary:{RESET}  ({total} total applications)",
        "─" * 60,
        f"{'Stage':<24} {'Count':>5}  {'%':>6}  {'Avg Days':>8}",
        "─" * 60,
    ]

    for stat in stats:
        ansi = hex_to_ansi_bg(stat.color)
        label = f"{ansi} {stat.key} {RESET} {stat.label}"
        visible_len = len(f" {stat.key}  {stat.label}")
        padding = 24 - visible_len
        lines.append(
            f"{label}{' ' * padding} "
            f"{stat.count:>5}  {stat.percentage:>5.1f}%  {stat.avg_days:>7.1f}d"
        )

    return "\n".join(lines)


def _build_month_markers(
    min_date: date,
    max_date: date,
    date_to_col: Callable[[date], int],
    bar_width: int,
    label_width: int,
) -> str:
    """Build a row of abbreviated month labels aligned to the timeline columns."""
    month_chars = list(" " * bar_width)
    d = min_date.replace(day=1)
    while d <= max_date:
        col = date_to_col(d)
        month_label = d.strftime("%b")
        if 0 <= col <= bar_width - len(month_label):
            for j, ch in enumerate(month_label):
                month_chars[col + j] = ch
        if d.month == 12:
            d = d.replace(year=d.year + 1, month=1)
        else:
            d = d.replace(month=d.month + 1)
    return f"{DIM}{' ' * label_width}{''.join(month_chars)}{RESET}"


def _format_bar(
    segments: list[Segment],
    color_map: dict[str, str],
    date_to_col: Callable[[date], int],
    bar_width: int,
) -> str:
    """Render a colored bar representing an application's stage timeline."""
    bar = [" "] * bar_width

    for seg in segments:
        c1 = date_to_col(seg.start)
        c2 = date_to_col(seg.end)
        if c2 <= c1:
            c2 = c1 + 1
        if c1 >= bar_width:
            c1 = bar_width - 1
        if c2 > bar_width:
            c2 = bar_width
        color = color_map.get(seg.stage_label, FALLBACK_STAGE_COLOR)
        ansi = hex_to_ansi_bg(color)
        for c in range(c1, c2):
            bar[c] = f"{ansi} {RESET}"

    parts = []
    for cell in bar:
        if cell == " ":
            parts.append(f"{DIM}·{RESET}")
        else:
            parts.append(cell)
    return "".join(parts)


def render(
    apps: list[Application],
    stats: list[StageStat],
    colors: dict[str, str],
) -> None:
    """Print the full Gantt-style timeline to stdout."""
    label_width, bar_width = _get_dimensions()
    today = date.today()

    # Summary
    print(_format_summary(stats, len(apps)))

    if not apps:
        print(f"\n{DIM}No applications to display.{RESET}\n")
        return

    # Date range
    all_dates = [today]
    for app in apps:
        for seg in app.segments:
            all_dates.extend([seg.start, seg.end])
    min_date = min(all_dates)
    max_date = max(all_dates)
    total_days = (max_date - min_date).days or 1

    def date_to_col(d: date) -> int:
        return round((d - min_date).days / total_days * bar_width)

    # Header
    print()
    print(
        f"{BOLD}{'Application':<{label_width}} "
        f"{'Timeline':<{bar_width}}  Stage / Days{RESET}"
    )
    print("─" * (label_width + bar_width + 20))
    print(_build_month_markers(min_date, max_date, date_to_col, bar_width, label_width))

    # Application rows
    ellipsis_width = 3  # space reserved for "..." truncation indicator
    grouped = group_by_company(apps)
    for company, roles in grouped.items():
        print(f"{BOLD}{company} ({len(roles)}){RESET}")
        for app in roles:
            bar_str = _format_bar(app.segments, colors, date_to_col, bar_width)
            total_elapsed = (app.segments[-1].end - app.segments[0].start).days
            max_len = label_width - ellipsis_width
            truncated = app.position[:max_len].ljust(label_width - 2)
            suffix = f"{app.last_stage} ({total_elapsed}d)"
            max_suffix = SUFFIX_WIDTH - 2  # account for "  " separator
            if len(suffix) > max_suffix:
                suffix = suffix[: max_suffix - 1] + "…"
            print(f"  {truncated}{bar_str}  {suffix}")
            if app.note:
                print(f"  {ITALIC}{DIM}  └─ {app.note}{RESET}")

    print()

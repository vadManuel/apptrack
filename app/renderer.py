from datetime import date, datetime

from app.transformer import DataTransformer

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
ITALIC = "\033[3m"

BAR_WIDTH = 90
LABEL_WIDTH = 70


def hex_to_ansi_bg(hex_color):
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    fg = "\033[30m" if lum > 128 else "\033[97m"
    return f"\033[48;2;{r};{g};{b}m{fg}"


def build_timeline_data(transformer: DataTransformer):
    today = date.today()
    apps_data = []

    for company, applications in transformer.apps.items():
        for app in applications:
            attrs = app.get("attrs", {})
            position = app["position"]

            stages = []
            for key in transformer.flow_order:
                if key in attrs:
                    dt = datetime.strptime(attrs[key], "%m/%d/%Y").date()
                    stages.append((key, dt))

            terminal = None
            for t in transformer.terminal_states:
                if t in attrs:
                    dt = datetime.strptime(attrs[t], "%m/%d/%Y").date()
                    terminal = (t, dt)
                    break

            if not stages:
                continue

            segments = []
            for i, (key, start) in enumerate(stages):
                stage_name = transformer.stage_map[key]
                if i + 1 < len(stages):
                    end = stages[i + 1][1]
                elif terminal:
                    end = terminal[1]
                else:
                    end = today
                segments.append((stage_name, start, end))

            if terminal:
                t_key, t_date = terminal
                stage_name = transformer.stage_map[t_key]
                segments.append((stage_name, t_date, t_date))

            submit_date = stages[0][1]
            last_stage = segments[-1][0]
            note = app.get("note")
            apps_data.append(
                (company, position, submit_date, segments, last_stage, note)
            )

    return apps_data


def render(transformer: DataTransformer):
    today = date.today()
    apps_data = build_timeline_data(transformer)

    # Determine date range
    all_dates = [today]
    for _, _, _, segments, _, _ in apps_data:
        for _, start, end in segments:
            all_dates.extend([start, end])
    min_date = min(all_dates)
    max_date = max(all_dates)
    total_days = (max_date - min_date).days or 1

    def date_to_col(d):
        return round((d - min_date).days / total_days * BAR_WIDTH)

    # Summary
    total_apps = len(apps_data)
    stage_counts = {}
    stage_days = {}

    for _, _, _, segments, last_stage, _ in apps_data:
        stage_counts[last_stage] = stage_counts.get(last_stage, 0) + 1
        last_seg = segments[-1]
        days_in_stage = (last_seg[2] - last_seg[1]).days
        stage_days.setdefault(last_stage, []).append(days_in_stage)

    print()
    print(f"{BOLD}Summary:{RESET}  ({total_apps} total applications)")
    print("─" * 60)
    print(f"{'Stage':<24} {'Count':>5}  {'%':>6}  {'Avg Days':>8}")
    print("─" * 60)

    all_keys = transformer.flow_order + transformer.terminal_states
    for key in all_keys:
        name = transformer.stage_map[key]
        count = stage_counts.get(name, 0)
        pct = count / total_apps * 100 if count else 0
        avg_days = sum(stage_days[name]) / count if count else 0
        color = transformer.colors[name]
        ansi = hex_to_ansi_bg(color)
        label = f"{ansi} {key} {RESET} {name}"
        # pad accounting for ANSI escape codes (not visible width)
        visible_len = len(f" {key}  {name}")
        padding = 24 - visible_len
        print(f"{label}{' ' * padding} {count:>5}  {pct:>5.1f}%  {avg_days:>7.1f}d")

    # Header
    print()
    print(
        f"{BOLD}{'Application':<{LABEL_WIDTH}} "
        f"{'Timeline':<{BAR_WIDTH}}  Stage / Days{RESET}"
    )
    print("─" * (LABEL_WIDTH + BAR_WIDTH + 20))

    # Month markers
    month_chars = list(" " * BAR_WIDTH)
    d = min_date.replace(day=1)
    while d <= max_date:
        col = date_to_col(d)
        month_label = d.strftime("%b")
        if 0 <= col <= BAR_WIDTH - len(month_label):
            for j, ch in enumerate(month_label):
                month_chars[col + j] = ch
        if d.month == 12:
            d = d.replace(year=d.year + 1, month=1)
        else:
            d = d.replace(month=d.month + 1)
    print(f"{DIM}{' ' * LABEL_WIDTH}{''.join(month_chars)}{RESET}")

    # Sort: furthest in interview process first, quickest rejections last
    flow_stage_names = [transformer.stage_map[k] for k in transformer.flow_order]
    terminal_stage_names = [
        transformer.stage_map[k] for k in transformer.terminal_states
    ]

    def sort_key(app):
        company, position, submit_date, segments, last_stage, note = app
        is_terminal = last_stage in terminal_stage_names
        if not is_terminal:
            # Active: furthest stage (desc), then most recent
            stage_idx = (
                flow_stage_names.index(last_stage)
                if last_stage in flow_stage_names
                else -1
            )
            return (0, -stage_idx, -segments[-1][2].toordinal())
        else:
            # Terminal: furthest stage before terminal (desc)
            # then by how quickly they were rejected (quickest rejection = last)
            non_terminal = [s for s in segments if s[0] not in terminal_stage_names]
            max_flow = max(
                (
                    flow_stage_names.index(s[0])
                    for s in non_terminal
                    if s[0] in flow_stage_names
                ),
                default=-1,
            )
            total_elapsed = (segments[-1][2] - segments[0][1]).days
            return (1, -max_flow, -total_elapsed, submit_date.toordinal())

    apps_data.sort(key=sort_key)

    # Group by company, preserving sorted order
    from collections import OrderedDict

    grouped = OrderedDict()
    for company, position, _submit_date, segments, last_stage, note in apps_data:
        grouped.setdefault(company, []).append((position, segments, last_stage, note))

    # Application rows
    for company, roles in grouped.items():
        print(f"{BOLD}{company} ({len(roles)}){RESET}")
        for position, segments, last_stage, note in roles:
            bar = [" "] * BAR_WIDTH

            for stage_name, start, end in segments:
                c1 = date_to_col(start)
                c2 = date_to_col(end)
                if c2 <= c1:
                    c2 = c1 + 1
                if c1 >= BAR_WIDTH:
                    c1 = BAR_WIDTH - 1
                if c2 > BAR_WIDTH:
                    c2 = BAR_WIDTH
                color = transformer.colors.get(stage_name, "#888888")
                ansi = hex_to_ansi_bg(color)
                for c in range(c1, c2):
                    bar[c] = f"{ansi} {RESET}"

            bar_str = ""
            for cell in bar:
                if cell == " ":
                    bar_str += f"{DIM}·{RESET}"
                else:
                    bar_str += cell

            total_elapsed = (segments[-1][2] - segments[0][1]).days
            truncated = position[: LABEL_WIDTH - 3].ljust(LABEL_WIDTH - 2)
            print(f"  {truncated}{bar_str}  {last_stage} ({total_elapsed}d)")
            if note:
                print(f"  {ITALIC}{DIM}  \u2514\u2500 {note}{RESET}")

    print()

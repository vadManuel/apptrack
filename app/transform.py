from datetime import date, datetime

from app.models import Application, FlowConfig, RawRole, Segment, StageStat


def build_timeline_data(
    raw_apps: dict[str, list[RawRole]],
    config: FlowConfig,
    *,
    today: date | None = None,
) -> list[Application]:
    if today is None:
        today = date.today()

    applications = []
    for company, roles in raw_apps.items():
        for role in roles:
            attrs = role.attrs
            position = role.position

            stages = []
            for key in config.flow_order:
                if key in attrs:
                    dt = datetime.strptime(attrs[key], "%m/%d/%Y").date()
                    stages.append((key, dt))

            terminal = None
            for t in config.terminal_states:
                if t in attrs:
                    dt = datetime.strptime(attrs[t], "%m/%d/%Y").date()
                    terminal = (t, dt)
                    break

            if not stages:
                continue

            segments = []
            for i, (key, start) in enumerate(stages):
                stage_name = config.stage_map[key]
                if i + 1 < len(stages):
                    end = stages[i + 1][1]
                elif terminal:
                    end = terminal[1]
                else:
                    end = today
                segments.append(Segment(stage_name, start, end))

            if terminal:
                t_key, t_date = terminal
                stage_name = config.stage_map[t_key]
                segments.append(Segment(stage_name, t_date, t_date))

            applications.append(
                Application(
                    company=company,
                    position=position,
                    submit_date=stages[0][1],
                    segments=segments,
                    last_stage=segments[-1].stage_label,
                    note=role.note,
                )
            )

    return applications


def compute_summary(
    apps: list[Application],
    config: FlowConfig,
) -> list[StageStat]:
    total = len(apps)
    stage_counts: dict[str, int] = {}
    stage_days: dict[str, list[int]] = {}

    for app in apps:
        stage_counts[app.last_stage] = stage_counts.get(app.last_stage, 0) + 1
        last_seg = app.segments[-1]
        days = (last_seg.end - last_seg.start).days
        stage_days.setdefault(app.last_stage, []).append(days)

    stats = []
    all_keys = config.flow_order + config.terminal_states
    for key in all_keys:
        label = config.stage_map[key]
        count = stage_counts.get(label, 0)
        pct = count / total * 100 if count else 0
        avg = sum(stage_days.get(label, [])) / count if count else 0
        stats.append(
            StageStat(
                key=key,
                label=label,
                color=config.colors[label],
                count=count,
                percentage=pct,
                avg_days=avg,
            )
        )
    return stats


def sort_applications(
    apps: list[Application],
    config: FlowConfig,
) -> list[Application]:
    flow_labels = [config.stage_map[k] for k in config.flow_order]
    terminal_labels = [config.stage_map[k] for k in config.terminal_states]

    def sort_key(app: Application):
        is_terminal = app.last_stage in terminal_labels
        if not is_terminal:
            stage_idx = (
                flow_labels.index(app.last_stage)
                if app.last_stage in flow_labels
                else -1
            )
            return (0, -stage_idx, -app.segments[-1].end.toordinal())

        non_terminal = [s for s in app.segments if s.stage_label not in terminal_labels]
        max_flow = max(
            (
                flow_labels.index(s.stage_label)
                for s in non_terminal
                if s.stage_label in flow_labels
            ),
            default=-1,
        )
        total_elapsed = (app.segments[-1].end - app.segments[0].start).days
        return (1, -max_flow, -total_elapsed, app.submit_date.toordinal())

    return sorted(apps, key=sort_key)


def group_by_company(
    apps: list[Application],
) -> dict[str, list[Application]]:
    grouped: dict[str, list[Application]] = {}
    for app in apps:
        grouped.setdefault(app.company, []).append(app)
    return grouped

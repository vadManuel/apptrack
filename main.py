"""Entry point — wires loader → transform → renderer."""

import argparse
import sys

import yaml

from app.loader import load_applications, load_flow
from app.models import ConfigError
from app.renderer import render
from app.transform import build_timeline_data, compute_summary, sort_applications


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render a Gantt-style job application timeline.",
    )
    parser.add_argument(
        "--flow",
        default="flow.yaml",
        help="path to flow config YAML (default: flow.yaml)",
    )
    parser.add_argument(
        "--apps",
        default="applications.yaml",
        help="path to applications YAML (default: applications.yaml)",
    )
    args = parser.parse_args()

    try:
        config = load_flow(args.flow)
        valid_keys = set(config.flow_order + config.terminal_states)
        raw_apps = load_applications(valid_keys, args.apps)
        apps = build_timeline_data(raw_apps, config)
        stats = compute_summary(apps, config)
        sorted_apps = sort_applications(apps, config)
        render(sorted_apps, stats, config.colors)
    except FileNotFoundError as e:
        print(f"Missing file: {e.filename}", file=sys.stderr)
        sys.exit(1)
    except ConfigError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"YAML parse error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()

import re

import yaml


class DataTransformer:
    apps: dict = {}
    colors: dict = {}
    stage_map: dict = {}
    flow_order: list = []
    terminal_states: list = []

    def __init__(self, flow_path="flow.yaml", apps_path="applications.yaml"):
        with open(flow_path) as f:
            self._flow_data = yaml.safe_load(f)
        with open(apps_path) as f:
            self._apps_data = yaml.safe_load(f)

    def make_flow(self) -> None:
        for entry in self._flow_data["flow"]:
            key = entry["key"]
            self.stage_map[key] = entry["label"]
            self.colors[entry["label"]] = entry["color"]
            self.flow_order.append(key)

        for entry in self._flow_data["terminal"]:
            key = entry["key"]
            self.stage_map[key] = entry["label"]
            self.colors[entry["label"]] = entry["color"]
            self.terminal_states.append(key)

    def parse_applications(self) -> None:
        for company_entry in self._apps_data["applications"]:
            company = company_entry["company"]
            self.apps[company] = []

            for role in company_entry["roles"]:
                position = role["position"]

                increment = 0
                for app in self.apps[company]:
                    if app["position"] == position:
                        increment += 1
                    else:
                        pattern = rf"^{re.escape(position)} \((\d+)\)$"
                        m = re.match(pattern, app["position"])
                        if m:
                            inc = int(m.group(1))
                            if inc >= increment:
                                increment = inc + 1
                if increment > 0:
                    position = f"{position} ({increment})"

                self.apps[company].append(
                    {
                        "position": position,
                        "attrs": role.get("stages", {}),
                        "note": role.get("note"),
                    }
                )

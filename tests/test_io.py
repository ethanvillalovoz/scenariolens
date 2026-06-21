import json
import tempfile
import unittest
from pathlib import Path

from scenariolens.io import (
    load_scenarios,
    save_scenarios,
    scenario_from_dict,
    scenario_to_dict,
    scenarios_from_payload,
    scenarios_to_payload,
)
from scenariolens.samples import synthetic_scenarios


class ScenarioIoTest(unittest.TestCase):
    def test_scenario_roundtrip_preserves_core_fields(self) -> None:
        scenario = synthetic_scenarios()[0]
        decoded = scenario_from_dict(scenario_to_dict(scenario))

        self.assertEqual(decoded, scenario)

    def test_payload_roundtrip_preserves_scenario_count(self) -> None:
        scenarios = synthetic_scenarios()
        decoded = scenarios_from_payload(scenarios_to_payload(scenarios))

        self.assertEqual(len(decoded), len(scenarios))
        self.assertEqual(decoded[0].scenario_id, scenarios[0].scenario_id)

    def test_save_and_load_scenarios(self) -> None:
        scenarios = synthetic_scenarios()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scenarios.json"
            save_scenarios(path, scenarios)
            decoded = load_scenarios(path)

        self.assertEqual(decoded, scenarios)

    def test_load_rejects_unknown_version(self) -> None:
        payload = scenarios_to_payload(synthetic_scenarios())
        payload["version"] = 999

        with self.assertRaises(ValueError):
            scenarios_from_payload(payload)

    def test_load_rejects_unknown_agent_type(self) -> None:
        scenario = scenario_to_dict(synthetic_scenarios()[0])
        scenario["tracks"][0]["agent_type"] = "spaceship"

        with self.assertRaises(ValueError):
            scenario_from_dict(scenario)

    def test_saved_json_has_format_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scenarios.json"
            save_scenarios(path, synthetic_scenarios())
            payload = json.loads(path.read_text())

        self.assertEqual(payload["format"], "scenariolens.scenarios")
        self.assertEqual(payload["version"], 1)


if __name__ == "__main__":
    unittest.main()


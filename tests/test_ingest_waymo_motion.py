import unittest

from scenariolens.ingest.waymo_motion import (
    WAYMO_OPEN_CHALLENGES_URL,
    WAYMO_OPEN_DATASET_URL,
    adapter_status,
    ingest_waymo_motion,
)


class WaymoMotionIngestTest(unittest.TestCase):
    def test_adapter_status_documents_planned_optional_adapter(self) -> None:
        status = adapter_status()

        self.assertEqual(status.adapter_name, "waymo_motion")
        self.assertFalse(status.implemented)
        self.assertEqual(status.dataset_url, WAYMO_OPEN_DATASET_URL)
        self.assertEqual(status.challenges_url, WAYMO_OPEN_CHALLENGES_URL)

    def test_ingest_waymo_motion_raises_clear_placeholder(self) -> None:
        with self.assertRaises(NotImplementedError) as context:
            ingest_waymo_motion("input", "output", max_scenarios=1)

        self.assertIn("planned optional adapter", str(context.exception))


if __name__ == "__main__":
    unittest.main()


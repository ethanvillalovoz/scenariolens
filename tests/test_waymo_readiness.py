import tempfile
import unittest
from pathlib import Path

from scenariolens.waymo_readiness import inspect_waymo_motion_readiness


class WaymoReadinessTest(unittest.TestCase):
    def test_readiness_finds_candidate_downloaded_outside_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            configured_input = root / "data" / "raw" / "waymo" / "motion" / "validation"
            downloads = root / "Downloads"
            configured_input.mkdir(parents=True)
            downloads.mkdir()
            shard = downloads / "validation.tfrecord"
            shard.write_bytes(b"waymo shard placeholder")

            readiness = inspect_waymo_motion_readiness(
                configured_input,
                candidate_roots=(downloads,),
            )

            self.assertFalse(readiness.ready)
            self.assertEqual(readiness.preflight.supported_file_count, 0)
            self.assertEqual(len(readiness.candidate_files), 1)
            self.assertEqual(readiness.candidate_files[0].path, str(shard))
            self.assertTrue(
                any("Copy or move one candidate file" in action for action in readiness.next_actions)
            )

    def test_readiness_accepts_dependency_free_waymo_json_fixture(self) -> None:
        readiness = inspect_waymo_motion_readiness(
            "docs/examples/waymo_motion_native_sample.json",
            search_common_locations=False,
        )

        self.assertTrue(readiness.ready)
        self.assertEqual(readiness.preflight.supported_suffix_counts[".json"], 1)
        self.assertEqual(readiness.candidate_files, ())
        self.assertTrue(any("waymo-motion-validate" in action for action in readiness.next_actions))


if __name__ == "__main__":
    unittest.main()

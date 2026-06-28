import json
import tempfile
import unittest
from pathlib import Path

from scenariolens.waymo_shards import (
    generate_waymo_motion_shard_plan,
    waymo_motion_shard_plan_markdown,
    waymo_motion_shard_plan_payload,
)


class WaymoShardPlanTest(unittest.TestCase):
    def test_shard_plan_recommends_next_missing_indices(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _write_fake_shard(root, "validation.tfrecord-00007-of-00150")

            payload = waymo_motion_shard_plan_payload(
                input_path=root,
                split="validation",
                dataset_version="waymo_open_dataset_motion_v_1_3_1",
                total_shards=150,
                next_count=3,
            )

            self.assertEqual(payload["local_shard_count"], 1)
            self.assertEqual(payload["recommended_download_count"], 3)
            self.assertEqual(
                [row["index"] for row in payload["recommended_downloads"]],
                [8, 9, 10],
            )
            self.assertIn(
                "validation.tfrecord-00008-of-00150",
                payload["download_commands"][0],
            )
            self.assertIn(
                "failure-study-stability",
                payload["cross_shard_stability_command"],
            )

    def test_shard_plan_markdown_includes_access_note(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _write_fake_shard(root, "validation.tfrecord-00007-of-00150")
            payload = waymo_motion_shard_plan_payload(
                input_path=root,
                split="validation",
                dataset_version="waymo_open_dataset_motion_v_1_3_1",
                total_shards=150,
                next_count=1,
            )

            markdown = waymo_motion_shard_plan_markdown(payload)

            self.assertIn("Waymo Motion Shard Expansion Plan", markdown)
            self.assertIn("gsutil cp", markdown)
            self.assertIn("If `gsutil` returns a 401", markdown)
            self.assertIn("Cross-Shard Stability Command", markdown)

    def test_generate_shard_plan_writes_markdown_and_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            input_dir = root / "validation"
            input_dir.mkdir()
            _write_fake_shard(input_dir, "validation.tfrecord-00007-of-00150")
            output = root / "reports" / "shard_plan.md"
            json_output = root / "processed" / "shard_plan.json"

            result = generate_waymo_motion_shard_plan(
                input_path=input_dir,
                output_path=output,
                json_output_path=json_output,
                next_count=2,
            )
            manifest = json.loads(json_output.read_text(encoding="utf-8"))

            self.assertEqual(result.local_shard_count, 1)
            self.assertEqual(result.recommended_download_count, 2)
            self.assertTrue(output.exists())
            self.assertTrue(json_output.exists())
            self.assertEqual(manifest["recommended_download_count"], 2)


def _write_fake_shard(root: Path, filename: str) -> None:
    (root / filename).write_text("fake shard placeholder", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()

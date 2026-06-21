import tempfile
import unittest
from pathlib import Path

from scenariolens.portfolio import generate_portfolio_report, portfolio_markdown
from scenariolens.report import ranked_scores
from scenariolens.samples import synthetic_scenarios


class PortfolioTest(unittest.TestCase):
    def test_portfolio_markdown_includes_required_sections(self) -> None:
        scores = ranked_scores(synthetic_scenarios())[:1]

        markdown = portfolio_markdown(
            synthetic_count=10,
            waymo_like_count=2,
            synthetic_scores=scores,
            waymo_scores=scores,
            asset_prefix=Path("assets"),
        )

        self.assertIn("# ScenarioLens Portfolio Report", markdown)
        self.assertIn("## Executive Summary", markdown)
        self.assertIn("## Top Synthetic Scenarios", markdown)
        self.assertIn("## Normalized Waymo-Shaped Fixture Results", markdown)
        self.assertIn("## Limitations", markdown)
        self.assertIn("## Next Work", markdown)

    def test_generate_portfolio_report_writes_markdown_and_assets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            fixture = root / "waymo_motion_normalized.csv"
            fixture.write_text(
                "scenario_id,track_id,object_type,timestep,center_x,center_y,"
                "velocity_x,velocity_y,is_sdc,tags,source\n"
                "waymo_like,sdc,TYPE_VEHICLE,0,0,0,5,0,true,merge_conflict,fixture\n"
                "waymo_like,ped_1,TYPE_PEDESTRIAN,0,4,-2,0,1,false,"
                "pedestrian_crossing,fixture\n",
                encoding="utf-8",
            )
            output = root / "reports" / "portfolio.md"
            assets = root / "reports" / "assets"

            generate_portfolio_report(
                output_path=output,
                assets_dir=assets,
                waymo_normalized_path=fixture,
                top_n=1,
            )

            self.assertIn("ScenarioLens Portfolio Report", output.read_text())
            self.assertGreaterEqual(len(tuple(assets.glob("*.svg"))), 1)


if __name__ == "__main__":
    unittest.main()


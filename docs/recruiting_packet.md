# ScenarioLens Recruiting Packet

This packet turns ScenarioLens into a concise recruiting artifact for autonomy,
robotics, AI/ML, and software engineering internship conversations.

## Links

- Live demo: https://ethanvillalovoz.com/scenariolens/
- Repository: https://github.com/ethanvillalovoz/scenariolens
- Portfolio report: `docs/reports/portfolio_report.md`
- Tech stack rationale: `docs/tech_stack.md`

## GitHub Repository Metadata

Recommended repository description:

> Waymo-aligned autonomy scenario ranking and explorer for long-tail driving evaluation.

Recommended website:

> https://ethanvillalovoz.com/scenariolens/

Recommended topics:

- `autonomous-driving`
- `self-driving-cars`
- `waymo`
- `waymo-motion`
- `scenario-mining`
- `scenario-ranking`
- `motion-forecasting`
- `safety-evaluation`
- `python`
- `portfolio-project`

## Resume Bullets

Use one bullet if space is tight:

- Built ScenarioLens, a Waymo-aligned autonomy evaluation project that ingests motion scenarios, computes interpretable interaction/risk metrics, ranks long-tail driving cases, and serves a searchable static explorer.

Use two bullets if the project gets a dedicated entry:

- Built ScenarioLens, a local-first autonomy scenario evaluation tool that ingests synthetic, Waymo Motion-shaped JSON, normalized CSV, and small downloaded Waymo Motion TFRecord slices, then ranks long-tail cases using interpretable proximity, TTC, VRU, path-conflict, density, and taxonomy features.
- Shipped a tested portfolio demo with 60+ Python unit tests, GitHub Actions CI, SVG trajectory rendering, deterministic dashboard data, and a static Scenario Explorer deployed at `ethanvillalovoz.com/scenariolens`.

Short project line:

> ScenarioLens | Python, Waymo Motion-shaped data, scenario ranking, static dashboard

## 30-Second Pitch

ScenarioLens is a small autonomy evaluation project focused on a practical
deployment question: which rare driving scenarios deserve targeted evaluation
before an AV system is trusted in a new operating domain? Instead of attempting
to build a full self-driving stack, it builds a laptop-friendly pipeline for
ingesting motion scenarios, computing interpretable interaction and risk
features, ranking long-tail cases, and showing the results in a searchable demo.
I scoped it around public Waymo Motion-style records and clear testing so the
artifact is credible, inspectable, and lightweight.

## Interview Story

Problem:
Autonomous-driving systems need more than strong average-case behavior. They
need evidence on rare, interactive, safety-relevant cases such as pedestrians,
cyclists, blocked lanes, unprotected turns, close-proximity interactions, and
dense multi-agent scenes.

Approach:
ScenarioLens treats motion scenarios as the evaluation unit. It normalizes small
curated scenario records, computes lightweight interaction metrics, assigns
taxonomy tags, ranks scenarios by evaluation value, and exports both human- and
machine-readable artifacts.

Architecture:

1. Scenario schema in `src/scenariolens/schema.py`.
2. Ingestion adapters for synthetic scenarios, row-wise CSV, normalized
   Waymo-shaped CSV, protobuf-shaped Waymo Motion JSON, and small native
   Waymo Motion TFRecord slices.
3. Metrics and taxonomy scoring for proximity, TTC, VRUs, path conflicts,
   density, dynamics, and scenario category.
4. Report, portfolio, renderer, and dashboard exporters.
5. Static Scenario Explorer backed by deterministic JSON and SVG assets.

Why it is Waymo-relevant:
Waymo's public ecosystem includes Waymo Open Dataset, Waymo Motion, scenario
data, simulation, forecasting, and safety evaluation. ScenarioLens deliberately
aligns with that public boundary: it uses Waymo Motion-shaped records where
possible, reads the Motion fields needed for small downloaded slices, and
focuses on scenario triage rather than pretending to replace production
autonomy systems.

Tradeoffs:

- Chose motion/scenario data first instead of image or LiDAR because it is
  laptop-feasible and directly supports interaction analysis.
- Kept the core package dependency-free so reviewers can run tests quickly.
- Used deterministic checked-in demo data so the public artifact is stable.
- Kept the native Waymo reader narrow: it extracts the fields ScenarioLens
  needs instead of claiming full Waymo Open Dataset parity.

Testing and verification:

- Unit tests cover schema behavior, ingestion, metrics, reports, rendering, and
  dashboard data.
- GitHub Actions runs the test suite and static JavaScript syntax check.
- The public demo was browser-smoke-tested locally and deployed through the
  personal portfolio site.

What I would build next:

1. Expand the downloaded Waymo Motion validation-slice run into a documented
   scenario collection summary.
2. Add richer map and traffic-light context.
3. Add side-by-side scenario comparison and exportable collections.
4. Integrate a lightweight Waymax/JAX simulation path for scenario replay or
   perturbation.

## Claims To Keep Honest

- Do say: "Waymo-aligned", "Waymo Motion-shaped", "public-data oriented", and
  "portfolio evaluation tool".
- Do not say: "used Waymo's internal stack", "built a self-driving system", or
  "validated on full-scale Waymo production data".
- The strongest claim is the engineering artifact: a tested pipeline, static
  explorer, reproducible commands, public demo, and clear next-step roadmap.

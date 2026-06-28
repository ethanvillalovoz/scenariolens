# ScenarioLens v0.2.0 Outreach Draft

## Short GitHub/LinkedIn Post

I built ScenarioLens, a lightweight autonomy evaluation framework for mining
long-tail motion scenarios and finding where simple prediction baselines fail.

It ingests public Waymo Motion-shaped data and small local TFRecord slices,
computes interpretable interaction metrics, evaluates a constant-velocity
baseline with ADE/FDE and miss rate, then publishes public-safe reports and a
static Scenario Explorer.

The goal is not to build a self-driving system. It is to build the kind of
evaluation tooling autonomy teams rely on: scenario triage, failure analysis,
dataset understanding, and reproducible evidence.

Live demo: https://ethanvillalovoz.com/scenariolens/
Repo: https://github.com/ethanvillalovoz/scenariolens

## One-Sentence Pitch

ScenarioLens is a Waymo-aligned open-source framework for mining, ranking, and
analyzing long-tail autonomy motion scenarios with baseline failure evidence.

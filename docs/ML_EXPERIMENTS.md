# Running local forecasting experiments

Sprint 18 correction: the historical snapshot workflow now reports `migraine-onset-24h/v1.1`. Its 60/20/20 boundaries are fixed from the declared candidate grid before exclusions, with horizon/label-availability purging against those boundaries even if a later partition is empty. Coverage must have been confirmed by horizon end plus the fixed 24-hour lag; later-confirmed intervals cannot displace earlier evidence. Existing historical outputs are not rewritten. See [audit remediation](AUDIT_REMEDIATION.md) for regressions and synthetic before/after comparisons. The revision-aware Sprint 10 workflow remains the current research reference; correcting the legacy split does not supply real outcome evidence or clinical validation.

## Current Sprint 10 workflow

Use [ML_RESEARCH_BASELINE.md](ML_RESEARCH_BASELINE.md) and `python -m research.baseline_cli` for revision-aware research schema 2. It supports Sprint 9 numeric-history projection, explicit independent outcome journals, strict cutoff/freeze reconstruction, account isolation and opt-in synthetic software checks. It never turns app status into verified onset/coverage or reads a live database through its CLI. No eligible real bundle was supplied and no real-data fitting was performed. The remaining sections describe the preserved **legacy v1 snapshot workflow**, not an automatic migration or endorsement of historical app exports. Current v2.1 requires independent onset evidence and complete observation coverage for positives, complete explicit no-episode coverage for negatives, historical eligibility freezes and candidate-grid split boundaries. See the guide for exact policies.

Read [the audit and frozen protocol](FORECASTING_AUDIT.md) before preparing data. There is currently **no suitable real dataset and no trained or validated MigraMind forecasting model**. Automated tests use synthetic fixtures only, with no results presented as research performance. Do not relabel seed/demo fixtures as real longitudinal data.

## Install and audit

From the repository root, in PowerShell:

```powershell
cd backend
./.venv/Scripts/python -m pip install -r requirements-ml.txt
./.venv/Scripts/python -m research.cli --audit-db --account-id YOUR_ACCOUNT_ID --output-dir ../.research/local-audit
```

The audit is read-only and never trains. `.research/local-audit/report.json` contains aggregate completeness/provenance blockers. No health rows are printed to stdout. No external data is fetched. ML dependencies are optional and kept separate from runtime requirements. The tested environment is captured in `backend/requirements-ml.lock.txt`.

## Required local input contract

Use a reviewed, private bundle with research schema 1, never a bare final export. Generate the formal input schema without generating clinical records:

```powershell
New-Item -ItemType Directory -Force ../research-data | Out-Null
./.venv/Scripts/python -c "from research.contract import Bundle; import json; print(json.dumps(Bundle.model_json_schema(), indent=2))" | Set-Content -Encoding utf8 ../research-data/bundle.schema.json
```

The top-level fields are:

| Field | Requirements |
| --- | --- |
| research_schema_version | 1 |
| provenance | source_kind (`unknown`, `synthetic`, `real_longitudinal`), opaque participant_key, source_description, consent_confirmed, point_in_time_verified. Real/verified assertions require independent review, not automatic guessing. |
| snapshots | Full schema-3 MigraMind exports, each with its genuine aware exported_at timestamp and an explicit episodes list; optional wellness/early_symptoms/attack_sessions collections. Unique increasing snapshot times; stable record IDs. Contacts and profile are ignored by this contract. |
| coverage | start_at, end_at, confirmed_at (all offset-bearing), and complete. Complete means all attack onsets in the interval were actively ascertained, including explicit confirmation when none occurred. A wellness check-in or absent entry does not meet this definition. |

A raw export can be saved privately via Settings or by an explicit local request, for example:

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/api/export -OutFile ../research-data/current-export.json
```

This creates one snapshot of what is known **now**, not a historical dataset. Do not copy it to earlier dates or overwrite genuine snapshot metadata. The app currently has no formal observation-coverage collection flow or immutable journal. Establish those processes prospectively before creating a research bundle. Reconcile time-unknown episodes/recovery, onset quality and late reporting with the participant/research team; do not invent times or clinical outcomes.

The legacy pipeline is single participant. Do not concatenate different people's exports or transfer between unrelated participant keys. The application now enforces account ownership; the older v1 bundle itself only attests to participant identity. The v2 contract explicitly rejects mixed account journals. Use consented deidentified data and private local storage with appropriate access controls. Export and derived feature files still contain health information.

## Prepare, then explicitly opt in to fitting

Set real time bounds from the reviewed collection protocol, using offset-bearing timestamps. The following uses variable names so no fictitious clinical dates or records are implied:

```powershell
$researchStart = Read-Host 'Actual first prediction timestamp with UTC offset'
$researchEnd = Read-Host 'Actual exclusive end timestamp with UTC offset'
./.venv/Scripts/python -m research.cli --input ../research-data/verified-bundle.json --start $researchStart --end $researchEnd --timezone Asia/Kolkata --output-dir ../.research/preparation
```

Preparation never fits. Inspect aggregate exclusions, split counts and blockers in `report.json`. Optionally add `--write-dataset` to explicitly write sensitive `dataset.json` with feature rows and target/availability timestamps, in the ignored output directory. No notes or names enter the feature dataset. Audit mode refuses this option.

Only once all data/provenance/consent requirements have genuinely passed:

```powershell
./.venv/Scripts/python -m research.cli --input ../research-data/verified-bundle.json --start $researchStart --end $researchEnd --timezone Asia/Kolkata --train --output-dir ../.research/experiment-v1
```

Training refuses insufficient real longitudinal data, synthetic/unknown provenance, demo markers and inadequate purged classes. Do not weaken gates just to get numbers. The report includes source SHA-256, pipeline and dependency versions, feature list, time-grid configuration, exclusions, split counts, threshold rule and comparable validation/test metrics. Seeds and hyperparameters are fixed in source. Experimental reports are local only and never enable prediction serving. No pickled model is saved or loaded.

XGBoost is optional. If an appropriate compatible package is already installed, the adapter is included; otherwise its result explicitly says `dependency_unavailable`. Installation is a separate research environment choice. It was **not installed or trained in this sprint**. Logistic regression and the historical-frequency baseline were exercised only on synthetic fixtures inside automated tests.

## Tests

```powershell
./.venv/Scripts/python -m pytest -q
cd ../frontend
npm test
npm run build
npm run test:e2e
```

Optional logistic/reference-metric tests skip when scikit-learn is not installed. They ran in the verified environment. Core dataset, missing-data, split and unavailable-service tests do not require ML dependencies. Browser tests require the local frontend and installed Chrome as described in the root README. No test activates tel/SMS links or uses real clinical data.

## Before any real forecasting claim

Needed work includes prospective consented longitudinal collection; explicit negative-window ascertainment; immutable versioned event/availability history; a reviewed migraine onset/recovery definition; identity and provenance verification; preregistered power/sample-size and temporal validation plans; enough independent events and follow-up; missingness/bias analysis; clinically meaningful threshold and calibration assessment; uncertainty estimates respecting serial dependence; external and prospective validation; human-factors and safety review; and production privacy/access controls. Passing the current engineering gates or beating a baseline on one person's retrospective logs is insufficient.

A forecast must never be a prerequisite for seeking urgent help. This research has no connection to SOS dispatch or automatic emergency actions.

## Sprint 4 file inventory and verified results

Created: `backend/research/__init__.py`, `contract.py`, `dataset.py`, `models.py`, `evaluation.py`, `experiment.py`, `cli.py`; `backend/app/forecasting.py`; `backend/requirements-ml.txt`, `requirements-ml.lock.txt`; `backend/tests/test_research.py`; `frontend/src/AIInsights.tsx`, `AIInsights.test.tsx`; and both research guides in `docs/`.

Modified: `backend/app/main.py` (read-only versioned status route), `backend/tests/test_api.py`, `frontend/src/main.tsx`, `frontend/src/style.css`, `frontend/e2e/assistance.pw.ts`, root `README.md` and `.gitignore`. Existing model/schema/migration files were inspected but not changed. The private ignored `.research/local-audit/report.json` is an aggregate local audit artifact, not a dataset or model.

Verified: 46 backend tests, 18 frontend tests and 4 browser tests passed; production frontend build and Python dependency checks passed. All optional logistic/reference tests ran with installed scikit-learn. XGBoost remained unavailable. The read-only audit returned insufficient_data / trained false / model_served false. Existing live APIs and `/api/v1/forecast` responded successfully through the Vite proxy. No application data was used for model fitting; synthetic fits were limited to automated tests. One existing upstream TestClient deprecation warning remains. Actual phone/SMS handoff and screen-reader comfort still need manual checks; PostgreSQL remains unverified without a Docker daemon.

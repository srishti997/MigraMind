# Sprint 10: revision-aware offline research baseline

This pipeline evaluates software and, when independently reviewed inputs exist, a single account's research data. It does not diagnose migraine, recommend treatment, publish risk scores, save/load model artifacts, or change any application API/UI. No application health records were used for training. No eligible real research bundle was supplied in this sprint. Synthetic performance is not evidence of clinical effectiveness.

## Blockers identified before fitting

| Source | What can be reconstructed | What cannot currently be established |
| --- | --- | --- |
| Sprint 9 daily revisions | Submitted numeric observations/status, their reported event/observation instants, source-local date/zone, server availability, corrections and tombstones | A daily migraine status is not an exact verified episode onset. `event_at` is not promoted to onset time. |
| Diary episodes | Current exact starts where supplied | Original creation/edit/deletion availability and historical onset/recovery adjudication are absent. Current rows cannot be copied backwards in time. |
| Older wellness/early symptoms | Current reported values and original creation times | Historical corrections and deletions cannot be reconstructed. These sources are excluded from v2 features. |
| Completed no-migraine reports | An explicit statement confirmed after source-day end | Complete independent surveillance, reconciliation with diary conflicts, and coverage of an arbitrary next-24-hour interval are not established automatically. |
| Consent and research outcomes | An externally reviewed offline manifest/journal could supply these | The application has no research-consent or outcome-adjudication ledger. Support-sharing consent is not research consent. |

Consequently, the Sprint 9 adapter supplies **zero verified outcome records** and forces `outcome_history_complete=false`. It cannot train regardless of check-in counts. Real-data fitting requires a separately supplied, independently reviewed research-consent reference, source-integrity review, complete episode-history attestation and revisioned adjudication evidence. These references/booleans are attestations, not technical proof or clinical verification. An authorized research team must establish them; software cannot manufacture them from JSON.

## Dataset specification: research schema 2

`research/revision_contract.py` defines the strict machine-readable input. Generate its JSON schema without generating health records:

```powershell
cd backend
./.venv/Scripts/python -c "import json; from research.revision_contract import RevisionBundle; print(json.dumps(RevisionBundle.model_json_schema(), indent=2))"
```

| Field | Contract |
| --- | --- |
| `research_schema_version` | Exactly 2. Neither schema-5 app exports nor legacy schema-1 research bundles are silently accepted. |
| `account_key` | One opaque account pseudonym. Every daily/outcome revision must match; mixed/unclaimed records are rejected rather than filtered after pooling. |
| `captured_at` | Fixed aware input snapshot timestamp. No revision may occur after it. No implicit wall-clock `now` changes experiment results. |
| `provenance` | `source_kind` is `synthetic` or `consented`; nonblank `source_reference`, optional `consent_reference`, `provenance_verified`, `outcome_history_complete`. Consented inputs without reviewed provenance/consent cannot build labeled rows or train. |
| `daily_revisions` | Account key, stable record ID, contiguous revision starting at 1, creation/correction/deletion action, aware server `recorded_at`, and typed values (null only for deletion). |
| Daily values | Source date/IANA zone, migraine/no-migraine/unknown status, aware `event_at`, `observed_at`, `status_recorded_at`, optional sleep hours/quality, stress, hydration. `event_at <= observed_at <= status_recorded_at == recorded_at`; event source-local date must match. Daily identity is immutable and dates are unique per account. No free text, contacts, medications or identity fields. |
| `outcome_revisions` | Same revision envelope, with externally adjudicated onset, no-episode interval, observation interval or unknown interval values. Stable outcome kind per record; no deleted-record resurrection. |
| Outcome values | `kind`, aware `start_at`, optional `end_at` (required/increasing for intervals), `verified`, `independently_verified`, `verification_reference`, `complete`. Known ends must have occurred by server availability. Unknown episode ends remain unresolved. `verified` means protocol-reviewed evidence of the reported event, not a medical diagnosis. |

Every chain must start with creation, have contiguous unique revisions and nondecreasing actual availability timestamps. Equal availability times are ordered by revision number. Truncated/final-state-only journals fail validation. Account deletion removes the original journal; erased records cannot subsequently be reconstructed by this pipeline. Secure research retention, withdrawal handling and backup deletion require a separate approved policy.

`research/sprint9_adapter.py::project_account(session, account_id, account_key, provenance, captured_at)` is an explicit administrative, read-only projection, not a public endpoint. The caller supplies an authorized session and a consistent database read transaction. Consented-source projection rejects missing research consent or unreviewed provenance before querying any records. It queries that owner only, strips text and identity fields, and never queries legacy diary/wellness or infers outcomes. No CLI automatically connects to the application's database, reads users' records, or exports them. Synthetic API tests exercise this adapter using isolated databases only.

## Feature availability at cutoff

For each fixed cutoff `t`, choose the highest revision whose **server `recorded_at < t`**, separately for each record. A correction at exactly `t` is unavailable. A later correction/tombstone never rewrites earlier features; a tombstone already known before `t` removes that record. User-reported event/observation times cannot backdate availability. Select the latest event, not the most recently corrected old event.

Nine features, in a fixed matrix order:

- Latest completed source-local-day sleep hours, sleep quality, stress and hydration within the preceding seven elapsed days.
- Age of that latest event in elapsed hours; count of eligible daily reports and count of self-reported migraine days in that interval. A migraine-day count is not an exact onset count.
- Counts of distinct **verified onsets already available** in the preceding 7 and 30 elapsed days, when the outcome-history provenance is reviewed. These are observed counts, not negative labels for missing dates.

Optional absent measurements stay null; explicit zero stays zero. There is no field-wise carry-forward, causal trigger interpretation, severity reconstruction or free-text encoding. Empty historical observations exclude a sample. A pre-cutoff verified onset with no known recovery excludes that cutoff as ongoing/unresolved. An outcome journal revealing an attack already underway at `t` also excludes it. Source-local day completion uses IANA midnight boundaries, including 23/25-hour DST days; prediction windows always use UTC-normalized instants.

## Targets, coverage and historical freezes (v2.1)

Cutoffs use a predeclared 24-hour UTC grid, inclusive `--start`, exclusive `--end`. The outcome horizon is [t, t + 86,400 seconds), including onset at t and excluding onset at the end. DST does not change elapsed length. Outcome adjudication and eligibility freeze at horizon end plus `--label-lag-hours` (default 24; allowed 0-168). This lag is a protocol assumption, not evidence all reports have arrived.

- Positive: independently verified exact onset inside the horizon AND full-horizon independently verified, explicitly complete observation coverage. Coverage may be a continuous union of `observation_interval` and `no_episode_interval` records. No-episode evidence overlapping an onset is conflicting and excludes the window.
- Negative: no onset, and a continuous union of independently verified, explicitly complete `no_episode_interval` records covers the entire horizon. General observation coverage alone never proves no episode.
- Every relevant evidence record requires `verified=true`, `independently_verified=true`, and a nonblank `verification_reference` identifying separate protocol-reviewed source evidence. These fields are attestations: software cannot establish actual independence or clinical validity from JSON.
- Missing, unknown, unverified or incomplete coverage excludes a window, including otherwise positive windows. A gap of even one second prevents complete coverage. Daily statuses/absence never manufacture onset or surveillance evidence.
- Only revisions recorded at or before the per-window freeze affect label adjudication or eligibility. Deletions and moved/retracted onsets already known then exclude affected windows, rather than creating replacement negatives. Subsequent corrections/deletions cannot veto earlier frozen decisions; they can affect later features and decisions.

Three clocks are explicit per row: `snapshot_at` is the latest feature availability strictly before prediction; `outcome_as_of` is horizon end plus lag; `eligibility_as_of` equals the outcome freeze. `label_available_at` records that freeze for split purging. `--dataset-as-of` bounds the journal available to the build, defaults to `captured_at`, and cannot exceed capture. Immature windows are excluded. Reports record this boundary, policy version, planned grid, lag and split policy; CLI additionally records input/source/dataset hashes. Archive immutable inputs with reports: hashes cannot recover erased history. Changing provenance attestations or grid creates a new experiment, not a reconstructed historical decision.

The August 18 counterexample appended an unchanged correction to the first synthetic onset. The former all-journal veto removed a frozen January window and reduced training from 142 to 141. The regression now retains the identical 142 earlier training rows, including when that later revision is a deletion. Split boundaries also derive from the candidate grid rather than retained row counts, so a later holdout exclusion cannot shift training membership.

Frozen labels describe evidence known then, not current adjudicated truth. Withdrawal/legal erasure requires invalidating affected experiments under an approved retention policy, not silently changing historical cohorts. Truncated revision chains fail validation; unavailable/unverified history or insufficient evidence excludes examples. Real source timestamps, evidence independence and journal completeness still require external audit. No real-world adjudication data was provided.

## Splitting and baselines

`research/revision_dataset.py` rejects pooled accounts, duplicate/overlapping cutoffs and invalid point-in-time rows. A 60/20/20 chronological split uses the fixed candidate grid before outcome filtering or fitting. Purge training rows whose horizon **or label freeze** reaches the fixed validation boundary, and validation rows similarly before the fixed test boundary. Purged counts and retained split class counts are reported. No random row splitting or cross-person transfer is used.

Conservative engineering stop rules reuse the existing foundation: at least 180 eligible windows over 180 calendar days, 30 positive/60 negative overall, and after purging train at least 90 with 10 per class; validation/test at least 20 with 5 per class each. These are software stop rules, **not** a clinical sample-size/power calculation, research approval or readiness criterion. Single-class/empty data report blockers and no fitted-model metrics. All sources, including synthetic fixtures, face the same sample/class gates. Synthetic fitting additionally requires `--allow-synthetic-fit`.

The historical-frequency baseline predicts only the positive fraction among retained training labels. Logistic regression reuses the existing fixed `C=1`, `max_iter=1000`, seed 0 pipeline, with training-only median imputation, explicit missingness indicators, retained all-empty columns and standard scaling. Always-no-onset and always-onset baselines supply naive comparisons. Hyperparameters and threshold 0.5 are fixed before validation/test; no threshold tuning or test-based model selection occurs. There is no XGBoost fitting or model artifact serialization in v2.

All models use identical held-out rows. Reports give candidate/retained/excluded/purged counts, exclusions by reason, class balance, feature missingness, PR-AUC (explicit trapezoidal definition), separately named average precision, Brier score, ROC-AUC, five fixed calibration bins with denominators, descriptive calibration error and threshold metrics. Ranking metrics are null with a reason for empty/single-class samples; Brier is defined for nonempty valid samples only. The gate prevents fitting insufficient splits rather than fabricating probabilities or metrics. Brier improvement over the historical-frequency baseline is reported; calibration bins assess calibration rather than fit a calibration model. A constant-score trapezoidal PR curve differs from average precision; prefer the separately labeled definitions to an ambiguous “PR-AUC” claim. No independent-row confidence interval is manufactured for temporally dependent data.

## Reproducible software demonstration

Use the existing optional ML environment (no dependency changes are required). `backend/requirements-ml.lock.txt` records the tested package versions, including NumPy 2.5.4 and scikit-learn 1.9.1. Reproduce in an isolated environment; compatibility with other versions/platforms needs review.

```powershell
cd backend
./.venv/Scripts/python -m pip install -r requirements-ml.lock.txt
# Writes explicitly SYNTHETIC SOFTWARE TEST data and refuses to overwrite a file.
./.venv/Scripts/python -m research.synthetic_fixture --output ../research-data/synthetic-sprint10-v2.json
./.venv/Scripts/python -m research.baseline_cli --input ../research-data/synthetic-sprint10-v2.json --start 2024-01-01T00:00:00Z --end 2024-08-28T00:00:00Z --output-dir ../.research/sprint10-prepare
# Explicit software-test fitting; this is not a clinical experiment.
./.venv/Scripts/python -m research.baseline_cli --input ../research-data/synthetic-sprint10-v2.json --start 2024-01-01T00:00:00Z --end 2024-08-28T00:00:00Z --dataset-as-of 2024-08-31T00:00:00Z --train --allow-synthetic-fit --output-dir ../.research/sprint10-synthetic
```

The fixture contains 240 algorithmic windows, including 60 positive/180 negative software cases; no realistic disease process or population is simulated. Its verification flags describe constructed test cases only. Preparation without the synthetic opt-in reports a synthetic-fit blocker. Synthetic fitted reports are marked `synthetic_software_test_complete` and `synthetic_software_test_only`, with `clinical_validation=false` and `model_served=false`. Their apparent accuracy, calibration or baseline differences say nothing about actual migraine forecasting.

For a genuine reviewed bundle, use its actual protocol cutoffs and `--input` path, omit `--allow-synthetic-fit`, prepare without `--train`, inspect every exclusion/split/provenance blocker, then explicitly request `--train` only after independent approval. No eligible real input is supplied here. Do not copy a final app export into invented past versions or relabel synthetic data as consented. References cannot substitute for independent source review.

`report.json` contains aggregate metrics/configuration, input SHA-256, derived-dataset SHA-256, research-source hash, fixed input capture/grid, Python/package versions and limitations. Running identical inputs/configuration/code in the pinned environment yields identical reports. Model fits occur in memory and are discarded. Optional `--write-dataset` requires an explicit output directory and writes sensitive feature/label rows with opaque account keys; treat them as health data. Use ignored private `research-data/` and `.research/` directories, never commit exports/reports, and define retention before real research. Stdout prints status only; invalid private inputs produce a generic error without echoed health fields. No network calls, downloading, frontend predictions or app database writes occur.

## Verification and evaluation limits

```powershell
cd backend
./.venv/Scripts/python -m pytest -q
cd ../frontend
npm test
npm run build
```

Tests use only synthetic fixtures and isolated account databases. Coverage includes strict pre-cutoff availability, same-cutoff exclusions, backdating, corrections/tombstones, outcome freeze/withdrawals, interval gaps/conflicts, exact boundaries/DST, cross-account rejection, consent gates, schema rejection, chronological purging, training-only preprocessing, single-class/undefined metrics, deterministic generator/report hashes and reproducible synthetic fitting. No user application database was read for training or migrated. This sprint has no schema or frontend changes.

What can currently be evaluated: software correctness, reproducibility and behavior under explicitly constructed test cases; current versioned numeric-feature availability under the stated adapter contract. What cannot currently be evaluated: real next-24-hour predictive performance, clinical utility, population/generalization claims or deployment readiness. Remaining requirements include genuine research consent, independently reviewed onset/recovery and coverage histories, complete revision retention, a prospectively defined at-risk schedule, sensitivity to reporting lag/withdrawal, missing-not-at-random/selection bias assessment, dependence-aware uncertainty, preregistered sample-size/evaluation criteria and independent prospective/external validation. The running app continues to show insufficient evidence for forecasting.

Current correction verification results are recorded below after rerunning the complete isolated backend suite and synthetic offline CLI. Earlier frontend verification (56 tests and production build) predates this research-only correction; no frontend/API/schema behavior changed.

### Correction validation results

- **Outcome coverage: PASS (software contract).** `tests/test_baseline_v2.py` covers missing/unknown/gapped/incomplete coverage, independent verification/reference requirements for both classes, onset boundaries, conflicting evidence and general surveillance that cannot imply a negative. Real-world evidence independence is **NOT VERIFIED**: no eligible real input was supplied or used.
- **Future-dependent selection: PASS (synthetic reconstruction).** `test_august_18_correction_preserves_frozen_earlier_training_windows` retains identical 142 training rows after the August 18 correction/deletion; `test_future_holdout_exclusion_cannot_move_training_split_boundaries` checks a later exclusion cannot move earlier partitions. Snapshot immaturity, account isolation, cutoff availability, revision integrity and purging are covered in the same suite. Completeness and genuine availability timestamps of real source journals remain **NOT VERIFIED**.
- Final command `./.venv/Scripts/python -m pytest -q` from `backend`: **178 passed, 0 failed, 0 skipped**, one upstream Starlette/httpx deprecation warning, 37.05 seconds. Earlier focused run: 46 passed; later added coverage/split regressions are included in the final full suite.
- Generated `.research/sprint10-correction-fixture.json` using `python -m research.synthetic_fixture`; ran the documented CLI twice with explicit `--dataset-as-of 2024-08-31T00:00:00Z`, `--train --allow-synthetic-fit`, distinct private output directories. Both succeeded and reports were byte-identical. There were 240 synthetic windows (60 positive/180 negative), no exclusions, four purged rows, and train/validation/test sizes 142/46/48. Derived dataset SHA-256: `aa06ccb6fd7944ac3cc77f1cbd87c941183fe669cddc1b46669ed628d6776ff4`. These counts and results test software only, not forecasting effectiveness.
- `git diff --check` passed. Generated fixtures/reports, environment and local database paths are ignored; no files are staged. No real health records were read for training, no app predictions or unrelated runtime changes were introduced, and no commit/push/merge occurred. Frontend/build/browser checks were not rerun for this research-only correction.

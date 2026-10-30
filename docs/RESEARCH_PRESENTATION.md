# MigraMind research presentation

Sprint 17, 2026-10-30. Presentation claims are bounded by the [architecture](PROJECT_ARCHITECTURE.md) and [evidence matrix](PROJECT_EVIDENCE_MATRIX.md). This is a source-based account of engineering and research preparation, not a new experiment or literature review.

## Project overview and motivation

MigraMind combines an account-isolated migraine diary, explicit daily observations and user-controlled support preferences with an offline forecasting research foundation. Its central engineering question is whether a future evaluation can reconstruct what was actually known at each prediction time. Retrospective edits, missing reports and uncertain onset times can otherwise make a model appear useful without supporting prospective predictions.

The current contribution is a working prototype and a testable evidence contract: preserve unknowns, record prospective revisions, prevent historical leakage, inspect data quality and refuse unsupported forecasting claims. The application generates no migraine risk score. There is no validated forecasting performance, clinical benefit or real-data training result to present.

## Research question and estimand

The primary intended task is single-participant new migraine-onset forecasting in the next 24 elapsed hours at an at-risk cutoff `t`. The binary target concerns at least one independently verified exact onset in `[t, t + 86,400 seconds)`. An onset exactly at `t` is included; one exactly at the horizon end is excluded. Known ongoing attacks and unresolved recovery make a cutoff ineligible. Daily migraine status and assistance-session times are not exact-onset labels or diagnoses.

The current reference is [Sprint 10 v2.1](ML_RESEARCH_BASELINE.md), implemented in [revision_dataset.py](../backend/research/revision_dataset.py) and [baseline_v2.py](../backend/research/baseline_v2.py). The older [forecasting audit](FORECASTING_AUDIT.md) describes a separate snapshot-based foundation, optional XGBoost and validation-selected thresholds. Those choices must not be attributed to v2.1, which uses fixed threshold 0.5 and no XGBoost.

## Time, missingness and outcome evidence

Use a declared 24-hour UTC cutoff grid with inclusive start and exclusive end. The next-24-hour horizon remains 86,400 seconds through DST. Completed feature days use each report's own IANA timezone. For each record, choose its highest revision with server `recorded_at < t`; a correction exactly at the cutoff is unavailable. Backdating an event never backdates its availability. Later corrections/deletions do not rewrite earlier features.

The nine features are latest eligible completed-day sleep hours, sleep quality, stress and hydration; observation age; eligible daily-report and self-reported migraine-day counts over seven elapsed days; and already-available verified onset counts over 7/30 elapsed days. Optional absent values remain null, explicit zero remains zero, and no field-wise carry-forward occurs. Legacy editable observations, free text, contacts and post-onset treatment/duration are excluded from v2 features.

Both positive and negative windows need independently reviewed complete coverage over the entire horizon. Positives additionally need exact verified onset. Negatives require explicit complete no-episode intervals covering the entire horizon, with no contradictory onset. General observation intervals alone do not prove absence. Missing days, unknowns, gaps, conflicts, unverified evidence and incomplete coverage exclude windows rather than create negatives. Verification flags/references are attestations requiring real source review, not proof supplied by software.

Outcome adjudication and eligibility freeze at horizon end plus a specified reporting lag (default 24 hours, permitted 0-168). This is a protocol assumption, not proof of report completeness. Only revisions available by that freeze affect the historical decision. A captured snapshot and `dataset_as_of` bound reconstruction; immature windows are excluded. Later revisions can affect later decisions but cannot silently select a different earlier cohort. Frozen labels represent evidence known then, not current adjudicated truth. Withdrawal or legal erasure requires transparent snapshot revocation/versioning under an approved policy.

## Splits, models and evaluation

The fixed candidate grid determines chronological 60/20/20 train/validation/test boundaries before outcome filtering. Purge train/validation rows whose horizon or label-availability freeze reaches the next boundary. No shuffling, pooled-account training or test-driven selection is supported. Imputation, missingness handling and scaling fit on training data only.

V2 compares always-no-onset, always-onset, training-only historical frequency and fixed logistic regression (`C=1`, `max_iter=1000`, seed 0), on identical held-out rows. Threshold 0.5 and hyperparameters are fixed. Reports include candidate/retained/excluded/purged counts, exclusion reasons, per-split class balance, missingness, trapezoidal PR-AUC and separately named average precision, ROC-AUC, Brier score, five fixed calibration bins with denominators, descriptive calibration error and threshold metrics. Undefined metrics are null; ranking metrics also carry an explicit undefined-status reason. Calibration assessment is not a fitted calibration correction. Dependent time-series rows do not justify independent-row confidence intervals.

Engineering stop rules require at least 180 eligible windows over 180 calendar days, at least 30 positives/60 negatives overall, and after purging at least 90 train rows with 10 per class and 20 validation/test rows each with 5 per class. These gates are not a power calculation or proof of clinical sufficiency. Insufficient or single-class inputs stop fitting. A future real study still needs a preregistered design, dependence-aware uncertainty, selection/missingness analysis and independent prospective/external validation.

## Dataset decisions and synthetic limitations

The repository's [Park workbook audit](PARK_DATASET_AUDIT.md) records NO-GO for this strict prospective task. It found daily longitudinal observations, explicit no-headache answers and reported start/end times, but not verifiable submission availability, historical revisions, independently verified onset or complete rolling-horizon surveillance. Identifier/outcome contradictions also need reconciliation. Public access does not establish research consent or institutional privacy approval. A descriptive association study would need its own specification and review; it would not validate forecasting. This presentation summarizes the existing audit and does not claim to have re-downloaded the workbook.

There are two distinct synthetic paths: the small read-only January 2026 product fixture, and the offline deterministic software-test fixture. Neither simulates a validated disease process or population. Offline fitting requires explicit synthetic opt-in; apparent metric values test code behavior only. No real eligible bundle is supplied, and the application-to-research adapter emits zero verified outcomes. No performance number is used as a portfolio claim.

## Access and prospective pathway

[Research access](RESEARCH_DATA_ACCESS.md) drafts an unsent metadata-first inquiry to the published N1-Headache access route. Current authority, permissions, eligibility, journal semantics and transfer approval remain unconfirmed. No contact or data acquisition is authorized here. [The pilot protocol](PROSPECTIVE_PILOT_PROTOCOL.md) proposes feasibility work, not an approved study: accountable institution/PI, ethics/privacy determinations, genuine consent, secure operations and an independently defensible outcome process must precede recruitment. Its proposed 12-20 adults, 7-day run-in and 56-day observation are planning choices and cannot satisfy the current per-person 180-day baseline gate.

Apply the [readiness gate](RESEARCH_READINESS_GATE.md) before any future study. If independent onset/coverage or historical availability cannot be established, retain NO-GO rather than lower evidence requirements. No predictive UI, collection, model or deployment is added by Sprint 17.

## Five-minute technical demonstration

Prerequisite: use an already prepared dedicated local synthetic target and matching synthetic frontend under the [operations runbook](OPERATIONS_RUNBOOK.md). Do not provision over existing data. Do not type personal health details, call/SMS anyone, upload downloads or train during the presentation. If no demo is running, walk through source/documents rather than imply a live deployment.

| Time | Action and narration |
| --- | --- |
| 0:00-0:40 | Sign in to the fictional demo. Point out the synthetic/read-only banner: “This is tracking and research infrastructure; no clinical risk score is served.” |
| 0:40-1:30 | Open the guide's Daily status examples and private revision history. Explain migraine, explicit no migraine and unknown; distinguish event time from actual server creation time. The fixed fixture has creation revisions only; do not promise correction/deletion examples. |
| 1:30-2:10 | Use Show example calendar for the fixed January fixture. The episode date depends on device timezone. Blank dates do not prove no migraine. Show a read-only explanation without submitting a form. |
| 2:10-3:15 | Open Overview's research features, request the quality review and show insufficient forecasting evidence. The current completed-day window may exclude old fixtures; do not alter records to fill it. Explain zero verified outcomes and why daily status is insufficient. |
| 3:15-4:00 | Show the separate export confirmation and disabled download before consent. A download is optional and synthetic/local only; explain that confirmation is not study enrollment and the preparation file is not training eligible. |
| 4:00-4:35 | Show keyboard navigation, appearance and brief entry/exit of Attack Mode. Do not activate call/SMS or session writes. Support actions are user-initiated and independent of forecasting. |
| 4:35-5:00 | Show the architecture diagram and fixed-grid baseline boundary, then sign out. Close with the real gap: lawful longitudinal evidence and prospective validation, not a larger model. |

If a service fails, show its actual unavailable state and the corresponding source evidence; do not simulate a successful export or risk prediction. [Product review](PRODUCT_QUALITY_REVIEW.md) holds historical browser/build results and manual usability limits; these were not rerun by this documentation sprint.

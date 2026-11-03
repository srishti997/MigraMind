# MigraMind forecasting research: data audit and protocol v1

Historical protocol with Sprint 18 correction: the snapshot pipeline is now `v1.1`; [remediation](AUDIT_REMEDIATION.md) records the fixed-grid split and coverage-availability changes. This remains separate from the current [revision-aware baseline](ML_RESEARCH_BASELINE.md). No historical report is silently updated and no real forecasting performance is established.

This is an offline experimentation foundation, not a clinical model. No usable real longitudinal dataset was found, no model was trained on application records, no clinical performance is reported, and no model can trigger assistance actions. This audit predates account authentication. The current app has per-account authorization; the newer [account preparation foundation](PERSONALIZED_AI_FOUNDATION.md) documents current runtime data readiness. Original offline provenance and stop rules below remain conservative research requirements.

## Local inventory and provenance

Only local project files were searched for datasets. The search excluded installed dependencies, caches, build artifacts and browser test output. No clinical dataset was downloaded or synthesized. A local demo database was found, with mixed demo/unverified provenance and no suitable verified longitudinal training cohort. Record counts and private audit outputs remain local and are not included in this source repository. No rows with unverified provenance are assumed to be real clinical observations. Demo seeds and synthetic automated fixtures are not training data. There are no verified complete observation intervals or immutable past snapshots.

The repeatable read-only audit writes an aggregate report only when an output directory is requested. Its stdout reports status, not records or probabilities. The current result is `insufficient_data`, with no training. Counts may change as the local application is used.

## Schema audit

| Source | Collected | Forecasting limitations |
| --- | --- | --- |
| Episodes | Legacy local date; optional aware start/end normalized to UTC; IANA zone; optional severity/duration; location, symptoms, impact, notes, possible associated factor; medication names/times; optional session ID | Date-only rows have no exact onset. Creation/update timestamps and revisions are absent. End, severity and duration can be unknown. Current values may be retrospective edits. No clinician-adjudicated migraine definition or onset quality flag. |
| Wellness | Local date and zone; original creation timestamp; optional sleep hours/quality, stress, hydration, missed meals, screen estimate and cycle text | No edit history, exact exposure intervals, logging-adherence measurement, or explicit report of no attack. Same-day daily estimates can include post-onset information. Missing is not zero. |
| Early symptoms | Aware onset, original creation timestamp, zone, symptom and notes | Retrospective entry and edits can leak future knowledge. Not a proven prodrome or causal exposure. Original creation time does not timestamp later revisions. |
| Attack sessions | UTC start/end, unique active slot | Button presses are assistance-session timestamps, not adjudicated biological onset or recovery; linking does not make them additional episodes. |
| Contacts/profile | Support preferences, contacts and communication details | Not forecasting features. Not included in the research bundle contract or derived feature matrix. |
| Missing infrastructure | — | Explicit complete observation intervals including negatives; verified real/consented provenance; immutable versioned snapshots or an append-only event log; patient identity/isolation; prospective outcome adjudication; data quality/recovery flags. |

No migration is needed for this sprint. Existing schemas, migrations, records and CRUD flows are preserved. The research contract deliberately does not pretend that adding an export date reconstructs historical knowledge.

## Precise estimand and decision schedule

For a single consented participant, target `episode_onset_next_24h` is 1 if at least one deduplicated recorded episode starts in **[t, t + 24 elapsed hours)**, otherwise 0 only when that entire horizon is explicitly confirmed to have complete observation. The endpoint is recorded self-reported onset, not a clinically verified diagnosis. Multiple starts in a horizon still produce a binary 1. Self-reported records cannot by themselves establish clinical validity.

The CLI uses an explicit offset-bearing start and a fixed 24-hour UTC cadence until an exclusive end. Target duration stays 86,400 seconds during daylight-saving changes; it is not a variable-length local calendar day. All comparisons use aware UTC instants. A fixed IANA reporting timezone is part of the experiment configuration. Previous-day wellness eligibility uses that record's own timezone. Travel and time-zone changes remain potential sources of bias.

Prediction is only for an at-risk time, without an ongoing attack. Known overlapping intervals and exact duplicate starts are merged; touching but non-overlapping intervals remain distinct. Unknown ends conservatively leave an attack unresolved and exclude later prediction times. A prior legacy date-only episode also conservatively excludes decisions because the ongoing state cannot be reconstructed; no midnight onset or recovery is invented. These exclusions can be severe and require quality review, not automatic repairs.

A later outcome snapshot may reveal an attack already underway at t, making the decision retrospectively ineligible. Unknown onset dates touching the horizon exclude that target. Ongoing or unresolved cases are not force-labeled negative. Planned/future-dated onsets in an export do not become observed history. Future ends are treated as unresolved at that snapshot.

Labels require continuous confirmed coverage over the whole horizon, even for positives, to avoid selecting positives through better logging while guessing negatives from missing entries. Coverage confirmation is required after the interval ends and, in v1.1, by horizon end plus the fixed 24-hour reporting lag; this is an engineering assumption to preregister and examine, not evidence that all late reporting has arrived. The first snapshot at or after that maturity supplies the outcome and its actual availability timestamp. Later-confirmed coverage is excluded rather than delaying or replacing earlier evidence. Late corrections, missed onsets and selective reporting still require prospective adjudication.

## Leakage barriers

- A full, immutable snapshot must have been exported strictly before t to supply features. A single final export cannot be backdated into many historical snapshots. The current editable schema's original `recorded_at` alone is not revision availability.
- Features use only values in that snapshot; recorded times must precede t and not exceed snapshot availability. No outcome-window symptoms, post-onset medicines, later revisions, final attack duration, assistance actions, free text or contact information enter the matrix.
- Historical counts are counts of **observed onsets** in the preceding 7/30 elapsed days, not estimates of attacks on unobserved days. No missing diary day is relabeled symptom-free. Logging intensity can itself bias these features.
- Previous sleep, sleep quality, stress, hydration, missed meals and screen estimates come from the latest available check-in with a completed local date, at most seven days old. There is no zero fill or carry-forward across fields. Age, observation counts, a seven-day stress mean and available early-symptom counts are explicit features. Missing numerical values remain null until training-only imputation; all features also get missingness indicators.
- A fixed 60/20/20 chronological split uses the declared candidate grid before outcome filtering or fitting; no shuffling or participant pooling. Train rows whose horizon or label availability reaches the fixed validation boundary are purged. Validation rows are similarly purged before the fixed test boundary, even if validation/test retains no rows. A delayed final label snapshot can make all training rows unusable: that is correct, not a reason to waive the barrier.
- Imputation and scaling fit only on train. Hyperparameters are fixed, not tuned on the test set. Threshold selection uses validation only. The held-out test is not used for model selection, fitting, calibration, or threshold choice.

The contract requires one participant per bundle. A provenance boolean is an attestation, not technical proof: external verification of consent, snapshot integrity, source dates and identity is still required. No code can establish genuine clinical provenance just from JSON fields.

## Baselines, evaluation and stop rules

`HistoricalFrequency` predicts the training-only proportion of positive, fully observed eligible 24-hour windows. It never divides attacks by days with absent diary records. Logistic regression uses median imputation with empty-column retention, explicit missingness indicators, standard scaling and fixed regularization. XGBoost has a deterministic, small fixed configuration and is used only when its optional package is installed; it is not installed by default or required by the API. No model artifacts are deserialized or deployed.

The engineering gates require >=180 labeled windows spanning >=180 days, >=30 positive and >=60 negative windows overall, and after purging: train >=90 with >=10 of each class; validation/test each >=20 with >=5 of each class. These are conservative **stop rules, not a formal sample-size calculation or evidence of clinical sufficiency**. They do not turn synthetic rows into real data. Source must be `real_longitudinal`, with a documented single participant, verified consent and point-in-time integrity, and no detected demo records. Insufficient or single-class splits do not train.

The report compares each model against the historical baseline on the same validation and test rows. It reports:

- ROC-AUC; trapezoidal PR-AUC and separately named average precision, with tied scores grouped. Ranking metrics are null with a reason for empty/single-class data.
- Brier score on any nonempty valid binary sample. Null on empty input.
- Five fixed reliability bins (count, mean prediction, observed frequency), descriptive expected calibration error. This is calibration **assessment**, not a fitted calibration correction or proof of calibration.
- Sensitivity TP/(TP+FN), false-positive rate FP/(FP+TN), false alerts per 100 observed prediction windows, false discovery rate FP/(TP+FP), alert rate and denominators. Absent denominators produce null, not fabricated zeroes.
- Small-sample flags. No inferential claim or confidence interval is invented. Temporal dependence means naive independent-row confidence intervals would be misleading; a preregistered block-resampling protocol is still needed.

Each model's threshold is selected solely on validation from a fixed grid to maximize sensitivity subject to validation FPR <=0.10, preferring higher thresholds on ties. A threshold above 1 explicitly represents never alerting. This is an experimental comparison rule, not a clinical intervention policy. Brier/ranking/calibration metrics use raw probabilities regardless of this threshold. No alert is issued by the running app.

## Runtime boundary

GET `/api/v1/forecast` returns contract v1, a 24-hour target, `insufficient_data`, null probability/model version, explicit missing-data reasons, `clinically_validated: false` and `emergency_actions_affected: false`. Even a future internal data-readiness review yields `model_unavailable` until a separate validated-model integration exists. There is no HTTP flag, environment variable, experiment report or artifact path that enables serving. Forecast status has no database writes. Runtime does not import ML packages, train, load a model, suggest medications or affect call/SMS/112 access.

The discreet **AI Insights — In Development** section appears on Overview and handles unavailable/offline status without percentages. Warm Day, Gentle Dark and Attack Mode are preserved. No public deployment was made.

## Method references

Implementation choices were checked against primary library documentation: [scikit-learn chronological evaluation and train-only preprocessing](https://scikit-learn.org/stable/modules/cross_validation.html), [probability calibration](https://scikit-learn.org/stable/modules/calibration.html), [evaluation metrics](https://scikit-learn.org/stable/modules/model_evaluation.html), and [XGBoost's classifier API](https://xgboost.readthedocs.io/en/stable/python/python_api.html#xgboost.XGBClassifier). These references describe tools and methods; they do not validate MigraMind or establish clinical sample requirements.

# Personalized AI data foundation (no forecasting model)

## Sprint 9 collection extension

Sprint 10 adds a separate [revision-aware offline dataset specification and baseline guide](ML_RESEARCH_BASELINE.md). Research schema 2 reconstructs numeric check-ins strictly from pre-cutoff revisions and requires a separately reviewed onset/no-episode journal for labels. The explicit read-only account adapter supplies no verified outcomes. Consented-source provenance and outcome-history blockers remain; unknown, incomplete, conflicting, withdrawn or historically unverifiable outcomes are excluded rather than guessed negative. Synthetic fitting is opt-in software verification only. The runtime foundation below, forecasting API and frontend are unchanged, with no risk scores or established runtime prospective labels. No real-data fitting, model deployment or migration is included.

Migration 008 now adds a separate account-owned daily status and optional observation collection with application-enforced append-only revisions, correction availability timestamps and deletion tombstones. It preserves all legacy rows. Open **Daily status**, and review descriptive coverage under AI Insights > **Daily collection quality**. See [the full collection contract](PROSPECTIVE_COLLECTION.md) for schema, APIs, retention and timestamp semantics. This extension supersedes the earlier statement that no durable record history exists **for these new daily reports only**; the existing read-only adapter below still uses legacy sources without immutable historical versions.

New reports distinguish user-reported `event_at`, user-reported `observed_at`, source local date/IANA timezone, first server `created_at`, and revision server `recorded_at`/`status_recorded_at`. Current versions saved after their source date are retrospective; revisions preserve when each earlier version was actually available. Same-day collection supports a future prospective protocol but does not establish a verified prospective outcome. Optional fields remain null when absent, including zero-versus-missing distinctions. Missing dates never imply no migraine. A no-migraine status saved before day-end remains provisional until explicitly reconfirmed after that day ends; midnight rollover alone cannot create a negative label. Episode and older wellness discrepancies remain visible and unresolved.

The new quality endpoint reports account-only observed dates, explicit completed nonconflicting no-episode dates, unknown dates, same-day/retrospective current versions, missing fields, corrections and tombstones. It separates other-source-zone reports rather than remapping dates. These counts are descriptive; they do not replace the existing readiness adapter, feed predictors or supply verified 24-hour outcomes. The readiness service continues to establish zero prospective labels; forecasting remains unavailable with insufficient evidence, irrespective of record counts.

Deleting a daily report hides its current health values and appends a null-valued tombstone; authorized prior values remain available in private history and schema-5 exports. Account deletion erases both tables in the account deletion transaction. Backups/downloads remain separate copies; automatic retention expiry and production backup erasure are not implemented. Existing legacy forms remain outside this audit mechanism. No tamper-evidence against database administrators, research consent, complete surveillance or clinical validity is implied.

Future evaluation must reconstruct only versions available strictly before each cutoff, applying deletion state as known then and excluding later corrections even if their event times predate cutoff. Final current-row exports cannot substitute for historical availability. A prospective consented protocol must define complete coverage, reconcile disagreements, freeze labels after the full elapsed-24-hour horizon and reporting lag, and use purged chronological evaluation with training-only preprocessing. No arbitrary count threshold establishes clinical readiness. No forecasting model was trained, deployed or activated in Sprint 9.

## Scope and use

On branch `feat/personalized-ai-foundation`, the existing diary, descriptive Insights, authentication and assistance flows remain intact. On Overview, expand **Your data readiness** under **AI Insights ? In Development**, then select **Review data readiness**. The explicit request reads the current account only and stores nothing. It does not train, predict, export records, request location or affect emergency access.

`GET /api/v1/data-readiness?timezone_name=UTC&days=30` uses existing session/CSRF authorization, server-selected identity, ownership-filtered queries, and no-store responses. Reporting days are restricted to 7?90; invalid IANA zones are rejected. Caller-supplied owner IDs or historical cutoffs cannot change scope or backdate preparation. No record text, contact details, cycle notes, medication data, credentials or session IDs enter preparation. No health payloads are logged.

No migration is required: this is a read-only adapter over migration 007's existing schema. No old records are assigned to accounts or changed. No automatic research enrollment or persistence is introduced. Unclaimed legacy records are excluded by ownership filtering. Current preparation captures are ephemeral, **not a durable immutable history**. Persisted, consented, tamper-evident versions are future work.

## Data contract and implementation

`research/account_foundation.py` projects account-owned rows into the existing internal research `Snapshot` contract. It rejects mixed-account or unclaimed rows and copies allowlisted primitive fields. The existing research `point_features` function supplies the time-aware baseline feature preparation; no ML libraries or model modules are imported by this service. `account-preparation/v1` is separate from the unchanged forecasting API and offline experiment version.

| Source | Prepared fields | Availability and missingness |
| --- | --- | --- |
| Episodes | ID, legacy date, exact start/end, severity | No original creation/revision timestamp exists. Current values are known only at capture. Null severity stays null; zero is a valid observed rating. Date-only attacks do not become midnight onsets. |
| Wellness | ID, date, source IANA zone, recorded time, optional sleep hours/quality, stress, hydration, meals, screen hours, optional whole-day status and confirmation timestamp | Creation time does not establish revision availability. Daily aggregates do not have exact exposure times. Unknown fields stay null; meals false is valid zero. Whole-day status is used for coverage descriptions only, not feature predictors or historical labels. |
| Early symptoms | ID, onset, recorded time | Both timestamps must be aware; onset cannot follow recording. No free-text symptom content is prepared. These are possible observations, not proven prodromes. |

Features include observed onset counts over the prior 7/30 elapsed days; elapsed time since observed onset; latest previous completed source-local-day wellness values within 7 days; stress mean and wellness count over 7 days; observed early-symptom count over 24 elapsed hours; and available 30-day severity mean/count. Features carry explicit missing indicators. Severity averages exclude nulls; zero-only averages remain zero. Missing severity does not reduce the total onset count. Observed counts of zero mean no qualifying records in the capture, **not evidence of no attacks or symptoms**. No imputation, field-wise carry-forward, learned normalization, causal interpretation or training occurs.

## Cutoff and leakage rules

All records are read before the capture timestamp is assigned. The prospective preparation cutoff is one microsecond after this temporary capture; the horizon is **[cutoff, cutoff + 24 elapsed hours)**. The next-day boundary is exactly 86,400 seconds across DST, rather than a local calendar date. This is a reproducible preparation boundary, not a deployed prediction schedule or score.

`prepare` rejects snapshots at or after the cutoff. It cannot substitute a final export for past knowledge. Wellness and symptom recording times must be before cutoff and no later than capture; future onsets are not historical features. Same-day wellness cannot enter previous-day features. Its own source timezone determines when a wellness date ends, including 23/25-hour DST days and travel differences. Reporting-zone coverage uses the existing descriptive-insights day-boundary rules.

Unresolved/ongoing attacks and date-only attack history conservatively block at-risk preparation. Invalid episode history also blocks preparation rather than silently making a person eligible. Other invalid source rows are excluded with source-level counts. Later changes to live rows do not modify an already copied capture. End times are used only for at-risk eligibility; final duration, medicines, support actions and outcome-window symptoms never become predictors.

Original recorded times do not establish historical edit availability. A retrospective entry may be included only in a later prospective capture, never backdated into a historical feature. Captures are not persisted here, so no retrospective training matrix can legitimately be built from this endpoint's current rows.

## Coverage, labels and readiness

The assessment shows completed reporting dates, timed recorded episode dates, explicit completed whole-day no-episode reports, unknown dates, conflicting reports, onset-unknown episode reports, check-in and timed early-observation counts, and available/missing values. The denominator for severity is timed onsets in the reporting window; wellness denominators are check-ins, not all reporting days. Invalid source rows are counted separately. Blank dates and absent fields are never zero-filled. Whole-day negatives are excluded when timing, confirmation, conflicts, continuing attacks or timezone alignment make them uncertain (existing descriptive-insights rules).

The prospective target remains whether a recorded episode starts in the next 24 elapsed hours. Exact starts can describe **candidate observed positives** after the fact; a missing start cannot establish a negative. Date-only attacks cannot label exact onset windows. Whole-day no-episode reports can describe local dates, but do not by themselves establish complete, prospective next-24-hour outcomes at an arbitrary cutoff. Current rows have no immutable cutoff feature history, outcome-adjudication history or independently verified surveillance coverage.

Therefore this runtime foundation reports **zero established positive and negative prospective labels**, no established candidate prediction grid, and unknown unlabeled-window count. Reporting dates are not mislabeled as forecast samples. The target and probability remain null. This is a conservative statement of evidence availability, not a claim that no attacks occurred. Training and evaluation are always unjustified in this runtime version, regardless of row counts. The forecast endpoint remains unavailable; no flag enables a model.

## Readiness criteria and future evaluation plan

Before future experiments: obtain explicit research consent and independently review provenance; collect append-only, account-linked event versions and actual availability timestamps; define a prospective at-risk prediction schedule; collect complete observation intervals and reconcile onset/recovery/late reports; snapshot labels after the full horizon and predefined reporting lag. Clinical adjudication and privacy/security review remain distinct requirements.

Reuse the existing offline protocol only after these conditions hold: single-participant chronological 60/20/20 splits; purge horizons and label availability across boundaries; fit imputation/scaling on training only; compare train-only historical-frequency and fixed logistic-regression baselines; consider optional XGBoost later. Select thresholds on validation, never test. Report ROC-AUC/PR-AUC only with supported classes, Brier score and calibration with denominators, sensitivity and false-alert rates; missing/undefined metrics remain null. Preregister temporal-dependence-aware uncertainty assessment and prospective external validation.

Existing engineering stop rules (180 labeled windows over 180 days, minimum class counts and adequate purged splits) remain **necessary gates, not a clinical sample-size justification**; see FORECASTING_AUDIT.md and ML_EXPERIMENTS.md. This sprint does not invoke offline fitting, change those thresholds, generate performance evidence or deploy anything.

## Local audit privacy

The existing administrative `--audit-db` command now requires `--account-id YOUR_ACCOUNT_ID` and filters every source by that ID. Unclaimed and other-account records are excluded. It captures after all reads. This is a local administrator command using database access, not an authentication API; use the authenticated readiness panel for ordinary account access. No new endpoint serves audit files. Sensitive optional outputs remain ignored and local. Raw schema-4 account exports are not automatically accepted as historical schema-3 research bundles: genuine availability metadata and source review are still required.

## Validation and limits

Synthetic automated fixtures cover mixed-account rejection, API/CLI isolation, CSRF, missing versus zero, late records, future onsets, same-cutoff rejection, copied-capture stability, unknown/invalid ends and source-local DST completion. Existing research tests cover prospective-label gating and chronological purging. Frontend tests cover explicit loading and failure behavior without fabricated results. No real records are edited or used as fixtures.

Still unverified: PostgreSQL execution, durable research consent/versioning/coverage infrastructure, screen-reader/device usability of this panel, large-history performance, longitudinal provenance and clinical forecasting validity. There is no accuracy claim. No new schema, model artifact, public deployment or predictive training is included.


Verification in this workspace: 108 backend tests, 51 frontend unit tests, all 13 Playwright tests and the production build passed. The full browser suite, including the two-account account lifecycle test, ran against a fresh isolated synthetic database. The existing local database was not used for browser writes; its checksum remained unchanged during the review. One existing upstream TestClient deprecation warning remains. Browser coverage checks explicit read-only loading, keyboard disclosure, 320px overflow and both themes; it is not a screen-reader or clinical usability evaluation.

Known interface limitation: invalid-record counts and detailed exclusion warnings are available in the authenticated readiness response but are not yet displayed in the panel. Readiness remains blocked rather than implying invalid records are complete evidence. No real health data, credentials, local database, research output or generated artifact is part of this change.

Sprint 10 correction policy v2.1 requires independently referenced onset evidence and complete observation coverage for positives, and explicit complete no-episode coverage for negatives. Per-window outcome/eligibility freezes and a separately selected dataset-as-of boundary preserve historical decisions. Chronological split boundaries use the candidate grid rather than retained labels. See [ML_RESEARCH_BASELINE.md](ML_RESEARCH_BASELINE.md) for the August 18 regression, metadata, withdrawal implications and external-verification limits.


Sprint 11 adds a [completed-day quality dashboard and explicit local preparation download](RESEARCH_DATA_QUALITY.md), reusing daily revisions and the offline validation contract. It neither supplies verified outcomes nor changes forecasting readiness. Missingness, confirmation cutoffs, source timezones and existing histories remain distinct; no automatic correction, model training, schema migration or external sharing is introduced.

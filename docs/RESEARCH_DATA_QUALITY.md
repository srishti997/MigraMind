# Sprint 11: research data quality and evaluation readiness

Open Overview > AI Insights > Research data quality > Review research quality. This is an explicit read-only review, not a risk score. Daily status > Review yesterday prepares the existing form for the preceding local date with Unknown selected for a new report; choose a status and save. For an existing report it opens the existing correction flow, preserving values, date, timezone and revision controls. Deleted dates remain reserved. Nothing is saved by opening either review.

## Reused architecture and current blockers

Sprint 9 daily reports and append-only revisions remain the source of current numeric observations and historical availability. Existing date/time validation, ownership, session/CSRF/origin checks, optimistic edits and deletion history are unchanged. The quality service reuses Sprint 9 episode-date reconciliation and Sprint 10 DailyValues/RevisionBundle validation instead of inventing a second historical format. Existing descriptive collection quality and legacy readiness views remain available.

Caregiver support-card sharing consent is contact-specific and does not authorize research enrollment or downloads. Sprint 11 reuses the explicit-confirmation, authenticated API and local-download patterns, while keeping a separate one-download scope. There is no durable research-enrollment ledger or independent adjudication source in this prototype. Therefore independently verified outcomes remain zero, research_ready is always false, and preparation downloads are not Sprint 10 training bundles. No app request trains, serves or activates a model. Full backend regression tests exercise the existing offline baselines with synthetic fixtures only.

## Completed-day review and missingness

GET /api/v1/research-quality accepts timezone_name (IANA, default UTC) and days (7-90, default 30). The window ends yesterday in the selected timezone; today is excluded. Source dates are never remapped between zones. Reports in other zones are counted separately and cannot supply observation coverage in this review. Local day ends use timezone-aware next-midnight boundaries, including 23/25-hour DST days.

A completed episode or explicit no-episode day requires a valid daily status with server status_recorded_at at or after the source day's end. A no-episode report conflicting with diary evidence or a daily status conflicting with legacy wellness evidence becomes unknown in the computed review only. Original values and history are never changed. Missing, deleted, explicitly unknown, invalid or provisional reports never become negative outcomes. The dashboard's completed reports are user statements, not independently verified onset or full-horizon labels.

Counts distinguish days with reports, missing dates, unknown/unconfirmed dates, completed episode reports, explicit completed no-episode reports, dates requiring review, reports in other zones, exportable histories and independently verified outcomes. Optional measurements remain optional; missing is distinct from zero. Optional omissions are displayed separately from invalid/incomplete records. Engineering sample-count gates belong to the existing offline experiment and are not clinically validated readiness criteria.

## Checks and auditability

Checks flag missing/unparseable timestamps, invalid daily values, invalid severity, inconsistent episode intervals, missing recovery times, duplicate source dates, contradictory daily statements, incomplete post-day confirmation and unverifiable revision histories. Legacy date-only episodes remain conflict evidence but are not verified onsets. Flags contain codes and dates, never raw notes or sensitive values in logs. Revision validation requires complete ordered creation/correction chains, ownership, availability chronology, stable source date/zone, matching current revision and matching current values, and matching revision 1 availability to the original server created_at anchor. No repair, inferred historical version or background correction occurs. Conflicts need user review in Daily status/history or Diary.

## Explicit research-preparation download

After reviewing scope, check the consent checkbox and select Download research-preparation JSON. The checkbox resets after each successful download or reload. No download happens on load or checkbox selection alone. POST /api/v1/research-export requires strict confirmed=true, scope=local_research_preparation, timezone_name and days. Extra fields, foreign owner selectors, invalid scope, missing confirmation and invalid ranges are rejected. The endpoint derives account ownership exclusively from the authenticated session, enforces CSRF/origin checks, uses no-store and limits export requests to 10 per 15 minutes (existing process-local limiter). It uploads nothing and contacts no external service. The confirmation is recorded in the downloaded receipt, not a durable server enrollment ledger.

The response recomputes quality at download time. It contains:

- export_schema: migramind-research-preparation/1, exported_at (server UTC), collection/quality policy provenance and explicit false clinical-validation/de-identification flags.
- consent: the one-download scope and server confirmation timestamp; research_enrollment=false.
- scope: requested source-date window, timezone, descriptive counts, blockers and issue codes/dates.
- daily_revisions: complete structurally valid numeric histories for nondeleted reports whose source dates and zones match the window. Each record has a fresh random export ID; account_key is a local placeholder, not a global identity. Records retain revision, action and genuine recorded_at. Values retain source date/zone, user event_at and observed_at, server status_recorded_at, status and optional sleep_hours/sleep_quality/stress/hydration_ml.
- outcome_revisions: empty. provenance_verified, outcome_history_complete and training_eligible: false.

Observation eligibility means structurally reconstructable feature history, not label eligibility. Unknown or provisional statuses and conflicting self-reports can be exported with their quality flags: they remain observations, never negative forecast labels. All corrections for a selected source date are included, even when their recorded times fall outside the requested source-date window. Deleted chains, malformed/truncated histories and duplicate-date records are excluded in their entirety. Free text, contacts, account identity, diary episodes, older wellness and early-symptom records are excluded. Zero stays zero and absent optional numeric values stay null. The existing personal account export remains unchanged for broader record access, including private deletion history.

This file is private health data: exact dates/timestamps may identify someone, and random IDs are not proof of de-identification. Store downloads privately. Account deletion erases the existing app-owned journals but cannot remove downloaded files or backups. Research retention, withdrawal, secure storage, genuine enrollment and independently reviewed onset/recovery and coverage evidence require a separately approved protocol. Do not relabel the file as a consented/training-eligible Sprint 10 bundle.

## Reproduction and limitations

From backend run ./.venv/Scripts/python -m pytest -q. From frontend run npm.cmd test -- --maxWorkers=2 (Windows PowerShell) and npm run build. Browser tests use npm run test:e2e against a private freshly migrated synthetic database. MIGRAMIND_API_PROXY can select an isolated backend for Vite; MIGRAMIND_E2E_BASE_URL can select its frontend without changing default app ports. Set the corresponding local origins in CORS_ORIGINS for isolated integration tests. Never point browser account-creation tests at a real health database.

Known limits: no independent outcome adjudication, genuine research consent/enrollment or clinical validation; no verified onset labels from daily status; no immutable history for legacy records; application-level history is not administrator-proof; SQLite was exercised, PostgreSQL was not; no background upload or research integration; large-history performance, assistive technology and real-device comfort remain unverified. Source queries use the existing session and complete account histories; concurrent changes that fail current/history validation are excluded rather than repaired. A fresh download may differ after an edit and is not an immutable research snapshot. Sprint 10's explicit frozen historical experiment policy remains unchanged.

## Validation results (2026-10-26)

Final backend: **194 passed, 0 failed, 0 skipped** in 51.59 seconds; one existing upstream Starlette/httpx deprecation warning. Coverage includes empty/missing/unknown dates, completed-day confirmation, contradictions including malformed and legacy episode intervals, strict per-download consent, CSRF/origin and account boundaries, exports, numeric zero, corrections/deletions, truncated histories, duplicate days, invalid severity, DST source midnight and timezone separation. The existing diary, readiness and offline baseline regressions remain green.

Frontend: **62 passed, 0 failed, 0 skipped**, across 12 test files. Includes explicit consent, no automatic downloads, missing/unknown/conflicting days, timezone display, empty/error states, history-preserving daily confirmation and failed exports. **Production build passed**, with no new dependencies. **Playwright: 15 passed, 0 failed, 0 skipped** in 35.7 seconds, including the new 320px keyboard review/download workflow, creation/correction histories and no changes to original records; all existing diary, Insights, account, assistance and Attack Mode browser checks passed.

Earlier validation failures were resolved: the temporary Vite proxy override initially required an unavailable Node process type; it now uses Vite's existing loadEnv API. A concurrent Vitest attempt had 2 passed tests and 11 worker-start errors; a subsequent complete run passed all 62 tests. One earlier Playwright run had 14 passes and one 30-second responsive-navigation timeout; after other test processes finished, the complete suite passed 15/15 with the same assertions and default timeout. Test assertions were not weakened. The Windows npm PowerShell wrapper ignored the initial worker-limit option; npm.cmd forwards it correctly.

Python dependency checks and git diff --check passed. Browser integration used a separately migrated synthetic SQLite database under ignored backend/.research/ and separate test ports; existing app health records were not inspected, migrated or used as fixtures. Test servers started for this sprint were stopped. No source migrations, application record corrections, new predictive models or frontend predictions were introduced. Generated databases, environments, builds, reports and screenshots are excluded from source control. Publishing requires separate review; merging is never automatic.

## Changed files

- backend/app/research_quality.py: pure quality analysis, strict export confirmation and scoped read-only endpoints; backend/app/prospective.py registers the extension using existing ownership/auth models.
- backend/tests/test_research_quality.py: synthetic isolated backend regressions.
- frontend/src/ResearchQuality.tsx and ResearchQuality.test.tsx: accessible review and explicitly confirmed local download.
- frontend/src/AIInsights.tsx: dashboard integration; frontend/src/DailyCheckin.tsx and DailyCheckin.test.tsx: explicit yesterday review through existing correction/save flows.
- frontend/e2e/research-quality.pw.ts: real isolated API/browser export/history test.
- frontend/vite.config.ts and frontend/playwright.config.mjs: optional isolated backend/base URL selection, retaining default app endpoints.
- README.md, docs/RESEARCH_DATA_QUALITY.md, docs/ML_RESEARCH_BASELINE.md and docs/PERSONALIZED_AI_FOUNDATION.md: scope, schema, missingness, consent, retention, research blockers and verification.



## Pre-publication review

The review found and fixed a missing creation-time anchor check: a journal/current pair with altered availability must not be accepted when revision 1 disagrees with the original server created_at. Inconsistent chains now receive unverifiable_revision_history and are excluded from preparation exports. This detects storage inconsistency; it does not provide protection against an administrator who rewrites all copies.

New isolated API/export regression coverage verifies that a later backdated correction preserves the original history and pre-cutoff feature values, rejects client-supplied server availability and historical export cutoffs, leaves unknown/uncovered outcomes unlabeled, and retains private tombstone history while excluding deleted chains from fresh exports. Frozen historical experiments and current preparation downloads remain distinct.

Review verification: 196 backend tests passed, 0 failed, 0 skipped (52.58 seconds; one existing upstream Starlette/httpx warning). All 62 frontend tests passed across 12 files, 0 failed, 0 skipped; production build and dependency checks passed. All 15 Playwright checks passed, 0 failed, 0 skipped (41.7 seconds), against a fresh isolated synthetic database. The 15-file publication audit found no detected secrets, databases, virtual environments, generated outputs, real health records or unrelated changes. The branch was checked against fetched origin/main without resetting work.

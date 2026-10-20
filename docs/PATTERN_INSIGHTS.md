# Personalized descriptive pattern insights — Sprint 8

This page describes the signed-in user's recorded observations. It does not diagnose, establish triggers/causes, calculate migraine risk, train a model, or recommend treatment changes. No clinical or real-user outcome validation is claimed.

## Browser workflow

Open **Insights** in the existing navigation. Choose a 30- or 90-day window and a reporting timezone. The page shows data sufficiency, recorded onset counts with observation coverage, available severity/exact-duration averages, wellness averages and eligible comparisons, possible early symptom counts and a timestamp table. Every chart has text/denominators or a keyboard-accessible table. Warm Day/Gentle Dark tokens and reduced-motion behavior are reused; insights do not alter Attack Mode or emergency access.

In **Wellness**, an optional **Whole-day episode observation** can record either an episode or no episode for a completed local date. Leave the field unknown for an unfinished day or when unsure. Creating/editing this confirmation is explicit; the server rejects confirmations before that date ends. Editing a wellness record preserves its original timezone. Older clients that omit the new field preserve an existing confirmation only when date and timezone are unchanged; moving the day/zone clears it. Clients cannot set the confirmation timestamp themselves.

## Data and API

- `GET /api/pattern-insights?timezone_name=UTC&days=30` returns `descriptive-v1`. `days` is constrained to 7–90; the UI offers 30 and 90. The reporting window includes today through the current server instant. All datetime comparisons use aware UTC instants and IANA civil-day boundaries.
- Existing cookie authentication and the session-bound `X-CSRF-Token` protect this read endpoint. Every query filters by the current account; user/owner query parameters cannot select another account. Unassigned legacy data remains inaccessible. There are no public report links or new health-data logs.
- Migration **007** adds nullable `wellness.episode_observation` (`episode`, `no_episode`, or null) and server-managed `observation_recorded_at`. Existing IDs, values, ownership and other migrations remain intact. All old rows start unknown. Account export includes the optional fields automatically; account deletion follows the existing ownership rules.
- No external analytics, dataset, new ML dependency or prediction service is used. Free-text notes, medications, legacy associated-factor text, contact details and cycle-note contents are not analyzed. Only the number of check-ins containing cycle notes is shown; cycle phase is not inferred.

## Time and missingness rules

Timed attacks, possible early symptoms, and daily wellness aggregates stay distinct:

1. An attack's exact `started_at` determines its reported onset date. Known end timestamps support durations and known overlap. Zero severity is a valid reported value, not missing. Date-only attacks have no invented midnight timestamp; unknown ends have no invented recovery or continuing headache-day count.
2. Early symptoms use their own `onset_at` and remain separate from attack symptoms. A nearest later recorded attack within **24 elapsed hours** is described as occurring after the symptom only when the symptom is strictly earlier and no known/uncertain overlapping attack prevents that interpretation. This window is an engineering description, not a validated prodromal definition. Symptoms during known attacks and uncertain overlaps receive different labels. No following recorded attack does not establish its absence.
3. Wellness dates retain their original timezone. `recorded_at` means submitted time, **not exposure onset**. Sleep/stress/hydration/screen/meals are daily retrospective observations; their order relative to an attack is unknown. They are not described as pre-attack exposures.
4. Future onsets and unavailable/future observation timestamps are excluded. Invalid/naive timestamps are flagged rather than converted silently. Exact duration averages require valid end timestamps no later than the report time.
5. Reporting days use consecutive local midnights, so DST days can be 23 or 25 hours. Daily aggregates enter comparisons only if their source-zone civil-day boundaries match the reporting-zone day exactly. Equivalent zone aliases may match; travel observations with different boundaries are excluded rather than shifted to a fabricated date.

## Comparisons and sufficiency

The comparison groups are **distinct completed days with a timed recorded onset** versus **explicitly confirmed whole days with no episode**. Multiple attacks on one day do not duplicate its wellness value. Confirmation of an episode-free date must occur after that local day ends and no later than the report time. Missing check-ins, missing fields and empty diaries never create negative observations.

Days with conflicting no-episode/attack records are excluded. Known continuing attacks exclude negative dates even when they have no new onset. Unresolved ends conservatively exclude later episode-free comparisons. Date-only attacks may exclude their surrounding dates; older date-only attacks can also block later negatives because recovery cannot be reconstructed. These exclusions are reported, not automatically repaired. A whole-day report that an episode occurred without a timed attack does not invent an onset.

Each factor requires **three available daily values per group** before comparison means are displayed. This is a small-sample display safeguard, **not a statistically/clinically validated evidence threshold**. Counts, missing-value denominators and both group means are shown; there are no causal labels, significance claims, risk percentages or medication suggestions. With fewer values, the page says **Not enough information yet**. Simple averages/counts can still describe available entries with their sample sizes; they do not establish a recurring personal pattern.

Onset counts are counts of records, not estimates of total attacks or surveillance coverage. Editable, retrospective records lack immutable availability history, and reporting intensity can bias all summaries. These features must not be used as a leakage-safe forecasting dataset; the stricter research contract in [FORECASTING_AUDIT.md](FORECASTING_AUDIT.md) remains separate and unchanged.

## Validation and remaining limits

Automated tests use synthetic fixtures only. Coverage includes empty/sparse data, unknown versus zero, explicit/unsupported comparisons, multiple onsets per day, unresolved ends, date-only records, conflicts, strict symptom/onset ordering, DST repeated hours, zone aliases/travel, invalid/future timestamps, migration preservation, CSRF/ownership, mobile tables and chart explanations. Browser account isolation is checked with temporary synthetic accounts that are deleted afterward.

Verification in this workspace: **97 backend tests and 49 frontend tests passed; 12 Playwright browser tests passed in the preceding browser verification**, along with the frontend production build. One existing upstream TestClient deprecation warning remains. Migration 007 was applied to local SQLite after a private backup; comparison against that backup verified every pre-existing column value was preserved and new observation fields remained null. Browser fixtures are synthetic; the real-API two-account check created temporary synthetic records and removed its accounts afterward. These passing tests verify implementation behavior, not clinical accuracy.

PostgreSQL execution, screen readers, real-device comfort, large-history performance and longitudinal real-user data quality remain unverified. The application is still a local prototype; existing production security limitations remain. Review missing/conflicting records with the diary if you know their timing; no completion or interpretation is inferred automatically.

To verify manually: sign in, open Insights with sparse records, then log completed-date wellness observations and timed episodes. Confirm missing days stay unknown. Compare two separate browser profiles/accounts, change reporting timezones, expand the chart/timing tables with a keyboard, and check both themes at mobile width. Do not seed clinical data or place emergency calls during testing.

## Changed files

- Backend: `backend/app/pattern_insights.py`, `backend/app/tracking_routes.py`, `backend/app/tracking_schemas.py`, `backend/app/main.py`, `backend/alembic/versions/007_pattern_observations.py`, `backend/tests/test_pattern_insights.py`.
- Frontend: `frontend/src/PatternInsights.tsx`, `frontend/src/main.tsx`, `frontend/src/TrackingForms.tsx`, `frontend/src/tracking.ts`, `frontend/src/style.css`.
- Frontend tests: `frontend/src/PatternInsights.test.tsx`, `frontend/test-fixtures/patterns.ts`, `frontend/e2e/patterns.pw.ts`, `frontend/e2e/authentication.pw.ts`.
- Documentation: `README.md`, `docs/PATTERN_INSIGHTS.md`.

## Final review

Missing severity stays null in form serialization, API schemas and storage, and is excluded from the severity average denominator. A reported zero remains a valid rating. Regression tests cover all-missing, zero-only and mixed ratings, including rendering.

Reporting-window regression tests cover 30 and 90 civil dates in UTC, Asia/Kolkata and America/New_York. The first local midnight and current report instant are included; instants immediately outside are excluded. Today remains incomplete and cannot create a whole-day negative observation. DST boundary and missing-data cases remain covered separately.

Final checks use isolated synthetic fixtures and a fresh ignored test directory; they do not modify existing user data. The existing BroadcastChannel startup fix and its unit/browser regression are included; see [rendering investigation](FRONTEND_RENDERING.md). No secrets, local databases, research outputs or generated build/test files belong in the commit. One upstream TestClient deprecation warning remains.

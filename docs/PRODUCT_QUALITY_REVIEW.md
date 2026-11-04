# Sprint 16: product quality and demonstration experience

Review date: 2026-10-29. Branch: `feat/product-quality-demo`, starting from merged Sprint 15 (`88cf786`). No hosted deployment, recruitment or real health-data collection is authorized or performed. The user separately authorized committing the reviewed Sprint 16 files, pushing the feature branch and opening a PR only after final checks pass; merge and deployment remain unauthorized. All test records are fictional. Backend behavior, migrations and research eligibility policies are unchanged.

## Subsequent portfolio review

The [2026-11-04 readiness review](PORTFOLIO_READINESS.md) records current checks and closes the saved-record read-only affordances left open here. This document retains the historical Sprint 16 evidence and walkthrough; use the new timed instructions for presentation.

## Review scope and findings

| Journey | Finding and response |
| --- | --- |
| Landing/onboarding/authentication | The existing sign-in gate preserves privacy, fixed demo identity and the synthetic warning. Retry could retain stale errors and an enabled form while reconnecting; reconnect now clears prior errors and shows the existing connecting state. No account or enrollment invitation is added. |
| Navigation/dashboard | Keyboard users had to traverse all navigation controls; add a visible-on-focus skip link and programmatically focus the page heading after a page change. Initial render does not steal focus, including React Strict Mode. Existing active-page semantics remain. The overview prompt now opens daily status rather than unexpectedly opening an episode form. |
| Demo diary/calendar | Current-month views hide fixed January fixtures, and add/edit controls invite unsuccessful writes. A collapsible, repeatable tour explains the fixture period and links to its calendar date in the device timezone. Modal add/edit and delete entry actions explain read-only mode before opening a form or confirmation. Empty diary copy explicitly preserves missingness. |
| Diary forms/history | Existing labelled fields, revision views and tombstones remain. Opening a modal clears stale errors; retry marks loading again. Dialog tab cycling excludes hidden and disabled controls and includes summaries. Closing or Escape is blocked during an in-flight save to avoid concealing its result. Existing attack-mode focus/return behavior is retained. |
| Insights/wellness/early symptoms | Descriptive summaries, optional observations, timestamp semantics and unknown-day distinctions remain unchanged. The tour explicitly separates associations from causes and insights from prediction. Wellness and daily migraine status remain distinct collections; no retrospective verification is invented. |
| Trusted contacts/caregiver/SOS | Existing user-initiated dialer/SMS, saved support card and dim attack mode remain. No automatic dispatch, sharing or external requests are added. The tour warns presenters not to activate real call/SMS links. The small fixture has no contact list; empty support states are part of the demo. |
| Research quality/consent/export | Tour explains where research quality lives on Overview and that review and export require separate actions. Existing explicit consent, account isolation and synthetic export labels are retained. Current-window missingness and zero independently verified outcomes are honest results, not broken demo states. |
| Settings/logout | Warm/dark preferences and attack-mode return behavior remain. Existing logout waits for its anonymous CSRF replacement. No demo reset or mutation control is added to the browser. Appearance changes stay local to the device. |

## Implementation and accessibility

The new `DemoGuide` is a labelled section with native disclosure and explicit navigation buttons. It does not advance automatically, persist a tracking identifier, call a service or upload information. It identifies fictional January 2026 examples, read-only operation, unknown outcomes and research limits. Navigation buttons wrap at narrow widths and meet a 44px minimum height; the existing semantic color tokens and visual identity are reused.

The skip target is programmatically focusable; page changes move focus to the heading, and visible focus uses the current palette. The tour is absent in Attack Mode to keep that view quiet. Existing reduced-motion, large-text and dim palettes remain. Browser regressions check 320px, 768px and 1280px, keyboard skip/heading behavior, accessible control names, and text/surface, muted-text/surface and primary-button token contrast in warm/dark themes. These checks cover selected properties, not all rendered contrast, screen-reader combinations, zoom modes, cognition or every disabled/error state. No WCAG compliance claim is made. Human screen-reader, zoom and task-based usability review remain required. No accessibility dependency is added.

## Validation evidence

| Final verification | Result |
| --- | --- |
| Backend | 249 passed, 0 failed, 0 skipped; 96.35s; one existing Starlette/httpx deprecation warning |
| Frontend | 72 passed across 13 files, 0 failed, 0 skipped; 10.69s; includes final reconnect-feedback regression |
| Existing + product Playwright | 21 passed, 0 failed, 0 skipped; 44.6s; final rerun used `--timeout=120000` with unchanged assertions and application limits |
| Built synthetic demo | 2 passed, 0 failed, 0 skipped; 3.9s; actual fixture calendar, private history, research review, consented UI download, mode mismatch, no uploads/writes and UI logout |
| Production builds | Final editable and synthetic TypeScript/Vite builds passed (8.18s / 3.35s Vite stages) |
| Dependencies | npm: 0 known advisories; OSV: 43 packages, 0 known advisories/skips; pip compatibility passed; no dependencies changed |
| Preservation and scope | Existing database and historical migration checksums unchanged; no backend or migration diff; no credentials, database or generated artifacts included |

Commands run from `backend` or `frontend` as applicable:

- Backend: `.venv/Scripts/python -m pytest -q`.
- Frontend: `npm test -- --run`.
- Existing plus new browser checks: `npm run test:e2e -- --timeout=120000`, using an isolated editable synthetic database.
- Built demo: `npm run test:demo`, against a separately provisioned synthetic database and final Vite preview on loopback.
- Production builds: `npm run build` with explicit `VITE_DATA_MODE=local` and `synthetic`, same-origin API.
- Dependencies: `pip check`, isolated `pip-audit` against OSV, and `npm audit`.
- Preservation: compare existing database/historical migration checksums; inspect diff for unintended files, credentials, databases and generated output.

Earlier implementation verification: an initial restricted frontend invocation could not resolve Vite configuration because esbuild lacked ancestor-directory access; it was rerun with the normal approved worker permissions. One intermediate unit run caught a dialog-selector regression (70 passed, one failed); the corrected selector passed all 71 frontend tests. A browser run during competing build/backend workload passed 17/18 and timed out during account-cleanup at 60 seconds. A fresh-target rerun without competing work passed all 18; its account workflow took 13.7 seconds. No rate limit or assertion was weakened. A malformed initial product-test mock was corrected to return an unavailable insights value rather than an invalid array. Screenshot inspection also caught an empty-state replacement that had not matched a typographic apostrophe; the final source uses explicit missingness wording. These intermediate outcomes are not presented as final passing checks. Mobile and desktop synthetic screenshots were inspected for layout and readable wrapping; screenshots remain ignored local artifacts, not source files.

## Five-minute technical demo

Prerequisite: follow the [operations runbook](OPERATIONS_RUNBOOK.md) to create a new dedicated empty synthetic target, migrate and provision it, then build with `VITE_DATA_MODE=synthetic`. Use a private fictional demo password. Never reuse a personal/research database. No hosted infrastructure or operational readiness is implied.

1. **0:00-0:40 - Sign in and scope.** Show the synthetic/read-only banner and reserved demo identity. State that this is a software prototype with no clinical prediction or permission for real health records.
2. **0:40-1:30 - Daily status and history.** Use the guide to open Daily status. Show the three January examples: migraine, explicit no migraine, unknown. Open record history and point out creation time versus backdated event time. Do not type health information or save anything.
3. **1:30-2:10 - Calendar and diary.** Choose Show example calendar. Show the fictional episode in the device timezone; note that other blank dates do not mean no migraine. Demonstrate that an add/edit action explains read-only mode without opening an entry form.
4. **2:10-3:20 - Research honesty.** Choose Review research features. Show AI Insights' insufficient-evidence state. Open Research data quality and explicitly request a review. Explain the last-30-completed-days window: old fixtures need not appear there. Missing days and zero verified outcomes prevent claims of forecasting readiness.
5. **3:20-4:10 - Consent and export.** Inspect the separate download confirmation; leave it unchecked to show that export is unavailable without consent. If demonstrating a download, explicitly consent and review only the synthetic flag/schema locally. Do not upload it. Export is neither clinically validated nor automatically de-identified.
6. **4:10-5:00 - Accessibility, support and exit.** Show keyboard navigation and the warm/dark preference. Briefly enter and exit Attack Mode without activating call/SMS links or starting a writable session. Explain empty contact states and user-initiated sharing. Sign out through Account and show that authenticated content is gated again.

## Reset and remaining limitations

Reproduce/reset by stopping the local demonstration and using a new empty versioned target with the existing provisioner. It refuses nonempty databases; there is no destructive browser reset. Keep old targets under the reviewed retention procedure. See [architecture](DEPLOYMENT_ARCHITECTURE.md), [readiness](DEPLOYMENT_READINESS.md) and [research gate](RESEARCH_READINESS_GATE.md).

The guide depends on the current `synthetic-demo/v1` January fixture; revisit its date shortcut when that version changes. Some embedded health/account/support forms can still be inspected and may accept typing, but existing frontend and backend guards reject mutation; the warning says not to enter real information. No claim is made that arbitrary malicious input can be classified as synthetic. The demonstration is not a complete study enrollment or accessibility certification. Host ownership, independent security/privacy review, PostgreSQL/TLS/roles, encrypted backup/restore, research approvals and clinical validation remain unresolved. Synthetic software results are not evidence of clinical effectiveness.

## Changed files and handoff

- `frontend/src/DemoGuide.tsx`: native, collapsible guide and explicit navigation actions.
- `frontend/src/main.tsx`: demo-aware entry actions, fixture calendar shortcut, skip/heading focus, daily-status prompt, retry/error and dialog behavior, missingness copy.
- `frontend/src/Authentication.tsx`: pass the attested demo mode to the workspace and reset reconnect feedback.
- `frontend/src/style.css`: semantic-palette guide, responsive buttons and keyboard focus/skip-link styles.
- `frontend/src/DemoGuide.test.tsx`: two guide unit regressions.
- `frontend/src/Authentication.test.tsx`: deferred reconnect regression proving stale feedback clears and the form waits for the replacement session.
- `frontend/e2e/product-quality.pw.ts`: responsive, keyboard, accessible-name, palette contrast, missingness, no-upload and UTC boundary browser checks; ignored synthetic screenshots.
- `frontend/deployment-e2e/demo.pw.ts`: actual built-fixture calendar/tour checks alongside existing consent and backend restrictions.
- `README.md` and this document: review entry point, evidence, scope and walkthrough.

No backend source, schema, fixture definition, migration, dependency or lockfile changed. Ten intended files are eligible for the explicitly authorized source-only commit and review PR after passing checks. No actual records, credentials, databases, generated screenshots, datasets or environments are in the source diff. Local test servers are stopped after verification. There is no merge or hosted deployment. The source-only commit, feature-branch push and PR are separately authorized by the final-review request.

## Final independent review and publication evidence

All requested software checks passed. The final review added coverage without changing runtime behavior, backend policies, fixture definitions, dependency locks or migrations:

- Calendar boundary tests run in `Etc/GMT+12`, `UTC` and `Pacific/Kiritimati`: the fixed 2026-01-02 10:00 UTC onset appears on January 1, 2 and 3 respectively. Each test verifies both selected date and visible episode, not merely the month label. Daily status still retains its own originally reported local date; no stored timestamps are rewritten.
- The actual built-demo flow now covers sign-in, fixture calendar, unknown-day private revision history, insufficient forecasting evidence, explicitly requested research-quality review, disabled download without consent, consented local JSON download, backend write rejection, record preservation and UI sign-out.
- The reconnect regression defers the replacement session response: the previous error clears, connecting status appears and sign-in stays unavailable until the response arrives. An initial build caught the new test using Playwright's `exact` option with Testing Library; this was corrected and both builds rerun successfully.
- Existing backend tests inventory every mutation route and an unknown administrative path, deny demo writes before body consumption, verify consent/account isolation/CSRF/session behavior, and compare application records across allowed demo reads/exports/login/logout. Existing frontend/browser tests cover dialog focus return, attack mode, diary/history, wellness timestamps, consent, exports and account isolation.
- Diff checks verify the latest main is the branch base, existing database/historical migrations are unchanged, every intended file is UTF-8 text, local documentation links resolve, and no database, virtual environment, health record, actual credential or generated artifact is included. Synthetic passwords and reserved test addresses are fictional fixtures.

These are software-verification passes, not clinical, research-approval or hosted-operational readiness decisions. The remaining limitations above still apply. No new runtime defect was confirmed during this final review; the changes made here strengthen verification and correct the test-only build error.

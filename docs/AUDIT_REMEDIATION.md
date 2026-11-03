# Sprint 18: final audit remediation

Branch: `audit/final-project-review`. Implementation verification: 2026-10-30; independent final review: 2026-11-03. The [independent audit](FINAL_PROJECT_AUDIT.md) was read in full before implementation. Findings were checked against source and regression behavior rather than treated as instructions to expand scope. This change fixes F02, F04, F05, F06 and F07; it adds no product feature, predictive model, collection pathway or deployment. Other findings remain explicitly bounded or deferred below.

## Legacy snapshot pipeline: exact mechanism and correction

Previously, `chronological_split` calculated 60/20/20 boundaries from the number of retained rows. Retention depends on outcome coverage/availability, so a later exclusion could move an earlier train/validation boundary. Purging afterward did not repair that selection dependence: the audit's 240-candidate example changed earlier training from 142 to 141 rows after removing a final retained row.

[dataset.py](../backend/research/dataset.py) now requires explicit `grid_start`/`grid_end`. It computes split times from the declared candidate grid before filtering, rejects duplicate/off-grid/out-of-range examples, and purges horizon and label availability against the fixed boundaries even when validation or test becomes empty. [experiment.py](../backend/research/experiment.py) passes the CLI experiment range and reports the fixed-grid policy and purged count. Missing boundaries raise an error rather than silently recovering the old behavior.

A second source-level problem was confirmed during remediation: a longer coverage interval confirmed much later could sort before earlier coverage and change which confirmation determined maturity. Coverage is now restricted to evidence confirmed by horizon end plus the existing 24-hour lag. The first available snapshot at or after that maturity supplies the label and its actual availability; split purging still uses that snapshot's availability. Late coverage cannot displace earlier evidence. This remains a snapshot contract, not the independently reviewed revision/outcome contract required by the current v2 baseline.

The legacy policy is versioned `migraine-onset-24h/v1.1`. No historical report is rewritten. The revision-aware files `revision_contract.py`, `revision_dataset.py`, `baseline_v2.py`, `baseline_cli.py`, their fixture and existing tests are unchanged. No provenance, class-count, coverage or training gate is relaxed. V2.1 remains the current research reference.

### Reproducibility and metric impact

Before editing, explicitly constructed synthetic-only reports were captured outside Git. After editing:

- The existing 210-window simulated legacy-contract fixture still produces train/validation/test counts of **124/40/42**, and all reported model metrics match the before-change report exactly. Only legacy policy/report metadata changes on that fixture.
- The exclusion counterexample now retains the same **142** earlier training rows after a future exclusion, and the same validation membership. This is a software regression result, not a forecasting metric.
- The full deterministic v2 synthetic report, derived-dataset hash and all model metrics match both the captured before-change report and an independent repeated fit exactly. A CLI `research_source_sha256` covering every research Python file will intentionally change when legacy source changes; this does not mean the v2 dataset/model behavior changed.
- Real-world metrics were not computed. Other historical legacy experiments with exclusions or late coverage may change their rows and metrics and must be rerun as a new versioned experiment, not compared as if the cohort were identical.

[Backend regressions](../backend/tests/test_audit_remediation.py) test future exclusions, absent later partitions, late coverage, future test labels/features/availability, training coefficients, validation probabilities and validation-only threshold stability. Existing pre-cutoff, freeze, coverage, consent and deterministic v2 tests remain green.

## Episode input and historical preservation

[EpisodeIn](../backend/app/tracking_schemas.py) is the shared Pydantic input model for POST and PUT. Its interval helper is also used by [research quality](../backend/app/research_quality.py). New submissions/corrections require:

- Offset-aware exact instants and an IANA zone for timed entries; exact onset cannot be future, and a supplied end must be strictly later than onset and not future.
- An explicitly supplied date must agree with onset in the recorded zone. An explicitly supplied duration must agree with the rounded exact interval and remain within the supported bound. Integer severity/duration reject Boolean/fractional coercion.
- A date-only entry cannot have an exact end. Future date-only submissions are rejected using the supplied zone, or UTC when no historical zone is supplied. No missing historical zone is written or guessed.
- Medication observations cannot be future. They are not required to fall inside the attack: no unsupported clinical relationship is assumed.

[Frontend serialization](../frontend/src/tracking.ts) checks invalid/future intervals before upload. The [form](../frontend/src/TrackingForms.tsx) disables manual duration when an exact end is supplied; it sends no contradictory date/duration for timed entries, letting the server derive those values explicitly. Positive sub-minute intervals may round to zero minutes; equal endpoints are invalid. Zero severity and unknown ends/durations remain valid.

The independent final review also found that a date-only frontend edit discarded an existing timezone and checked against UTC. Serialization now preserves an existing zone and validates the date in it, while keeping absent historical zones null. A regression checks both sides of UTC midnight and preservation without inventing a zone.

Existing database rows are not normalized, migrated or rewritten. Historical invalid rows remain readable/exportable; invalid attempted updates return 422 and leave the stored row intact. A user must explicitly correct an invalid row before saving it. ORM/administrator-level storage is still a separate trust boundary (F11/F15); this sprint does not claim database-enforced chronology for arbitrary direct SQL.

The DST browser fixture now fixes its test clock after the November fold-hour event, so the existing precision-preservation check tests a historical event rather than accidentally testing a future submission. Its timestamp assertions are unchanged.

## Trusted and emergency dialing

[Server syntax validation](../backend/app/phone.py) and [browser helpers](../frontend/src/assistance.ts) require ASCII digits, optional leading `+`, and valid spaces/hyphens/balanced non-nested parentheses containing digits. They reject empty/punctuation-only values, interior plus signs, URI schemes, query/control syntax, alphabetic/Unicode-digit substitutions and malformed parentheses. Existing 32-character storage/form limits remain. No country code, E.164 length, carrier, extension convention or reachability is inferred. Short/local numbers are not rejected merely for failing an international format.

POST and PUT contacts share the validator. Stored display values are not silently reformatted. Trusted-contact cards expose no call link for invalid historical values; Attack Mode filters unusable destinations; SOS suppresses invalid call/SMS links. The emergency setting retains its existing short-digit policy and falls back to the existing India `112` default if its saved value is malformed. Emergency access remains independent of forecasting. No dialer, SMS, emergency call or location acquisition was activated during verification. Real-device handoff/reachability remain unverified.

## Partial failures and retries

The old [workspace refresh](../frontend/src/main.tsx) used one rejecting `Promise.all` and applied none of seven results unless all succeeded. An insights failure could suppress healthy contacts/profile data; its shared error also disabled support presentation. A successful save followed by a failed refresh could appear like a failure of the whole operation.

Each read now applies its successful result independently. Resource-specific failures remain visible with read-only retry actions. Contacts/profile have their own completion/error boundary for Attack Mode, so pending/failed analytics or wellness cannot hide loaded support data. An unavailable profile cannot be blindly overwritten through its form. Failed insights become explicitly unavailable rather than leaving an apparently fresh old summary. A refresh generation discards older retry results. Retry performs GETs; it does not replay a prior create/update.

[Frontend regressions](../frontend/src/AuditRemediation.test.tsx) cover an unrelated insights failure and recovery, usable support while insights remains pending, profile failure with disabled writes and successful recovery, and a saved episode remaining visible after analytics failure with exactly one POST across retries. The change stays within the existing App/component structure; it does not introduce a new state framework or networking service. Broader cancellation, pagination and scale work remain deferred.

## Vite and dependency verification

The installed/locked Vite version was independently confirmed as `6.4.4`. The [maintainer advisory GHSA-8g5g-mxqh-grgj](https://github.com/vitejs/vite/security/advisories/GHSA-8g5g-mxqh-grgj) identifies that exact version as affected and `6.4.5` as patched. This concerns development-server file-deny behavior under its stated exposure/file conditions, not the static production bundle.

[package.json](../frontend/package.json) now pins compatible Vite `6.4.5`; [the lockfile](../frontend/package-lock.json) changes only the root Vite declaration and its resolved package/version/integrity. `npm ls --depth=0` reports a compatible installed tree. Fresh npm audit reports zero known advisories. A temporary isolated `pip-audit` installation scanned the ML lock against OSV: **38 packages, zero known advisories, zero skips**. All **31 base / 38 ML pins** match the installed project environment and `pip check` passes. The scanner's pinned/no-dependency mode warns that the locks lack distribution hashes; exact version pins do not establish supply-chain or host security.

These are dated advisory and compatibility checks, not proof that all security risks are resolved. No project Python dependencies were added or changed. Host/runtime patching, independent security review and operational controls remain open.

## Final verification

| Check | Final result |
| --- | --- |
| Backend suite | **254 passed**, 0 failed/skipped; existing Starlette/httpx deprecation warning |
| Frontend suite | **79 passed across 14 files**, 0 failed/skipped; one worker |
| Full Playwright suite | **21 passed**, assertions and application limits retained |
| Built synthetic demo | **2 passed** against real dedicated fixture/API |
| Production builds | Editable/local and synthetic TypeScript/Vite builds passed |
| ML | Leakage/late-coverage/training/validation regressions passed; synthetic before/after and repeated v2 comparison passed as described above |
| Dependencies | npm audit 0 known advisories; OSV Python scan 38 packages/0 advisories/0 skips; npm tree/pip compatibility and installed pins passed |
| Preservation | All 11 pre-existing local-database/migration-file SHA-256 values match the pre-change manifest; no migrations changed or new migration introduced |
| Documentation/diff | 364 local links and 67 source/document line references resolve within file bounds; all 18 finding dispositions present; UTF-8, Python syntax, tables/fences, whitespace, credential-pattern and Git diff checks passed |

Backend commands ran with explicit `APP_ENV=development`, `DATA_MODE=local` and `DATABASE_URL=sqlite://`; pytest fixtures use isolated memory/temporary databases. Browser verification used newly migrated temporary editable and dedicated synthetic SQLite targets, separate loopback ports, and matching frontend modes. Both build outputs, reports, helper scripts, scanner environment and databases stayed outside source control; existing ignored browser screenshots/results remain ignored. Helpers stopped their servers. Existing database bytes were hashed for preservation without querying or displaying records, and that database was never migrated or used by tests.

During implementation, TypeScript caught an unclosed fieldset and test-only misuse of Testing Library's `exact` option; both were corrected. A targeted run passed 19/20 frontend cases and caught an unnecessarily changed empty-contact message; the original empty state was restored with a separate message for invalid historical contacts. Final full frontend/build/browser runs passed afterward. No assertion was relaxed. The first targeted backend run passed 116 tests; final 254-test results include the additional late-coverage regression. These earlier runs are not substituted for final results.

Independent final-review reruns on 2026-11-03 confirmed the results above after the date-only timezone correction. The first frontend startup was blocked by sandbox ancestor-directory access; normal-access runs passed. An initial browser run passed 19/21 while frontend files were edited and Vite reloaded; it is not counted as a pass. The source-stable full rerun and demo/build results are the final results above. The temporary ML comparison wrapper initially had an indentation error; its corrected run compared actual reports successfully. These execution failures did not lead to relaxed assertions.

## Changed-file inventory

The reviewed source scope is 22 text files, including both new audit documents. Publication includes only this inventory.

| Area | Files |
| --- | --- |
| Backend validation/phone | `backend/app/main.py`, `backend/app/tracking_schemas.py`, `backend/app/research_quality.py`, new `backend/app/phone.py` |
| Legacy ML and regressions | `backend/research/dataset.py`, `backend/research/experiment.py`, `backend/tests/test_research.py`, new `backend/tests/test_audit_remediation.py` |
| Frontend behavior | `frontend/src/main.tsx`, `frontend/src/tracking.ts`, `frontend/src/TrackingForms.tsx`, `frontend/src/assistance.ts`, `frontend/src/AttackMode.tsx`, `frontend/src/SOSMessage.tsx` |
| Frontend tests/dependency | New `frontend/src/AuditRemediation.test.tsx`, `frontend/e2e/tracking.pw.ts`, `frontend/package.json`, `frontend/package-lock.json` |
| Documentation | `docs/FINAL_PROJECT_AUDIT.md`, new `docs/AUDIT_REMEDIATION.md`, `docs/ML_EXPERIMENTS.md`, `docs/FORECASTING_AUDIT.md` |

## All 18 findings: independently reviewed disposition

| Finding | Status | Verification / rationale |
| --- | --- | --- |
| F01: real forecasting evidence | **Deferred / research blocked** | Forecast probability remains null; adapter/export still cannot manufacture verified outcomes. No approved study or eligible real bundle is supplied. Solving this requires separately authorized institutional/data work, not portfolio code. |
| F02: legacy future-dependent split | **Resolved for confirmed mechanism** | Fixed candidate grid, actual label-availability purging and coverage-confirmation freeze; new regression suite. Legacy evidence/provenance limitations remain, and v2 remains the reference. |
| F03: hosted controls | **Deferred / hosted and real-data gates closed** | Production synthetic-only config and templates remain; PostgreSQL/TLS/grants/Linux/encrypted recovery require a real staging/operations effort not authorized here. |
| F04: Vite advisory | **Resolved for specified advisory** | Maintainer range verified; installed/locked 6.4.5, compatible dependency tree, builds and fresh npm audit passed. This does not clear unrelated security risks. |
| F05: episode chronology | **Resolved for API/model/form policy** | Shared input/review interval policy, consistent create/update rejection and browser checks; historical values preserved. No claim of administrator-proof storage. |
| F06: malformed dialing | **Resolved for syntax/link safety** | Server/form syntax checks and all trusted call/SMS guard paths; valid short/local formats preserved. Reachability/device interoperability are not validated. |
| F07: partial refresh coupling | **Resolved for confirmed operations** | Healthy resources apply independently; support has a separate loading/error boundary; blind profile writes blocked; retry and no-duplicate-write regressions passed. |
| F08: read-only form affordances | **Deferred** | Client/backend mutation guards and built-demo tests remain effective. Some embedded forms still allow typing before explaining rejection. It is a bounded demo polish issue, not an additional high-severity blocker; no real-input solicitation or new workflow added. |
| F09: shared login availability | **Deferred for any unattended hosting** | Existing per-account/process limiter remains unchanged. Single guided localhost demo is the supported scope; do not weaken authentication throttling without a separately designed abuse/availability policy. |
| F10: large histories | **Deferred** | Full-history scans remain. No scale claim or performance threshold is invented; targeted query/pagination work requires representative synthetic profiling beyond this defect-remediation scope. |
| F11: maintainability/storage invariants | **Deferred** | Application ownership checks and daily CAS/uniqueness remain tested. Broader module reorganization/DB constraints require separate review; no schema or unrelated refactor was introduced. |
| F12: CI/self-isolating test harness | **Partially addressed** | Meaningful regressions and isolated complete verification were added/run. The helper/scanner remain temporary; no checked-in CI/lifecycle guarantee is claimed. CI is worthwhile follow-up, not a fabricated completed control. |
| F13: manual accessibility/devices | **Deferred** | Existing responsive/keyboard/browser checks passed; human screen-reader, zoom, alternate-browser and real-device comfort/handoff evidence remains absent. No accessibility certification claimed. |
| F14: README archival structure | **Deferred** | Existing current intro/limitations remain factual. Only the two legacy methodology guides were corrected for changed policy. A broad README archive rewrite is not necessary to fix these confirmed blockers. |
| F15: governance/history/privacy | **Deferred / real-data blocked** | No enrollment/adjudication ledger, administrator-proof history or backup/download erasure was added. Existing journals, consent flags, export limits and account isolation remain. |
| F16: statistical sufficiency/novelty | **Deferred / research claims blocked** | Engineering gates, fixed baselines and false clinical-validation flags remain. Power, uncertainty, real outcomes and external validation require a separately approved study. |
| F17: personal attribution | **Awaiting presenter confirmation** | Existing interview wording remains conditional. No sole authorship, AI-generated percentage or personal contribution was inferred. This is a claims boundary, not a code defect this sprint can resolve. |
| F18: report overwrite | **Deferred** | Existing CLI can overwrite an explicitly selected output directory. This sprint used separate private before/after files; versioned output/refusal policy remains a documented low-severity archival improvement. |

No additional high-severity **bounded portfolio/local-demo** blocker was confirmed after reviewing all findings. Remaining high findings concern real research, hosted operation or unsupported personal/clinical claims and remain blocked rather than being declared fixed. No clinical prediction, data acquisition, deployment or merge is included. Commit, push and a PR targeting `main` are the separately authorized final-review publication steps.

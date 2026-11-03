# MigraMind independent final project audit

Audit date: 2026-10-30. Reviewed checkout: `main`, commit `c695037cc29f2495a459db9fce5373c96047c7ee`. This audit independently inspected source, configuration, migrations, tests and documentation and ran fresh checks. Earlier sprint results were treated as historical claims, not accepted as current passes. That original audit added only this document. Sprint 18 remediation on `audit/final-project-review` is recorded below and in [AUDIT_REMEDIATION.md](AUDIT_REMEDIATION.md); the original findings, scores and test evidence remain historical rather than being silently re-scored. Original line references describe the reviewed commit; current changes and regression sources are linked in the remediation record.

## Original release decision

**Ready for a bounded technical interview, engineering/research-methods presentation and source-code portfolio. Not ready for real-world research, clinical forecasting or an unreviewed public hosted service.** Present it as a tracking/support prototype with an offline evaluation foundation, not as a demonstrated migraine predictor. A research-results presentation claiming predictive benefit or algorithmic novelty is not supported.

The strongest evidence is functioning account-isolated workflows, explicit missingness, daily revision history, conservative v2 historical evaluation and a guarded synthetic demonstration. The weakest areas are absence of eligible real outcomes and approved collection operations, a still-runnable weaker legacy ML path, operational security verification, maintenance automation and some confirmed input-validation defects. No Critical defect was confirmed within this audit's scope; that is not a penetration-test certificate.

Public source presentation can proceed with the limitations visible. Fix the current Vite advisory before offering developer-server access, retire the legacy training ambiguity before inviting research replication, and resolve personal-attribution wording before claiming independent implementation. Keep real-data and hosted-readiness gates closed. A localhost guided synthetic demo is a different release boundary from an internet service.

## Assessment scale

Scores are coarse reviewer judgments, not measured percentages or clinical readiness probabilities: **1** = evidence/approval largely absent; **2** = partial implementation with major blockers; **3** = demonstrable prototype with material gaps; **4** = consistently verified within a clearly limited scope; **5** = independently assessed, mature evidence and operations for the stated intended use. There is no weighted total: good UI cannot compensate for absent research evidence.

| Area | Score | Evidence and interpretation |
| --- | --- | --- |
| Product quality | 3/5 | Diary, accounts, status/history, export and support flows have fresh API/browser evidence. Input validation, failure coupling and visible read-only mutation controls remain problems (F05-F09). |
| Engineering | 3/5 | 249 backend tests, 72 frontend tests and 23 browser checks passed in the final runs; migrations and isolation receive meaningful tests. Compressed orchestration, unbounded reads, weak storage-level invariants and absent checked-in CI/test lifecycle automation limit maintainability (F10-F12). |
| ML credibility | 3/5 | V2 temporal rules, fixed baselines and metric implementations are defensible software; independent metric comparisons agreed. Synthetic performance is correctly disclaimed. The legacy splitter still permits future-dependent partition changes and no real predictive effectiveness is established (F01-F02, F16). This is not a forecasting-accuracy score. |
| Research readiness | 1/5 | A protocol/access plan exists, but an approved institutional team, research enrollment, usable independent outcome journal and eligible real cohort are absent from the implementation/evidence. The strict forecasting study remains NO-GO (F01, F15-F17). |
| Security and privacy | 3/5 for prototype safeguards | Owner isolation, cookie/CSRF controls, redaction and demo ingestion guards have fresh regression evidence. A current moderate development dependency advisory, unverified hosted controls and missing real-data lifecycle assurance prevent a production-security conclusion (F03-F04, F10, F15). |
| Portfolio presentation | 3/5 | Architecture, research presentation, interview guide and source matrix are useful and linked. The README mixes setup with a long historical sprint log; clean installation/CI and verified personal contribution evidence need attention (F12, F14, F17). |

## Independent verification and limits

The tracked inventory contains 155 files and approximately 10,310 Python/TypeScript/TSX/CSS/Markdown lines before this addition. Review concentrated on every application/research module's responsibility and trust boundary, migrations/configuration, UI orchestration and tests exercising those paths. This was a repository audit, not an assertion that every line received formal proof or exhaustive fuzzing.

| Fresh check | Result and scope |
| --- | --- |
| Backend | `python -m pytest -q` from `backend`: **249 passed**, one Starlette/httpx deprecation warning. Explicit development settings and `DATABASE_URL=sqlite://`; tests use isolated memory/temporary databases. No skips reported. |
| Frontend | `npm.cmd test -- --maxWorkers=1`: **72 passed across 13 files**. A restricted startup failed on esbuild ancestor-directory access. The next normal-access two-worker run passed 51 tests but failed two worker startups; neither incomplete run is counted as a pass. The sequential rerun passed without changing assertions. |
| Editable browser integration | Existing Playwright suite: **21 passed**, against a freshly migrated temporary SQLite target and separate loopback API/Vite ports; not an existing application database. Includes real account/API flows and separately mocked UI scenarios. |
| Built synthetic demonstration | TypeScript check and synthetic Vite production build passed. Dedicated empty-target migration/provisioning passed; built-demo Playwright suite: **2 passed**. Checks include backend-mode mismatch, real fixture/history, explicit export consent, rejected mutations, record preservation and logout. |
| Intermediate build wrapper failure | The first synthetic build itself passed; its temporary wrapper then failed printing a Unicode log character. The wrapper output encoding was corrected outside the repository, and the synthetic-only follow-up completed successfully. |
| Independent targeted probes | Isolated API requests reproduced F05/F06. A constructed legacy split reproduced F02. A fresh limiter instance reproduced F09. Thirty deterministic binary/tied-score cases matched scikit-learn ROC-AUC, average precision, Brier and trapezoidal precision-recall area. These are software checks, not patient/model-effectiveness metrics. |
| Dependency checks | `pip check`: no broken requirements. Fresh `npm audit --json`: **one moderate advisory, zero high/critical**, discussed in F04. Python vulnerability advisories were not freshly scanned: `pip-audit` is not installed. Package compatibility is not vulnerability clearance. |
| Presentation/static checks | All 54 tracked Python files parsed. The existing 260 local documentation links resolve. Architecture Mermaid was rendered and visually inspected during final audit verification. Fresh 320px/1280px screenshots generated by mocked product tests were inspected; these verify those UI states, not all real-data layouts. |
| Data and change scope | Tracked inventory contains no database, spreadsheet/CSV, model, image or private-key artifacts in the inspected extensions. Templates/tests contain fictional values. No private application database or patient workbook was opened. Final source scope is this Markdown file only. |

Browser/build helper scripts, test databases, logs, generated bundles and diagram previews stayed in operating-system temporary or already ignored test-output directories. Test servers started for this audit were stopped by the helper. No calls/SMS, location acquisition, real-data collection, recruitment, model deployment or Git publication actions were performed.

Not verified: fresh dependency installation from an empty machine; Python advisory status; PostgreSQL execution and contention; Linux/nginx/systemd operation; internet TLS/firewalls/role grants; encrypted off-host recovery; sustained load; real-device calling/SMS/share behavior; Safari/Firefox; screen readers, 200-400% zoom and task-based migraine-time comfort. No empirical check of personal authorship or historical workbook row counts was possible from code alone. No systematic prior-art review or clinical validation was conducted.

Final document verification passed: 327 local links across README and documentation, including 67 source/document line references within file bounds; all 18 findings contain severity, evidence, impact, fix and release-boundary fields. UTF-8, table/fence structure, whitespace, credential-pattern and diff checks passed. Git scope confirms only `docs/FINAL_PROJECT_AUDIT.md` is added, with no tracked modifications or staged changes.

## Findings

Severity describes consequence within the stated boundary. “Research” below means real-data collection/evaluation or clinical claims, not permission to discuss a synthetic methods prototype. A finding that blocks research need not block public source presentation.

### F01 — No eligible real forecasting evidence or approved study implementation

**Sprint 18 status:** Deferred: real research remains blocked; no eligible real outcomes, enrollment or clinical validation supplied. See [remediation and regression evidence](AUDIT_REMEDIATION.md).

**Severity: High.** **Evidence:** [forecast service](../backend/app/forecasting.py#L18), [adapter](../backend/research/sprint9_adapter.py#L26), [export flags](../backend/app/research_quality.py#L135), [proposed pilot](PROSPECTIVE_PILOT_PROTOCOL.md#L3). The adapter forces incomplete outcome history and emits no outcomes; the served probability is null. The pilot leaves accountable roles/approvals unresolved.

**Why it matters:** Implementing an evaluation contract is not evidence that migraine can be forecast usefully. Daily status does not establish exact new onset, recovery or independent full-horizon surveillance. There is no defensible real-world sensitivity/AUC/benefit claim.

**Recommended fix:** Keep the no-score boundary. Before any study, obtain an accountable research team, approved consent/privacy protocol and a source audit demonstrating attainable independent onset/coverage evidence. If that cannot be established, retain NO-GO or separately specify descriptive research. Do not add a model to fill this gap.

**Blocks:** Portfolio: only forecasting/clinical-results claims. Synthetic demo: no. Research: yes.

### F02 — Legacy v1 training remains runnable with future-dependent splits

**Sprint 18 status:** Resolved for the confirmed split/coverage mechanism: legacy v1.1 uses declared-grid boundaries and bounded coverage confirmation, with train/validation invariance regressions. V2.1 is unchanged. See [remediation and regression evidence](AUDIT_REMEDIATION.md).

**Severity: High.** **Evidence:** [legacy split](../backend/research/dataset.py#L129), especially its retained-row fractions at line 136; [legacy experiment](../backend/research/experiment.py#L9), [CLI](../backend/research/cli.py#L41), and still-present [v1 instructions](ML_EXPERIMENTS.md#L56). V2 instead uses [fixed candidate-grid boundaries](../backend/research/revision_dataset.py#L142).

**Why it matters:** In an independent constructed 240-row example, removing only the last row changed purged legacy training size from 142 to 141 and changed earlier training membership. Chronological order and horizon purging alone do not prevent this future-dependent selection. The passing v2 regressions do not repair the separate v1 code path.

**Recommended fix:** Mark v1 explicitly deprecated in its CLI and entry-point documentation and disable its training path, or apply fixed-grid/freeze guarantees with dedicated regressions. Direct research replication to v2.1. Do not describe the entire repository as unconditionally leakage-safe.

**Blocks:** Portfolio: no, if disclosed. Synthetic product demo: no. Research using v1: yes.

### F03 — Hosted and real-data security controls are unverified, not operational

**Sprint 18 status:** Deferred: hosted/real-data operational controls require separately authorized staging and sign-off; no deployment occurred. See [remediation and regression evidence](AUDIT_REMEDIATION.md).

**Severity: High.** **Evidence:** [production settings](../backend/app/security.py#L25), [single-worker launcher](../backend/app/serve.py#L31), [proxy template](../deploy/nginx-demo.conf.example#L1), [role grants](../deploy/demo-role.sql.example#L1), [explicit unresolved controls](DEPLOYMENT_READINESS.md#L50). Code validates configuration strings; templates do not install or verify the services they describe.

**Why it matters:** TLS URL validation does not establish server certificates, actual least privilege, encrypted storage, backup erasure, incident response or recoverability. Local SQLite/browser passes cannot support a hosted PostgreSQL or production-security assertion.

**Recommended fix:** Keep localhost as the default demo. For any separately authorized hosting effort, assign operators and verify infrastructure, grants, log redaction, patching, backup/restore and incident procedures in staging. Do not represent placeholder service files as deployment evidence.

**Blocks:** Public source portfolio: no. Local synthetic demo: no; unreviewed hosted demo: yes. Real-world research: yes.

### F04 — Current Vite development-server advisory contradicts a current “zero advisories” claim

**Sprint 18 status:** Resolved for GHSA-8g5g-mxqh-grgj: Vite 6.4.5 installed/locked; compatible builds/tree and fresh npm audit passed. See [remediation and regression evidence](AUDIT_REMEDIATION.md).

**Severity: Medium.** **Evidence:** [locked Vite entry](../frontend/package-lock.json#L3275) is `6.4.4`; [dev command](../frontend/package.json#L7) binds loopback. Fresh npm audit identifies GHSA-8g5g-mxqh-grgj. The [maintainer advisory](https://github.com/vitejs/vite/security/advisories/GHSA-8g5g-mxqh-grgj) identifies 6.4.4 as affected and 6.4.5 as patched, with development-server file-deny bypass under its stated network/file conditions.

**Why it matters:** A developer serving a reachable Vite instance could expose files expected to be denied. This is a development-tool risk, not evidence that the generated static JavaScript bundle has that server vulnerability. No private-file exploit was attempted; the repository defaults reduce network exposure. Historical zero-advisory reports may have been true when recorded but are not today's clearance.

**Recommended fix:** In a separate change, update the resolved Vite version to a compatible patched release, regenerate/review the lockfile and rerun relevant build/browser/advisory checks. Continue serving static builds for any later approved hosting, never the development server.

**Blocks:** Source portfolio: no, with disclosure and prompt remediation. Network-exposed dev demo: yes until patched; bounded local/static synthetic demonstration: not by itself. Research environments using the affected server: remediate before use; other research blockers remain.

### F05 — Episode acceptance and quality-review chronology disagree

**Sprint 18 status:** Resolved for input/review consistency: shared interval policy, POST/PUT model rejection, frontend guards and historical-record preservation regressions. See [remediation and regression evidence](AUDIT_REMEDIATION.md).

**Severity: Medium.** **Evidence:** [episode chronology](../backend/app/tracking_schemas.py#L35) rejects an end before, but not equal to, onset and does not reject future instants. [Quality review](../backend/app/research_quality.py#L47) rejects equality and future instants. [Descriptive pattern logic](../backend/app/pattern_insights.py#L33) separately skips future onsets.

**Why it matters:** Independent authenticated in-memory API probes accepted a zero-length episode with HTTP 201, after which quality review flagged `inconsistent_episode_interval`; a future-onset probe also returned 201. Different screens can therefore disagree about an entry accepted by the same product. This is data-quality behavior, not a demonstrated authorization exploit.

**Recommended fix:** Decide and document one interval policy. Reject impossible/future completed observations at the input boundary or explicitly type planned/uncertain observations separately. Define whether zero-length means a valid instantaneous event or invalid duration and align analytics/quality tests.

**Blocks:** Portfolio: no if disclosed. Read-only fixture demo: no; an editable “all entries are validated” claim is unsupported. Research data capture: fix before relying on these records.

### F06 — A saved trusted contact can have no dialable number

**Sprint 18 status:** Resolved for syntax and dialing safety: shared policy on server/browser, invalid legacy destinations expose no call/SMS link; no reachability claim. See [remediation and regression evidence](AUDIT_REMEDIATION.md).

**Severity: Medium.** **Evidence:** [contact schema](../backend/app/main.py#L146) accepts punctuation-only strings; [normalization](../frontend/src/assistance.ts#L5) removes that punctuation. A probe saved phone `---` with HTTP 201 and zero digits, yielding an empty dialing destination after normalization.

**Why it matters:** A successfully saved support contact can fail at the moment it is needed. No phone call was placed to verify platform behavior; the empty normalized destination itself is confirmed.

**Recommended fix:** Validate a nonempty sensible dialable number after normalization on both server and form, retaining appropriate international/local formats. Add punctuation-only and normalization regression cases. Do not claim validation guarantees reachability.

**Blocks:** Portfolio: no if disclosed. Current empty-contact synthetic fixture: no; contact-calling demonstration must use reviewed fictional values without activating links. Real support use: yes for this flow until fixed and device-tested.

### F07 — One unrelated fetch failure can suppress healthy tracking/support data

**Sprint 18 status:** Resolved for the confirmed operations: independent read results, support-specific state, protected profile writes and read-only retry/no-duplicate-POST regressions. See [remediation and regression evidence](AUDIT_REMEDIATION.md).

**Severity: Medium.** **Evidence:** [workspace refresh](../frontend/src/main.tsx#L50) loads seven resources through one `Promise.all` and sets all results only after every request succeeds; [Attack Mode props](../frontend/src/main.tsx#L62) pass the shared error, and [support rendering](../frontend/src/AttackMode.tsx#L33) gates contacts/card on that error.

**Why it matters:** From source inspection, a failed insights/wellness request can prevent a successful contacts/profile response from becoming usable on initial load. The emergency link remains independent; this is not total emergency-access loss. A dedicated unrelated-endpoint outage probe was not run, so this is a source-supported failure-coupling finding rather than a newly measured outage.

**Recommended fix:** Use independent resource states and retries, especially for contacts/support/session data. Preserve healthy results and clearly identify unavailable sections. Add one integration regression where insights fails while contacts remains available.

**Blocks:** Portfolio: no. Normal synthetic demo: no, but degraded operation remains fragile. Real support workflows: address before making availability claims.

### F08 — Read-only demo still offers controls that imply writable functionality

**Sprint 18 status:** Deferred: guarded embedded forms still have read-only affordance limitations; no additional high-severity guided-demo blocker confirmed. See [remediation and regression evidence](AUDIT_REMEDIATION.md).

**Severity: Medium.** **Evidence:** [DailyCheckin](../frontend/src/DailyCheckin.tsx#L47), [account forms](../frontend/src/AccountSettings.tsx#L10), [Attack Mode session control](../frontend/src/AttackMode.tsx#L31), and [client write guard](../frontend/src/api.ts#L6). The built-demo test deliberately clicks Save and receives a read-only error ([test](../frontend/deployment-e2e/demo.pw.ts#L33)).

**Why it matters:** Backend guards correctly prevent mutation, but a reviewer can type into forms or initiate actions that cannot succeed. Safety enforcement and a polished demo are different concerns. Some main-workspace controls already explain read-only mode before opening a form; behavior is inconsistent across embedded components.

**Recommended fix:** Propagate explicit mode to embedded forms/session/account controls; disable mutation with a nearby reason while retaining history/logout/export. Do not remove server-side guards. Keep browsing read-only and do not solicit real inputs.

**Blocks:** Portfolio: no. Guided script: no; exploratory demo polish: incomplete. Research: not a collection solution.

### F09 — Shared demo login is an availability bottleneck

**Sprint 18 status:** Deferred for unattended hosting: retain throttling and the single guided localhost demo boundary. See [remediation and regression evidence](AUDIT_REMEDIATION.md).

**Severity: Medium.** **Evidence:** [account limiter](../backend/app/auth.py#L107) counts successful and unsuccessful login attempts against the same account key; [login](../backend/app/auth.py#L134) always calls it. A fresh limiter reproduced 10 permitted checks followed by HTTP 429. Demo provisioning uses one reserved account ([provisioner](../backend/app/demo.py#L24)).

**Why it matters:** More than ten login attempts across all viewers in a 15-minute window can block a shared demo even when passwords are correct. The process-local limiter also does not provide distributed abuse protection. This is not an argument to remove brute-force protection.

**Recommended fix:** Before an unattended/public demo, design a demo-specific abuse/availability policy at the application and ingress boundaries and verify simultaneous viewers/restarts. For a small local presentation, sign in once and rehearse failure messaging.

**Blocks:** Source portfolio: no. Single guided localhost demo: no; reliable unattended shared demo: yes until addressed. Multi-worker/research service: needs an explicit shared policy.

### F10 — Full-history reads and repeated scans have no demonstrated scale bound

**Sprint 18 status:** Deferred: no large-history performance claim; representative profiling/query work remains. See [remediation and regression evidence](AUDIT_REMEDIATION.md).

**Severity: Medium.** **Evidence:** [episode listing](../backend/app/main.py#L200), [daily listing](../backend/app/prospective.py#L102), [quality preparation](../backend/app/research_quality.py#L108), and per-row revision filtering in [analysis](../backend/app/research_quality.py#L75). Quality loads full histories and repeatedly scans revisions/wellness; the response window does not bound database reads.

**Why it matters:** A long-lived account can make listing, quality review and export expensive. No load test or p95 latency claim is supported. Small synthetic fixtures cannot demonstrate suitable longitudinal performance, and raising worker count would not resolve query complexity.

**Recommended fix:** First profile bounded synthetic long histories. Add owner/date filtering, group revisions once, paginate UI lists and use consistent snapshot reads for export. Preserve complete revision chains when selecting dates; never optimize by truncating history silently.

**Blocks:** Portfolio/small synthetic demo: no. Research-scale deployment: performance and snapshot behavior need evidence before approval.

### F11 — Maintainability and data integrity depend heavily on application orchestration

**Sprint 18 status:** Deferred: no unrelated refactor or schema change; storage administrator and direct-SQL boundaries remain. See [remediation and regression evidence](AUDIT_REMEDIATION.md).

**Severity: Medium.** **Evidence:** [main models/engine/routes](../backend/app/main.py#L16), integer-only [episode session link](../backend/app/main.py#L75), [daily JSON state](../backend/app/prospective_models.py#L7), and the compressed [workspace orchestration](../frontend/src/main.tsx#L28). Owner-scoped API checks exist, but cross-owner consistency and several chronology rules are not database-enforced. Alembic imports the application engine through [env.py](../backend/alembic/env.py#L2).

**Why it matters:** Current API tests protect the intended route paths; future maintenance/direct imports can bypass assumptions. ORM definitions, auth setup, migrations and route registration are tightly coupled. Dense multi-action lines make independent review and debugging harder.

**Recommended fix:** Format existing code first, then separate database/session/models from app construction and split UI data/state responsibilities incrementally. Add appropriate foreign keys/constraints and storage-consistency tests for essential invariants. Avoid a broad rewrite as a prerequisite to a portfolio presentation.

**Blocks:** Portfolio/synthetic demo: no. More ingestion paths or real-data operations: resolve the relevant integrity boundaries before adding them.

### F12 — Strong tests lack a checked-in continuous, self-isolating execution path

**Sprint 18 status:** Partially addressed: targeted regressions and full isolated checks added/run; checked-in CI/test-lifecycle automation remains deferred. See [remediation and regression evidence](AUDIT_REMEDIATION.md).

**Severity: Medium.** **Evidence:** Git tracked inventory has no `.github/workflows` files. [Standard Playwright config](../frontend/playwright.config.mjs#L2) targets a caller-provided/default running server without managing its database lifecycle; [real account test](../frontend/e2e/authentication.pw.ts#L3) creates/deletes accounts. The [demo config](../frontend/playwright.demo.config.mjs#L3) has a loopback check, but loopback alone does not prove a disposable database.

**Why it matters:** The tests are meaningful, but their safe reproducibility depends on manual environment setup. A fresh reviewer can aim mutation tests at an existing local instance. Advisory drift and the v1 gap also show why a previous green sprint is insufficient. Frontend worker-start failures were observable in this audit and should not be hidden.

**Recommended fix:** Check in one disposable-target verification harness and CI for backend, frontend, build, documentation and selected real API/browser tests using locked dependencies. Add regression cases for F02/F05/F06/F07; add genuine concurrent-transaction/PostgreSQL cases when that platform is supported. Record skipped optional ML tests explicitly. No need to inflate coverage with tests that mirror implementation.

**Blocks:** Portfolio: no, but materially weakens reproducibility. Synthetic demo: no with explicit isolated setup. Automated research/deployment assurance: yes until lifecycle/platform verification is established.

### F13 — Automated accessibility and device integration coverage is incomplete

**Sprint 18 status:** Deferred: automated checks passed; manual accessibility, comfort, alternate-browser and device handoff evidence remains absent. See [remediation and regression evidence](AUDIT_REMEDIATION.md).

**Severity: Medium.** **Evidence:** [semantic focus styles](../frontend/src/style.css#L64), [reduced motion](../frontend/src/style.css#L262), [product checks](../frontend/e2e/product-quality.pw.ts#L15), and Chrome-only [browser launch default](../frontend/playwright.config.mjs#L2). Fresh screenshots show coherent warm-theme spacing/wrapping at 320px and 1280px; selected keyboard/contrast/viewport checks passed. The screenshot scenarios mock the API.

**Why it matters:** A passing overflow assertion and a few token contrast ratios do not establish WCAG conformance, complete focus behavior, migraine-time comfort or successful phone/SMS/share handoff. Mobile navigation is long; the skip link helps, but real task burden remains unmeasured.

**Recommended fix:** Perform a small, documented manual pass with a screen reader, zoom/large text, touch devices and a non-Chromium browser. Review actual foreground/background pairs and failure states. Test handoffs only through controlled safe procedures, without emergency calls or unsolicited messages. Make narrow accessibility claims until then.

**Blocks:** Portfolio and guided synthetic demo: no. Accessibility certification or participant-use suitability claims: yes; real research needs an approved usability/accessibility assessment.

### F14 — README is informative but is not a clean current-state reviewer entry point

**Sprint 18 status:** Deferred: methodology guides corrected for v1.1; broad README archival restructuring remains a follow-up. See [remediation and regression evidence](AUDIT_REMEDIATION.md).

**Severity: Medium.** **Evidence:** [setup](../README.md#L10) uses broad Python requirements and `npm install`; [structure](../README.md#L67) still calls `main.tsx` the API client despite [api.ts](../frontend/src/api.ts#L1); [verification heading](../README.md#L70) leads into early 2/3-test results, followed by extensive sprint history. Current introductory caveats label old verification historical, so this is not evidence that the author fabricated those runs.

**Why it matters:** Reviewers must reconcile several generations of behavior and instructions. A current setup from broad ranges is not a reproduction of recorded lockfile-based results. Existing 260 working links are a strength but do not fix navigation/version ambiguity.

**Recommended fix:** Keep one short current overview, one locked synthetic quickstart, one current verification command section and explicit limitations. Move historical sprint detail to an archive and keep v1 clearly historical. Use `npm ci` and the reviewed Python lock for reproducibility; verify that path on a clean machine.

**Blocks:** Portfolio: no, but should be improved before a high-stakes submission. Synthetic demo: no if runbook followed. Research replication: requires an unambiguous version/environment.

### F15 — App history/download confirmation is not research governance or de-identification

**Sprint 18 status:** Deferred: consent/governance, complete historical availability and download/backup lifecycle remain real-data blockers. See [remediation and regression evidence](AUDIT_REMEDIATION.md).

**Severity: High for real-data use.** **Evidence:** [daily revisions](../backend/app/prospective_models.py#L20), current editable [episode model](../backend/app/main.py#L60), [account deletion](../backend/app/auth.py#L150), [export](../backend/app/research_quality.py#L131), and [account privacy copy](../frontend/src/AccountSettings.tsx#L10).

**Why it matters:** Legacy diary/wellness/early-symptom edits have no complete historical journal. Daily journals are application-managed rather than administrator-proof. Account deletion removes app-owned journals, not downloads/backups. Numeric exports retain exact timelines; per-download confirmation is not study enrollment. These limitations are largely disclosed correctly, but they are still real research/privacy blockers.

**Recommended fix:** Before real collection, define approved enrollment/withdrawal/retention and adjudication records, storage/backup access controls and source-integrity review. Version or revoke affected research snapshots transparently after corrections/withdrawal; do not imply app deletion erases all copies. Do not retrofit invented historical versions.

**Blocks:** Honest portfolio/synthetic demo: no. Claims of anonymous exports, immutable complete history or approved real-data collection: yes.

### F16 — Stop rules and descriptive metrics do not establish statistical sufficiency or novelty

**Sprint 18 status:** Deferred: statistical/clinical/generalization/novelty claims remain unsupported; sample gates are unchanged. See [remediation and regression evidence](AUDIT_REMEDIATION.md).

**Severity: High for research claims.** **Evidence:** [engineering gates](../backend/research/baseline_v2.py#L20), [fixed evaluation](../backend/research/baseline_v2.py#L62), [metric definitions](../backend/research/evaluation.py#L5), [periodic synthetic target](../backend/research/synthetic_fixture.py#L22), and [56-day feasibility proposal](PROSPECTIVE_PILOT_PROTOCOL.md#L9).

**Why it matters:** The 180-window/class gates are not power calculations. Serial dependence, per-person event support, reporting/selection bias, uncertainty and transportability remain unresolved. A short pilot cannot satisfy the per-person gate by pooling people. A deterministic fixture tests software mechanics; apparent calibration/accuracy says nothing about a population.

**Recommended fix:** Retain fixed comparators and explicit metric definitions. A later approved statistical plan must justify sample/event counts, missingness/selection analysis, lag sensitivity, dependence-aware uncertainty, relevant subgroups and external/prospective evaluation. Do not add model complexity or claim a research advance before evidence exists.

**Blocks:** Methods/software portfolio and synthetic demo: no. Predictive-effectiveness, clinical-utility, statistical-sufficiency or population-generalization claims: yes.

### F17 — Personal contribution and AI-assistance attribution require confirmation

**Sprint 18 status:** Awaiting presenter confirmation: no personal/sole authorship or AI-assistance percentages inferred. See [remediation and regression evidence](AUDIT_REMEDIATION.md).

**Severity: High for interview defensibility.** **Evidence:** [interview attribution section](INTERVIEW_PREPARATION.md#L42) already states the boundary. Git author labels and merged commits record provenance of commits, not how much design, implementation, testing or tool assistance came from each person.

**Why it matters:** A technically correct project can fail an interview if the presenter claims independent implementation they cannot explain or reproduce. This audit cannot infer the candidate's actual contribution from generated-looking code or account names.

**Recommended fix:** Have the presenter confirm a component-by-component contribution/assistance ledger and prepare one decision, one bug investigation and one code explanation they can defend. Credit collaborators/tools accurately. Do not invent percentages of AI-generated code or replace missing confirmation with an accusation.

**Blocks:** Project-level source portfolio/synthetic demo: no. Sole-authorship or specific first-person implementation claims: yes until confirmed. Research authorship also needs responsible contributor attribution.

### F18 — Offline reports can overwrite prior experiment evidence

**Sprint 18 status:** Deferred: explicit output directories can still be overwritten; no real experiment archive was created. See [remediation and regression evidence](AUDIT_REMEDIATION.md).

**Severity: Low.** **Evidence:** [CLI output writes](../backend/research/baseline_cli.py#L40) use fixed `report.json`/`dataset.json` filenames and overwrite within an existing output directory; the [synthetic fixture writer](../backend/research/synthetic_fixture.py#L44) instead refuses overwrite.

**Why it matters:** Hashes identify inputs but do not preserve a report that a later command replaces. This weakens the practical “immutable experiment” workflow, even though repeatability tests correctly compare identical reruns.

**Recommended fix:** Use fresh versioned/run-addressed output directories by default or require explicit overwrite, and preserve input/source/config manifests under an approved retention policy. Never commit patient-level outputs to Git as a substitute for secure provenance.

**Blocks:** Portfolio/synthetic demo: no. Archival research reproducibility: address before treating reports as an immutable audit record.

## What is differentiated, and what remains conceptual

Ordinary implemented engineering includes CRUD diaries, React/FastAPI integration, cookie authentication, descriptive charts, manual support links and deterministic preference/feedback ordering. The [support ranker](../backend/app/support_engine.py#L8) uses explicit preferences and smoothed self-reported ratings, not a learned clinical policy or autonomous emergency agent.

The project's more interesting engineering combination is explicit unknown-day handling, server-availability revision journals, separation of preparation exports from training labels, full-horizon outcome requirements, historical eligibility freezes, fixed-grid purging and a demo that refuses health-record mutation. Those are inspectable implementation choices and strong discussion material. They apply established point-in-time evaluation principles; no new learning algorithm, clinical discovery or demonstrated superiority is established. A priority/novelty claim would require a scoped prior-art comparison, which this audit did not conduct.

Actual personalized next-24-hour forecasting, reliable independent outcome adjudication, approved prospective enrollment, feasible independent surveillance, clinical effectiveness and hosted operations remain conceptual or unverified. The runtime's null score is consistent with those gaps, not a missing integration that should be patched quickly.

The Park decision must remain task-specific. The original [Park paper](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0149577) studies daily diary/trigger associations; its methods collect same-day factors rather than establishing MigraMind's strict historical forecasting evidence. The [repository audit](PARK_DATASET_AUDIT.md#L7) records missing verified submission/revision history, independent onset/coverage and identifier/outcome issues, with conditional descriptive reuse. This independent review verified the published task/method context and compared the stated gaps to the implemented contract; it did **not** reopen the patient workbook or independently recount its rows. Therefore workbook-specific contradictions remain attributed to that audit, not newly reproduced research findings. NO-GO for this strict forecasting task does not mean the dataset is useless or fraudulent.

## Fifteen difficult interview/review questions

Each answer should be supported by code or a concrete limitation, not a memorized claim of “AI-powered prediction.”

| # | Hard question | What a defensible answer must cover |
| --- | --- | --- |
| 1 | What has actually shipped that deserves the word AI, and what happens when I request a risk score? | Tracking/support and offline experiments are implemented; the forecast response has null probability. Support ordering is deterministic. Explain the “in development” label without implying validated prediction. |
| 2 | Walk through one cutoff with a backdated report, a correction exactly at the cutoff and a later tombstone. | Event time differs from server availability; features use strict `< t`, not `<= t`. Reconstruct versions, distinguish tombstones known before the cutoff from later changes, and explain partial legacy history. |
| 3 | Can dropping a future test window change your training population? | Show the confirmed v1 defect and v2 fixed-grid boundary. Explain that purging after a retained-row split does not fix future-dependent cohort selection. Do not defend all pipelines as equivalent. |
| 4 | Why do positives also need complete observation, and what bias do excluded windows introduce? | Class-dependent logging and selection; full-horizon evidence for both classes; exclusion denominators and missing-not-at-random bias remain even after conservative rules. |
| 5 | What independently verifies migraine onset and no attack? Is a reviewer checkbox sufficient? | No. Define acceptable independent evidence under an approved protocol and distinguish reported event, diagnosis, reviewer attestation and true completeness. Acknowledge that feasibility has not been established. |
| 6 | Why freeze labels after 24 hours of lag when patients can report later? | It is a fixed protocol assumption, not proof of completeness. Explain bounded snapshots, frozen historical evidence versus current truth, sensitivity analysis and withdrawal revocation/versioning. |
| 7 | Does your split demonstrate new-patient generalization? | No: one account, later-time held-out evaluation. Explain time dependence, horizon/label purging, grouped/time designs for future population studies and the absence of external evidence. |
| 8 | Why can constant-score trapezoidal PR-AUC differ from average precision? Which metric would you trust? | Explain interpolation/ties, report both definitions, compare Brier against training-only frequency and inspect calibration denominators. No one metric proves usefulness or clinical calibration. |
| 9 | Could your synthetic model results just learn a generator artifact? | Yes: periodic targets and constructed evidence are software fixtures. Reproducible hashes and metric agreement validate mechanics, not disease realism or future accuracy. |
| 10 | Why 180 windows and these class minima? Can your proposed pilot meet them? | Engineering stop rules, not power. A 56-day individual pilot cannot satisfy them; pooling people changes the task. A statistician must justify a later study independently. |
| 11 | Threat-model the HttpOnly cookie, CSRF bootstrap, stale tabs and shared-demo account. | Server-side token digests/expiry/rotation, read-session binding and mutation Origin checks; no cure for XSS/privileged DB access. Explain login throttling and the confirmed shared-account availability limit. |
| 12 | What does “delete my data” mean after research export or backup? | App-owned rows/journals are deleted; downloads/backups require separate governance. Timelines are not anonymous. Support consent and per-download confirmation do not create research enrollment. |
| 13 | What invariants survive concurrent requests or direct database access, and what PostgreSQL evidence do you have? | Daily compare-and-swap and unique slots have tests; many chronology/ownership rules are application-level. SQLite results do not establish PostgreSQL concurrency, grants or migration success. |
| 14 | What did this independent audit find that your tests missed? | Reproduce F02/F05/F06, explain F07's shared failure state, current Vite advisory scope and lack of CI/safe test lifecycle. Distinguish environment startup failures from failed product assertions. |
| 15 | Which code and decisions are personally yours, which were AI-assisted, and can you modify one safely without assistance? | Give confirmed roles and assistance, not authorship guesses or fabricated percentages. Explain a chosen implementation and test, review an alternative, and demonstrate ownership through reasoning. Git author names alone are insufficient. |

## Original prioritized next work (before Sprint 18 remediation)

1. **Before the next high-stakes interview:** confirm F17 attribution; rehearse the existing synthetic script with honest unavailable/empty states. Prepare the independent bug/split examples. No new model or feature expansion is needed.
2. **Small engineering/security patch:** remediate F04, unify episode chronology (F05), reject empty dialing destinations (F06), and preserve usable support data under unrelated failures (F07). These are concrete changes with targeted regression value, not a redesign.
3. **Close research-path ambiguity:** deprecate/disable v1 training (F02), identify v2.1 as the only current reference, and preserve experiment outputs safely (F18). Do not lower coverage/class gates just to produce metrics.
4. **Make the portfolio easy to verify:** shorten the current README and archive sprint history (F14); add a locked, disposable verification harness/CI (F12). Keep documentation claims tied to actual tests, including advisory dates and execution limits.
5. **Polish the bounded demo:** make embedded read-only controls explicit (F08), retain the fixture's genuine creation/event distinction, and assess shared-login limits only if an unattended demo is planned (F09). Do not introduce a destructive browser reset or disguise old fixtures as prospective data.
6. **Before participant-facing use:** complete manual accessibility/device tasks (F13), profile synthetic long histories and enforce relevant storage invariants (F10-F11). Do not treat source cleanup as research approval.
7. **Only for a separately authorized research/hosting effort:** close F01/F03/F15/F16 with named institutional, statistical, privacy and operational owners. If independent outcomes cannot be obtained lawfully and defensibly, retain forecasting NO-GO and present the engineering contribution as it stands.

No full-stack rewrite, new predictive model, real health-data collection, deployment, commit, push, PR or merge was performed or recommended as an automatic next action. Stop point: this audit document and its non-destructive verification evidence.

## Sprint 18 final verification and remaining boundaries

Independent final review on 2026-11-03: **254 backend tests**, **79 frontend tests**, **21 full Playwright checks**, **2 built synthetic-demo checks**, and both editable/synthetic production builds. The legacy canonical synthetic fixture retains identical split counts/model metrics; the complete v2 synthetic report, dataset hash and metrics match the pre-change report and repeated fit. The fixed-grid/late-coverage regressions now hold earlier training and validation stable. These are software results, not forecasting effectiveness.

Fresh dependency checks: npm audit reports zero known advisories; isolated OSV Python audit reports **38 packages, zero known advisories, zero skips**; installed base/ML pins and compatibility checks pass. All **11 pre-existing database/migration file hashes** match the pre-change manifest. The existing database was not migrated, queried for records or used by tests. No migrations were changed. Security scans do not establish hosted or clinical readiness.

F02/F04/F05/F06/F07 are resolved for the confirmed mechanisms. The remaining high findings concern actual research, hosted operations or personal attribution and remain gated. Original scores above are the independent pre-remediation assessment, not a new certification. See [AUDIT_REMEDIATION.md](AUDIT_REMEDIATION.md) for all 18 dispositions, precise policy changes, execution caveats and deferred work. No real-data collection, deployment or merge is included. Final-review publication is authorized separately as a commit and PR targeting `main`.

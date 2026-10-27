# Sprint 13: research readiness decision gate

Assessment date: 2026-10-27. Scope: current MigraMind repository plus the [acquisition plan](RESEARCH_DATA_ACCESS.md) and [draft pilot](PROSPECTIVE_PILOT_PROTOCOL.md). **No participant recruitment, contact, real-data acquisition, model training or deployment is authorized by this gate.** Owners below are roles to appoint, not claims of an existing institution or approval.

## Four distinct layers

| Layer | What a pass would establish | Current evidence/status | What it cannot establish |
| --- | --- | --- | --- |
| Prototype functionality | Synthetic-tested account ownership, revisions, explicit statuses, missingness and preparation downloads | Implemented with documented limitations in Sprints 9–11; no new runtime verification in Sprint 13 | Research permission, production security, verified outcomes or clinical performance |
| Research approval and operations | Named institution/PI, authorized protocol, consent, privacy/security review, managed hosting and incident/withdrawal processes | **BLOCKED / NOT APPROVED**; no enrollment ledger or approved study operations | That observations are complete, sufficient or predictive |
| Dataset quality and evaluation readiness | Lawful provenance plus genuine as-of feature versions, independent outcome evidence, full coverage, participant isolation, sufficient purged chronological samples | **BLOCKED**; app adapter supplies no verified outcomes, no eligible real bundle; Park release **NO-GO** | Clinical benefit, safety or generalization from synthetic/software results |
| Clinical validation and deployment | Separately approved prospective validation of a specified intended use, performance/uncertainty, safety, equity and governance with appropriate regulatory review | **NOT ESTABLISHED**; no claim or deployment planned | Approval from diary counts, engineering thresholds, a single retrospective result or a passed pilot |

Progress is not a numeric readiness score. Passing one layer does not imply the next, and approval can be suspended. Software gates such as 180 windows/180-day span and class minima are engineering constraints, not clinical sample-size evidence. A 56-day feasibility pilot cannot satisfy those personalized-baseline gates by pooling people.

## Decision records and required evidence

| Gate | Required record and accountable owner | Current decision |
| --- | --- | --- |
| G0: internal research plan | Project lead reviews source-backed scope, honest target, limitations and unsent email; names institution/PI and approves any next action separately | Draft documents available; organizational owner unresolved |
| G1A: external metadata inquiry | Authorized sender verifies professional contact and truthful affiliation; institution determines requirements for metadata discussion; no health attachments | Prepared, **not sent**; explicit outreach authorization still needed |
| G1B: external data access | PI/custodian confirm investigator eligibility, current control, protocol-specific permission, ethics/privacy determinations, ML scope, DUA, security location, retention/withdrawal and transfer route | **BLOCKED**; publication request route is not a grant |
| G2: human pilot activation | PI/site hold approvals/determinations, consent materials/ledger, approved definitions, funded independent adjudication, staff roles, accessibility checks, hardening/incident plan and participant contacts | **BLOCKED**; current app remains local synthetic prototype |
| G3: source/evidence audit | Data steward and independent reviewer verify genuine availability/revision chains, onset/recovery/uncertainty, complete positive/negative coverage, stable IDs and source dictionary against an approved immutable snapshot | **BLOCKED** for app; Park published artifact fails strict task; N1-Headache unresolved |
| G4: later offline evaluation authorization | Statistician/PI approve registered analysis, event/duration justification, sufficient individual classes, fixed candidate grid, purged splits and training-only preprocessing; all prior gates satisfied | **NO-GO now**; feasibility success only permits designing this stage |
| G5: clinical validation/deployment | Clinical lead, ethics/privacy/security owners and relevant regulatory reviewers approve a separate intended-use study and deployment case | **NOT VERIFIED / OUT OF SPRINT SCOPE**; never inferred from offline metrics |

For every actual decision record: gate ID, protocol/source versions, requested activity, evidence links in approved storage, decision (GO / CONDITIONAL GO / NO-GO / NOT VERIFIED), unmet conditions, named approver, decision time, review date/expiry and revocation conditions. Store no patient details or credentials in Git. A blank approval or a future task is not a pass. No fictitious signature/approval number is supplied here.

## Non-negotiable dataset checks

The [offline contract](ML_RESEARCH_BASELINE.md) remains authoritative. Reuse it rather than translating a final CSV into fictional revisions.

1. Consent/provenance is reviewed for this study and participant, with permitted-use and withdrawal scope. Caregiver consent, download confirmation and another study's IRB decision do not enroll anyone.
2. Every feature version was genuinely available **strictly before** its cutoff. Reported event time and diary date do not backdate receipt; exclude unverifiable legacy or truncated history. No whole-study aggregation, exit survey or outcome-period information enters features.
3. Exact new-onset evidence is independent and reviewable under a defensible protocol, with recovery/ongoing and time uncertainty resolved. A daily status, symptom classification or reviewer checkbox alone does not qualify.
4. Positives also require complete verified observation coverage across the entire elapsed-24-hour horizon; negatives require complete explicit verified no-episode coverage. Missing, unknown, conflicting, deleted or partly observed horizons never become negative. Separate-source copying does not establish independence.
5. Feature availability, outcome adjudication and eligibility freeze are distinct clocks, bounded by an immutable captured/dataset-as-of manifest. Later edits do not rewrite earlier available information or silently select earlier windows. Legally required withdrawal/removal revokes or versions affected snapshots transparently; it does not justify pretending old historical inputs never existed.
6. Candidate cutoffs and split boundaries are fixed before retained outcomes; purge overlapping horizons and label/adjudication availability. No cross-account bundle, duplicate-person overlap or future participant-specific aggregate crosses partitions. Population generalization requires an independently reviewed grouped/time design; concatenating single-account bundles is unsupported.
7. Report all candidate/retained/excluded counts with reasons, class balance, missingness and per-person span. Insufficient/single-class cases stop fitting and do not manufacture metrics. Any later authorized experiment reports appropriate naive comparators, PR-AUC only where defined, Brier/calibration with denominators and uncertainty. Synthetic metrics test code, not clinical effectiveness.

## Pilot progression, pause and stop

Use the [pilot's proposed denominator definitions and feasibility targets](PROSPECTIVE_PILOT_PROTOCOL.md), approved before enrollment. They concern retention, timeliness, structural integrity, independently adjudicable coverage, burden and privacy; none is a clinically validated forecasting requirement.

- **GO for synthetic rehearsal only:** today, within existing local prototype boundaries. Use no private application records, patient exports or workbook rows as fixtures. No runtime change or experiment is invoked by this documentation sprint.
- **CONDITIONAL GO to design a later forecasting study:** only after an approved pilot meets its feasibility targets and independent evidence is genuinely attainable at acceptable burden. A statistician must assess event rates, effective sample size, time dependence, class support and duration before any training decision. The short pilot alone is not a ready research training set.
- **REVISE / NO-GO:** retain NO-GO for strict forecasting if independent onset/coverage or historical availability cannot be established, even with high completion. Poor retention/burden requires protocol revision and amendment rather than deleting nonadherent participants. Consider a separately named descriptive research question only with appropriate approval.
- **Immediate pause:** suspected cross-account exposure, consent scope failure, serious privacy incident, systemic timestamp/history corruption or unavailable responsible staff. Stop affected recruitment/collection/export, contain and investigate through the approved incident process, and resume only after institutional authorization. Unknown outcomes remain unknown while investigated.

## Current blocker register and next actions

| Blocker | Minimum next evidence | Proposed responsible role |
| --- | --- | --- |
| No accountable research institution/PI/site or approvals | Named accountable team, jurisdiction, sponsor and approval/determination path | Project lead / institution |
| N1-Headache access, current contact authority and export semantics unconfirmed | Separately authorized metadata-first inquiry and questionnaire responses; no transfer yet | PI / custodian |
| No durable research enrollment or independent outcome journal | Approved consent/evidence design with source independence reviewed, then separately authorized implementation and synthetic tests | PI / clinical reviewer / engineer |
| Local prototype not ready for real health data | Security/privacy gap closure and sign-off, managed storage, access, recovery, retention/backup erasure and incident rehearsal | Security / privacy / operations leads |
| Feasibility and personal class sufficiency unknown | Approved pilot metrics with honest denominators, then later study design; no threshold relaxation to force a fit | Statistician / PI |
| Clinical effectiveness unknown | Future independently approved prospective validation; no prediction UI or clinical claim | Clinical governance lead |

Recommended next action is internal document review and appointment of the responsible institutional team. Review the unsent inquiry and pilot evidence standard, choose whether to pursue permissioned metadata or an ethics-ready collection protocol, and authorize that next step explicitly. If neither route can satisfy evidence/privacy constraints, document NO-GO rather than redefine missing data or lower integrity standards.

## Sprint 13 verification scope

This sprint adds only three planning Markdown documents. It reuses [Sprint 9](PROSPECTIVE_COLLECTION.md), [Sprint 10](ML_RESEARCH_BASELINE.md), [Sprint 11](RESEARCH_DATA_QUALITY.md), [prototype security limits](authentication-privacy.md), [Sprint 12](DATASET_FEASIBILITY.md) and the [Park audit](PARK_DATASET_AUDIT.md). No runtime functionality, migration, consent ledger, study service, dataset, model or permission flag is changed. Final documentation checks passed: 22 local links resolve, nine Markdown tables have consistent column counts, all three files pass UTF-8/whitespace and credential-pattern checks, and pre-publication Git scope contains only the three requested new documents with no tracked modifications or staged files. Manual review separates published facts, proposed protocol choices and unresolved approvals; published professional contact addresses are not credentials or participant data. Final review also clarifies disclosure-safe metadata requests, end-of-study horizon boundaries and optional final confirmation without post-withdrawal collection. Backend/frontend/browser/build suites are not rerun for documentation-only changes; previous test results are historical, not new research evidence. No contact, recruitment or real health collection occurred. Subsequent Sprint 13 finalization instructions authorize committing these three documents, pushing the branch and creating a PR after checks; merging remains unauthorized.

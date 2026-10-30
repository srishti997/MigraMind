# MigraMind interview preparation

Sprint 17, 2026-10-30. Use the [research presentation](RESEARCH_PRESENTATION.md) for the five-minute demo, [architecture](PROJECT_ARCHITECTURE.md) for system detail and [evidence matrix](PROJECT_EVIDENCE_MATRIX.md) to substantiate answers. Attribute individual work only where personal authorship can be established; repository inspection alone cannot establish who designed or implemented each contribution.

## Two-minute explanation

“MigraMind is a full-stack migraine diary and research-readiness prototype. The product supports diary entries, daily status, descriptive insights and user-controlled support preferences. I present it as research infrastructure because no clinically validated forecasting model is available and the application generates no risk score.

“The interface uses React and TypeScript, with a FastAPI backend, SQLAlchemy persistence and Alembic migrations. Authentication uses opaque cookie sessions, password hashing and server-side account isolation. The demonstration runs against a dedicated fictional fixture with frontend and backend write guards.

“The research challenge is reconstructing what was known at a prediction cutoff. A diary entry can be backdated or edited, and missing logs cannot mean no migraine. Daily check-ins therefore preserve server-timestamped creation, correction and deletion revisions. The offline baseline uses only versions available before the cutoff. It requires separate, independently reviewed onset and coverage evidence to label the next 24 hours.

“Evaluation uses chronological partitions fixed before outcome filtering, purges overlapping horizons and label availability, and fits preprocessing on training data only. The fixed baselines include historical frequency and logistic regression. Synthetic tests check these rules; they do not demonstrate real forecasting performance.

“A public dataset audit concluded NO-GO for this task because availability and outcome evidence could not be established. The next step is responsible research access or an approved feasibility pilot, alongside security and operational review. The strongest result today is an inspectable system that explains why prediction is unavailable and what evidence would be needed to evaluate it honestly.”

Rehearse aloud to fit the time; shorten component names before dropping the evidence boundary. Replace any first-person contribution statement with your verified role.

## Technical questions and accurate answers

| Question | Answer |
| --- | --- |
| What does the AI currently predict? | Nothing in the running product. The forecast endpoint returns insufficient data, null probability/model version and false clinical validation. Offline baselines are separate research software. |
| Why this stack? | React/TypeScript implements interactive typed UI flows; FastAPI/Pydantic validates API inputs; SQLAlchemy and Alembic provide relational persistence and explicit schema evolution. These are observable capabilities; original author motivations are not recorded by source inspection. |
| Why cookies rather than browser-stored JWTs? | This implementation uses opaque HttpOnly cookies with server-side token digests, expiry and revocation. CSRF headers bind protected reads to the mounted session; mutations also validate Origin. It does not depend on local-storage authentication tokens. This is a design tradeoff, not proof against all browser attacks. |
| How is cross-account access prevented? | Authenticated user dependencies and owner-scoped queries apply to records, linked IDs and exports. Legacy unclaimed rows stay hidden. Bidirectional ownership and stale-tab regressions exist; independent security assessment remains necessary. |
| Are all records immutable? | No. Daily check-in APIs insert revision rows and tombstones; legacy diary/wellness/early symptoms lack complete revision histories. Administrators can alter storage. Account erasure removes app-owned journals. |
| What if a user backdates sleep or corrects an old report? | Reported event time remains distinct from server availability. Features select revisions strictly before the cutoff. A later correction cannot retroactively enter an earlier feature vector. |
| What is a negative example? | Complete, explicitly no-episode coverage over the full next-24-hour horizon with independent review and no conflicting evidence. No entry, unknown status or general surveillance alone is insufficient. A completed daily no-migraine statement is not automatically such a label. |
| Why require coverage for positives too? | Counting recorded onsets as positives while guessing missing windows are negative selects classes through different reporting processes. Full-horizon evidence is required for both; the real-world validity of that evidence still needs review. |
| How do you prevent leakage? | Strict pre-cutoff revisions, separate label/eligibility freezes, fixed candidate-grid chronological boundaries, purging by horizon and label availability, training-only preprocessing and fixed v2 hyperparameters/threshold. Tests cover future edits and future holdout exclusions. |
| Why not random cross-validation? | Neighboring rows share histories, reporting patterns and time dependence. The implemented evaluation models later-time use within one account. It does not establish generalization to new people. |
| Why logistic regression rather than a larger model? | The current v2 comparator is fixed and auditable. Data validity is the limiting factor. There is no evidence that a more complex model would improve real forecasting; v2 does not fit XGBoost. |
| What metrics matter? | Ranking, Brier/calibration assessment and threshold error measures on identical held-out rows, with class counts, exclusions and denominators. Trapezoidal PR-AUC and average precision are distinct. Undefined metrics are null; no real performance is claimed. |
| How are timezones handled? | APIs require offset-aware instants where applicable, normalize time comparisons and retain source zones. Completed local days follow IANA midnight/DST boundaries; the prediction horizon is always 86,400 elapsed seconds. Legacy dates do not become exact onsets. |
| Is an export anonymous or research consent? | No. Numeric-only exports can remain identifying through exact timelines. Per-download confirmation is not durable enrollment or a lawful secondary-use basis. Preparation exports explicitly remain unverified and training-ineligible. |
| What did the Park audit establish? | The inspected release could not support this prospective onset task under current evidence requirements. Its daily observations do not supply verified submission/revision and outcome coverage histories. This does not prove the dataset is useless for a separately reviewed descriptive question. |
| Is the demo deployed and production ready? | No hosted deployment is claimed. Local synthetic verification and templates exist. Hosted PostgreSQL/TLS/roles, nginx/systemd execution, encrypted recovery and responsible operational sign-off remain open. Production configuration permits synthetic data only. |
| Does Attack Mode dispatch help? | It offers user-initiated calling/SMS preparation and saved preferences. It does not monitor emergencies, automatically send messages, recommend treatment or depend on model outputs. Never activate those links during a demo. |
| What would you improve next? | Close evidence and governance gaps first: accountable research team, approved protocol/consent, source availability/outcome audit and secure operations. Define sample-size and dependence-aware validation before considering model changes. |

## Personal attribution requires confirmation

Repository history records commits under Srishti Gupta and srishti997, but commit attribution does not establish independent implementation, design ownership or the extent of collaborator/tool assistance. Before using first-person implementation claims, confirm which components you personally designed, coded, tested or reviewed, and how assistance should be credited. No claim of sole authorship is made here; this confirmation is needed for personalized interview wording, not for publishing the project-level documentation.

## Contributions that can be demonstrated

Project-level contributions include integrated tracking/support workflows; session-bound account isolation; explicit unknown values and time semantics; a daily revision journal with stale-write protection; quality/conflict review and confirmed local exports; revision-aware offline evaluation with stop rules; a dataset NO-GO audit; and a guarded synthetic demonstration. Demonstrate each through its implementation/tests, not personal attribution inferred from this document.

The portfolio does not establish a novel algorithm, clinical efficacy, population forecasting accuracy, causal triggers, full accessibility compliance, administrator-proof records, automatic de-identification, approved research enrollment or hosted operational readiness. Historical test counts evidence software checks on their recorded dates, not these broader claims. No new runtime testing is implied by this documentation sprint.

Useful review prompts: ask a reviewer to challenge a cutoff boundary, a missing-day label, an ownership reference and a demo write. Explain the invariant and point to the relevant synthetic regression in the [matrix](PROJECT_EVIDENCE_MATRIX.md), rather than exposing actual private records or running an unapproved experiment.

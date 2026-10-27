# Sprint 13: research collaboration and data-access plan

Prepared 2026-10-27 on `feat/research-acquisition-pilot`. **Draft only; no communication sent, access granted or records obtained.** Read alongside [dataset feasibility](DATASET_FEASIBILITY.md), [Park audit](PARK_DATASET_AUDIT.md), [pilot protocol](PROSPECTIVE_PILOT_PROTOCOL.md) and [readiness gate](RESEARCH_READINESS_GATE.md). Park's published release remains NO-GO for prospective next-24-hour onset forecasting.

## Verified publication routes

Verification concerns published roles and addresses, not current employment, mailbox operation, legal controller status or authority to approve a transfer. Recheck through the publisher/institution before any separately authorized outreach. These are public professional contacts, not participant details or credentials.

| Lead | Publication evidence | Appropriate scope |
| --- | --- | --- |
| Marina Vives-Mestres, PhD; published correspondence address `mvives@curelator.com` | Correspondence block on page 1329 of [Vives-Mestres et al., Headache 2022;62:1329–1338, DOI 10.1111/head.14428](https://headachejournal.onlinelibrary.wiley.com/doi/epdf/10.1111/head.14428). Publication affiliation includes Curelator Clinical Statistics. | First metadata/access inquiry for the N1-Headache alcohol-analysis cohort. A corresponding researcher is not automatically the approving data controller. |
| Amparo Casanova, MD, PhD; published correspondence address `acasanova@curelator.com` | Corresponding author of [Casanova et al., Headache 2022;62:1406–1415, DOI 10.1111/head.14328](https://headachejournal.onlinelibrary.wiley.com/doi/10.1111/head.14328). | Related N1-Headache study contact if referred or separately authorized; do not duplicate-send or assume cohorts are independent. |
| Curelator Inc. | Casanova's publication names the company as holder of the data; the Vives-Mestres [author manuscript](https://upcommons.upc.edu/bitstream/handle/2117/384852/headache.pdf?sequence=1) credits company-provided data. | Ask the researcher to identify the current legal controller/custodian, access committee and contracting contact. No present transfer authority has been established. |

The [Vives-Mestres publisher data-availability statement](https://headachejournal.onlinelibrary.wiley.com/doi/10.1111/head.14428) describes written requests by qualified researchers. Casanova's statement likewise provides a request route. Neither is a public raw-data license, a guarantee of eligibility, permission for commercial ML, or permission to obtain the underlying application population. Published anonymization terminology is not a MigraMind re-identification-risk assessment. No raw extract, server journal, data dictionary or DUA has been reviewed.

The target is a new migraine onset within `[cutoff, cutoff + 86,400 seconds)`, using genuinely pre-cutoff information. Published day-defined attack starts, lagged exposures and repeated observations are useful leads but do not establish exact-onset labels or historical feature availability. The original selected analysis population must not be represented as all people with migraine. Do not import that study's imputation, adherence selection or participant-level aggregates into a historical forecasting protocol without independent review.

## Email draft — do not send

To: Marina Vives-Mestres, PhD (published contact above; verify before sending)

Subject: Metadata-first inquiry: N1-Headache longitudinal data for leakage-safe migraine research

Dear Dr Vives-Mestres,

I am [name], [role] at [institution / affiliation]. We are developing MigraMind, currently a research software prototype, and are exploring whether existing longitudinal diary data could support a future offline study of new migraine onset within the next 24 hours. We have not established clinical effectiveness and do not provide predictive risk scores to users.

Your 2022 Headache publication (DOI 10.1111/head.14428) identifies a written-request route for research data. Would you be willing to advise whether a collaboration or qualified-investigator application is possible, and who currently oversees access? We are first requesting a data dictionary, collection/revision protocol and access requirements, not participant records by email.

Our initial feasibility questions concern actual diary submission and edit times, reported symptom times and timezones, onset versus continuing attacks, explicit no-attack observations, missingness, stable participant linkage and usable follow-up. Historical reconstruction is essential: we would exclude outcomes or predictors whose timing and coverage cannot be verified rather than infer headache-free periods from missing entries.

Before any transfer, we would seek the applicable institutional/ethics determinations, permitted-use terms, privacy/security review and data-use agreement. We would propose an approved secure environment with restricted access, no public patient-level release and no external model-service uploads. We would welcome a metadata-only discussion or secure analysis within your environment if transfer is inappropriate.

Could you indicate the qualification criteria, permitted ML research scope, consent/withdrawal restrictions, access process and whether the relevant timestamp/revision evidence is retained? A questionnaire is drafted in our research plan and can be shared after review. We would also welcome discussion of a scientifically appropriate alternative if exact-onset forecasting cannot be supported.

Thank you for considering this inquiry.

[Name, role, institution, institutional email]

[Principal investigator / supervisor and contact, if applicable]

[Reviewed project summary and ethics status; state pending if pending]

Before sending: replace every placeholder truthfully, identify a responsible institution/PI, verify recipient, approve the project summary and obtain explicit outreach authorization. Do not imply an approval, security capability, funding source or institutional affiliation that does not exist. Do not attach exports, participant details or credentials. No follow-up is scheduled automatically.

## Data-access questionnaire

Request answers with dictionary/protocol references, versions and example **synthetic** rows where helpful. Mark each response confirmed, unavailable or unknown; a yes/no attestation alone does not verify source integrity. Metadata first: request disclosure-reviewed, binned aggregate distributions, not participant-level timelines or identifying small cells by email. Sensitive proof may need secure inspection after approvals.

| Area | Questions and evidence requested |
| --- | --- |
| Source and scope | Which release/cohort is available? Is it the published analytic subset, broader consented population or a new extract? What source-system version, collection dates, selection rules and overlap with other N1 studies apply? Can exclusions be audited without future adherence determining earlier eligibility? |
| Longitudinal records | Are participant-level observations available rather than summaries? Provide aggregate participant counts, observed days, calendar span, valid classes and gap distributions per person, including early withdrawals. Can metadata distinguish diaries offered, opened, completed and never submitted? |
| Event versus availability | Which timestamps are participant-reported event/observation times, device times, server receipt, database insertion, update and export? Are offsets, IANA zones, DST ambiguity, travel, clock drift and offline-sync delays retained? Can receipt precede later validation, and when did each field become usable? |
| Historical versions | Are original values and all corrections/tombstones retained with immutable availability anchors? Are deletions, migrations, backfills and bulk imports identifiable? Is history truncated or final-state only? How are simultaneous revisions ordered and unavailable history flagged? |
| Migraine/other headache | What classification/version distinguishes definite/probable migraine, aura-only events and other headaches? Was this algorithmic, participant-reported or reviewed? Obtain the rules and any validation evidence without equating diagnosis with every event. |
| Onset and continuation | Are exact first-symptom/headache/aura onset, recovery, recurrence and ongoing-state times available? What are their uncertainty and verification sources? Is an attack merely consecutive migraine days? Are multiple same-day attacks linked with stable IDs? Can unresolved prior attacks be excluded? |
| Coverage and negatives | Is no attack an explicit answer about a named completed interval, or a default/absence of symptoms? Who confirms full interval coverage and when? Are intervals half-open, continuous and independently reviewed? Can missing, unsure, partial, conflicting and ongoing periods be separated? Do positive windows also have full observation coverage? |
| Verification independence | What evidence independently corroborates reported onset and coverage? Does the reviewer see a separate contemporaneous source or only re-read the same diary? Supply reviewer role, protocol, evidence references, uncertainty, adjudication times and conflict-resolution policy. No sensor or reviewer checkbox is assumed to prove absence. |
| Predictors | Which optional measurements exist, at what temporal resolution and genuine availability? Distinguish baseline from exit surveys, same-day retrospective exposures, post-onset symptoms, treatment response and derived whole-person totals. Are schema/units and missing-value codes stable? |
| IDs and splits | Are stable pseudonyms and a custodian-held identity crosswalk available across device changes and exports? How are duplicate accounts/cohort overlaps recognized without transferring identity? Can time-ordered, horizon-purged within-person and participant-disjoint evaluations be supported? Are shifts in dates person-specific and documented? |
| Snapshot/freeze | Can a versioned as-of journal and release manifest be supplied with hashes, extraction time, historical outcome adjudication and eligibility freezes? Can prior snapshots lawfully be retained, or must withdrawals revoke them? How are later corrections distinguished from information known before cutoff? |
| Authority and consent | Who is controller/custodian and authorized signatory? What participant permission, ethics approval/waiver and secondary-use scope support this specific project? Do geography, vulnerable populations or research/commercial distinctions restrict use? A past study's waiver is not transferable to MigraMind. |
| License and DUA | Are offline ML, derived features, internal models, publication, code sharing, model release and commercial work allowed separately? What prohibits linkage, re-identification, onward transfer, cloud processing or external AI services? What review, costs, collaboration or publication terms apply? |
| Security and lifecycle | What approved storage location, roles, encryption, audit controls, subcontractors, access expiry, incident reporting, retention, withdrawal/deletion and backup rules apply? Can analysis remain in the custodian's environment? What aggregate disclosure controls are required? |

## Decision record and next steps

| Item | Current state | Evidence required / owner to appoint |
| --- | --- | --- |
| Published contact and request route | Verified from publications on 2026-10-27; deliverability unverified | Project lead rechecks before authorized contact |
| Institutional PI, investigator qualification and sponsor | Unresolved | Institution appoints accountable PI and confirms eligibility |
| Custodian identity, permission, DUA and ethics scope | Not established | PI, custodian and institutional privacy/contracts offices |
| Diary journal, exact onset, explicit surveillance and independent evidence | Unverified | Custodian dictionary/protocol and subsequent secure source audit |
| Valid participants, classes, follow-up and leakage-safe evaluation | Not established | Statistician/data steward after lawful metadata/data review |
| Secure transfer/analysis and withdrawal retention | Not approved | Institutional security/privacy owners; no transfer until resolved |

Recommended sequence: internal review of this draft; appoint PI/institution and define scope; separately authorize one metadata-first inquiry; assess questionnaire responses; obtain necessary determinations/agreements; perform an approved secure source audit; then apply the [readiness gate](RESEARCH_READINESS_GATE.md). If immutable availability or reliable outcomes are unavailable, retain NO-GO for strict forecasting and consider a separately named descriptive task. Do not invent timestamps, consent references or verification flags. This sprint does not execute any acquisition step.

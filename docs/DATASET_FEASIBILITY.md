# Sprint 12: real migraine datasets and research feasibility

Assessment date: **2026-10-26**. Branch: `feat/migraine-dataset-feasibility`. Repository inspected at `9411783`, containing merged Sprints 9–11. This is a documentation-only discovery assessment, not a dataset ingestion, experiment, clinical validation or exhaustive systematic review. Sprint 12B additionally inspected the actual public Park workbook outside the repository; see [the workbook audit](PARK_DATASET_AUDIT.md).

## Decision and recommendation

**NO-GO for real-data training/evaluation of the existing next-24-hour onset baseline today. CONDITIONAL GO for obtaining documentation, permissions and a controlled data-quality audit. No candidate is classified Eligible on the evidence verified here.** This does not establish that no suitable dataset exists.

The first public-data audit, **Park et al.'s smartphone headache diary supplement**, is now complete at schema/aggregate level: **Ineligible for the strict onset baseline in its published form**. See [Sprint 12B evidence](PARK_DATASET_AUDIT.md). Recommended permissioned collaboration lead remains **the N1-Headache cohort studied by Vives-Mestres et al.**, subject to access and timing/coverage verification. This is an acquisition recommendation, not approval to fit models. The existing application should continue collecting prospective observations without presenting predictions.

## Existing architecture and compatibility

The following implementations and their documentation were inspected before this assessment:

| Existing component | What it establishes | Consequence for external data |
| --- | --- | --- |
| [Sprint 9 collection](PROSPECTIVE_COLLECTION.md), [collection routes](../backend/app/prospective.py), migration 008 | Source-local dates/zones, event and observation timestamps, original server creation, append-only correction/tombstone snapshots. A same-day no-migraine entry needs explicit post-day reconfirmation. | A final edited CSV with only an event date cannot substitute for known historical versions. Missing reports remain unknown. |
| [Foundation](PERSONALIZED_AI_FOUNDATION.md), legacy readiness | Descriptive quality information; no verified prospective forecast labels. | Diary counts and diagnoses alone do not justify forecasting. Legacy episode/wellness edits lack reconstructable history. |
| [Sprint 10 contract](../backend/research/revision_contract.py), [dataset builder](../backend/research/revision_dataset.py), [baseline gates](../backend/research/baseline_v2.py), [research guide](ML_RESEARCH_BASELINE.md) | Strictly pre-cutoff features; fixed 24-hour horizons; separately frozen outcome adjudication/eligibility; candidate-grid chronological splits and purging; single-account bundles. | Audit real source semantics before any mapping. Do not invent revisions, verification flags, consent references or historical recording times to satisfy a schema. |
| [Sprint 9 projection](../backend/research/sprint9_adapter.py) | Explicit account scope and reviewed consent/provenance requirements; deliberately supplies no verified outcome journal. | Existing app status reports cannot be promoted to externally verified onset evidence. |
| [Sprint 11 quality/export](RESEARCH_DATA_QUALITY.md), [implementation](../backend/app/research_quality.py) | Structural revision checks including creation-time anchoring; explicit local download confirmation; preparation export is not training eligible. | Download consent and caregiver-sharing consent are not research enrollment. A preparation export is not a ready-made research-schema-2 bundle. |

No runtime code, schema, consent mechanism, endpoint, user record or model was changed. The existing baseline is account-isolated: a future population model would need a separately reviewed participant-grouped protocol, not concatenated account bundles.

## Task definition and eligibility gates

The request's **migraine occurrence within the next 24 hours** and the implemented **new episode onset within the next 24 hours** are different targets. Occurrence can include an episode already underway. A next-calendar-day migraine day, moderate headache tomorrow, diagnostic subtype, and persistence of today's attack are also different outcomes.

Recommended primary MigraMind research task: retain **a new, independently adjudicated migraine onset during `[t, t + 86,400 seconds)`**, among cutoffs with no known ongoing/unresolved episode, using information available strictly before `t`. Analyze occurrence/persistence only under a separately named, prespecified protocol. Do not silently change the current baseline to match an available dataset. Calendar days may last 23 or 25 hours; diary dates alone cannot establish arbitrary rolling 24-hour outcomes.

For classification below:

- **Eligible:** verified data access and intended-use permissions, suitable longitudinal rows, auditable prediction-time availability, independently reviewable outcome/coverage evidence and feasible temporal/participant splits.
- **Conditionally Eligible:** credible longitudinal source and a plausible lawful access route exist, but listed conditions still block use. This is not acceptance by the current baseline.
- **Ineligible:** a demonstrated task, resolution, artifact or access mismatch prevents the proposed use in the assessed release.
- **Unverified:** a study/listing is real, but essential raw-data access, permissions or semantics could not be established. A publication does not prove an accessible dataset.

Every gate below must pass before changing that decision:

1. Stable pseudonymous participant IDs and repeated observations with per-person follow-up, event/class counts, gaps and usable coverage distributions—not just a large pooled row count.
2. Predictor event time **and actual availability** before each cutoff. Obtain server submissions, edit histories or documented immutable capture with bounded delays. User-entered backdates and device event times are not availability timestamps.
3. A defensible migraine-specific outcome definition, separate onset/recovery evidence, adjudication method/version and verification provenance. A participant's migraine diagnosis does not verify every subsequent headache as a migraine.
4. Explicit, complete observation coverage for the entire horizon. The existing baseline requires coverage for positives as well as independently verified onset; negatives additionally require complete explicit no-episode intervals. Missing, unknown, incomplete, conflicting, deleted or unverifiable outcomes are excluded, never made negative.
5. A prespecified dataset snapshot, outcome lag/freeze and eligibility time. Later corrections must not rewrite earlier features or select historical training windows using future knowledge. Obtain original chains; final-state-only sources fail when historical availability is unknowable.
6. Chronological within-person evaluation with purged horizon/adjudication overlap. Population generalization additionally requires participant-disjoint evaluation; participant-disjoint random partitions alone do not establish future within-person performance.
7. Dataset-specific permission for the intended secondary analysis, local security controls, retention/withdrawal handling and any required institutional review. Article or notebook licensing is not automatically a raw-data grant.

The baseline's 180-window/180-day span, class-count and split-size gates are **engineering stop rules, not clinically validated sufficiency criteria**. They remain unchanged. Approximately three-month cohorts cannot pass the current single-person span gate; their public counts cannot be interpreted as retained eligible examples.

## Candidate comparison and acquisition ranking

Counts are **source-reported**, except the Park workbook counts independently recomputed in [Sprint 12B](PARK_DATASET_AUDIT.md). Ranking prioritizes useful next steps, not claimed predictive performance. Cohort summaries, different analyses and repositories must not be added together as independent datasets. See the linked candidate notes for evidence and unresolved fields.

| Priority / ID | Candidate and original source | Reported scale / resolution | Access evidence | Primary-task assessment |
| --- | --- | --- | --- | --- |
| 1 / A | [Park SHD, PLOS 2016](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0149577) | 62; 4,579 diary records; daily, 3 months | Original XLS downloaded and inspected; 4,579 rows confirmed, participant linkage conflicts | **Ineligible** published release for strict onset forecasting; descriptive audit only |
| 2 / B | [N1-Headache, Vives-Mestres 2022](https://doi.org/10.1111/head.14428) | 487; 43,830 tracked diary-days | Written request policy in author manuscript | **Conditionally Eligible**, subject to permission and timing/coverage audit |
| 3 / C | [HAPRED, Houle 2017](https://pmc.ncbi.nlm.nih.gov/articles/PMC5950708/) | 95 evaluable; 4,626 diary-days; AM/PM | Study verified; raw release not established | **Unverified** access; headache target mismatch |
| 4 / D | [Nerivio, Rabany et al. 2026](https://www.neurology.org/doi/10.1212/WN9.0000000000000144) | 53,065 users; 770,473 target-days | Publication verified; no raw release verified | **Unverified** access/availability; not proof of personalization |
| 5 / E | [Stubberud et al. 2023](https://discovery.ucl.ac.uk/id/eprint/10168944/) | 18; 388 diary entries | Institutional publication record, not a dataset grant | **Unverified** raw access and semantics |
| 6 / F | [mBrain, De Brouwer et al. 2022](https://link.springer.com/article/10.1186/s12911-022-01813-w) | 18 in two waves; 14 migraine, 4 cluster headache | Privacy-based nonpublic-data statement | **Ineligible** under current public access; collaboration requires new approval |
| 7 / G | [OPORA diagnostic study, Zenodo 19353040](https://zenodo.org/records/19353040) | 35; 1,134 episodes; approximately 10 months | Deposited file is a results PDF | **Ineligible** deposited artifact; underlying records **Unverified** |
| 8 / H | [BioCer, Faisal et al. 2026](https://link.springer.com/article/10.1186/s10194-026-02346-7) | 146; 21,550 next-day examples | Explicitly unavailable publicly **and upon request** | **Ineligible** under stated access policy and target definition |
| 9 / I | [BE-HOME, Zenodo 11125372](https://zenodo.org/records/11125372) | N not established from deposit; baseline/months 3, 6, 12 | Restricted files; visit-level variables described | **Ineligible** resolution; restricted access |
| 10 / J | [Kaggle migraine classification](https://www.kaggle.com/datasets/weinoose/migraine-classification), traced to [Sanchez-Sanchez et al.](https://f1000research.com/articles/9-618/v2) | 400 retrospective medical-record rows; 24 variables | Original article names Code Ocean release; Kaggle copy not independently matched | **Ineligible** forecasting; mirror integrity **Unverified** |
| 11 / K | [OpenNeuro ds005016, MBSR v1.1.3](https://openneuro.org/datasets/ds005016/versions/1.1.3) | 147; up to 3 imaging sessions | Official repository README and dataset description available | **Ineligible** for daily forecasting |
| 12 / L | [PhysioNet MIMIC-IV v3.0](https://www.physionet.org/content/mimiciv/3.0/) | 364,627 parent-cohort individuals; irregular EHR | Credentialing, training and DUA required | **Ineligible** for community migraine onset/negative coverage |

### A. Public-data recommendation: Park smartphone diary

The [paper's Supporting Information](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0149577) explicitly identifies an [S1 XLS dataset](https://doi.org/10.1371/journal.pone.0149577.s001), not merely a catalogue keyword match. Participants actively answered whether headache was present; headache-free responses and missing diary days were distinguished. Symptoms/intensity/duration, medication and same-day reported exposures were collected; recorded headaches were algorithmically classified. The publisher links CC BY 4.0.

**Sprint 12B verified workbook evidence:** the original publisher XLS was retrieved (5,764,608 bytes; SHA-256 and reproduction steps in [PARK_DATASET_AUDIT.md](PARK_DATASET_AUDIT.md)). Its three sheets contain 62 cohort records, 1,099 headache records and 4,579 total diary records. The total sheet includes 3,480 explicit no-headache responses with blank migraine classification, but also 11 no-headache/classification conflicts, 86 missing no-headache flags and 262 ongoing-headache reports. Reported start/end timestamps exist; they are event times, **not submission timestamps**. Four paired intervals end before they start. Diary registration IDs number 63 (total) and 64 (headache), versus 62 in the cohort, and C identifiers also fail simple cross-sheet linkage. No IDs were guessed or merged.

**Revised classification: Ineligible / NO-GO for the current next-24-hour onset baseline.** There is no diary-level receipt/revision journal, documented timezone, independently verified new-onset evidence or complete rolling-horizon coverage. Participant-level registration/modification dates do not repair those gaps. Maximum raw registration-ID-group span is 127 days, below existing engineering gates; this is not a clinical sufficiency judgment. Calendar-day labels and algorithmic migraine classification cannot be promoted to verified incident-onset labels. Conditional descriptive association work would require identity/coding reconciliation and privacy review; same-day factors are not proven causal triggers or pre-cutoff features.

The associated [Figshare item 2733109](https://figshare.com/articles/dataset/The_Number_of_Trigger_of_each_Recording_Day_with_and_without_Headache_/2733109) is a table asset with CC BY 4.0 metadata, **not another participant-level cohort**. Do not substitute it for the workbook. Original reference: Park et al., PLOS ONE 11:e0149577, DOI above.

### B. Permissioned recommendation: N1-Headache / Curelator

[Vives-Mestres et al., Headache 2022, DOI 10.1111/head.14428](https://doi.org/10.1111/head.14428), and the [institution-hosted author manuscript](https://upcommons.upc.edu/bitstream/handle/2117/384852/headache.pdf?sequence=1), describe 90 tracked days within 120 calendar days, symptom-based migraine classification and first days of consecutive-day attacks. Embedded missing days and incomplete covariates are acknowledged. The manuscript offers data to qualified researchers by written request.

Predictors include daily alcohol reports and lagged headache information; exact intake time was not collected. Participant-level analyses establish study linkage, not the contents of an obtainable export. **Require** explicit non-migraine coverage codes, original submissions/revisions, timezone and adjudication evidence. A day-defined attack start is not automatically an exact onset instant.

No raw-data license or actual access approval was verified. Article access is not that permission. Selection of alcohol consumers limits generalizability. This is **N1-Headache**, not Migraine Buddy. No request was sent and no records were obtained.

### C. HAPRED methodological lead

[Houle et al., Headache 2017;57:1041–1050, DOI 10.1111/head.13137](https://pmc.ncbi.nlm.nih.gov/articles/PMC5950708/), report presence/absence questions since the preceding diary and evening stress measurement. Follow-up ranged 11–96 days; 431 days were missing/unusable, including final-day cases. The outcome was **any headache pain above zero** over the 24 hours after an evening diary, including continuation—not independently verified new migraine onset.

Identifiers support the paper's per-person analysis, but export IDs, original capture times, revision retention, row-level completeness, raw release and reuse license remain unverified. Stress information is potentially available at the evening cutoff only if actual submissions confirm this. Published validation does not demonstrate MigraMind's required chronological personalized evaluation. Investigator contact is a possibility, not a verified access promise. Current short per-person series would fail the baseline span gate.

### D. Large-scale app evidence: Nerivio

[Rabany et al., Neurology Open Access 2026;2:e000144](https://www.neurology.org/doi/10.1212/WN9.0000000000000144), report January 2020–July 2025 data, explicit next-calendar-day occurrence/absence reports, diary/pretreatment symptoms, demographic and weather predictors, and participant-disjoint partitions. Mean usable target-days per user was only **14.52**. The calendar label is not verified incident-onset timing.

Raw availability, dataset license, exported IDs and edit/submission histories could not be verified. Treatment-triggered entries and symptom-dependent missingness need audit; a no-migraine report does not by itself prove complete horizon surveillance. Weather must have been available at prediction time, not retrospectively retrieved future observations. Device-study consent does not grant MigraMind permission. Personalization requires actual per-person coverage/class distributions, not pooled scale. No clinical performance claim from this paper is adopted here.

### E. Small wearable/diary pilot

The [UCL institutional record](https://discovery.ucl.ac.uk/id/eprint/10168944/) verifies Stubberud et al., *Forecasting migraine with machine learning based on mobile phone diary and wearable data*, Cephalalgia 2023, [DOI 10.1177/03331024231169244](https://doi.org/10.1177/03331024231169244). Reported predictors include diary observations and biofeedback heart rate, skin temperature and muscle tension.

Per-person usable follow-up, timestamp/availability fields, exported identifiers, explicit negative coverage, missingness codes, independent onset review, raw access and dataset reuse terms were not verified from that record. Repeated measures are reported, but personalized feasibility and the baseline's sufficiency gates cannot be inferred. A freely readable manuscript is not permission to access or reconstruct its raw patient dataset. Ask investigators for protocol/schema/access information before any acquisition.

### F. mBrain privacy-limited physiological monitoring

[De Brouwer et al., BMC Medical Informatics and Decision Making 2022;22:87](https://link.springer.com/article/10.1186/s12911-022-01813-w), describe unique patient IDs, wearable physiological streams, contextual events, edited/confirmed app entries and headache classifications. They report 98 headache events in migraine participants and 35 in cluster-headache participants. Two collection waves are described; exact usable days/person and row counts were not independently established here.

Wearable dropout and limited event feedback are reported. Physiological coverage is not explicit migraine-free observation coverage. Requested event time, server availability and correction chains must be distinguished. The authors state that privacy/ethics restrictions prevent public release; the openly available **DAHCC ontology is not the health dataset**. No raw-data license or collaboration approval was obtained. Potential within-person study design does not remove these barriers or establish verifiable negatives.

### G. Zenodo OPORA: report versus rows

[Broeker et al., Zenodo, published 31 March 2026](https://zenodo.org/records/19353040), describe daily diaries, questionnaires and wearable physiology in a prospective study. The verified file inventory contains **Diagnostic Study Results.docx.pdf**, not a longitudinal patient table. A record labeled “Dataset” therefore does not establish usable row-level access.

Raw participant IDs, exact diary coverage, missing-day coding, onset/negative verification, recording/edit times and usable individual histories are unverified. A license value was not readable in the retrieved landing-page rights section; metadata API access failed, so do not assume a raw-data reuse grant. The report may inform hypotheses about symptoms or severity, but cannot support an executable forecast dataset. Request a dictionary, access policy and underlying-record availability from the named creators before reconsidering the raw cohort. Peer-reviewed publication status was not established for this deposited report.

### H. BioCer: real cohort, unavailable dataset

[Faisal et al., Journal of Headache and Pain 2026;27:91, DOI 10.1186/s10194-026-02346-7](https://link.springer.com/article/10.1186/s10194-026-02346-7), report daily diary and wearable biofeedback data, with missing following-day diaries excluded. Their primary target is next-calendar-day **moderate-to-severe headache**, not incident migraine onset. Continuation is included in the main task. Do not reinterpret below-threshold headache as explicit migraine-free coverage.

The authors explicitly state that the sensitive minimum dataset is neither public **nor available upon request**; only analytical code may be requested. Article open-access terms do not override that restriction. Per-person raw IDs, revisions and availability cannot be inspected here. Do not download a mirror or suggest a routine data request contrary to the published policy. Population/per-person performance cannot be independently evaluated by MigraMind from this release.

### I. Zenodo BE-HOME: visit-level treatment outcomes

[Zenodo 11125372](https://zenodo.org/records/11125372), linked to [Grazzi et al., Neurological Sciences 2024;45:4923–4930, DOI 10.1007/s10072-024-07568-8](https://pubmed.ncbi.nlm.nih.gov/38771524/), describes headache frequency, medication intake and questionnaires at scheduled visits. Deposit files are restricted.

Participant count, individual row count, stable IDs, missingness and raw diary availability were not established from the deposit. The exposed variable description contains no daily onset or explicit full-day negative journal and no historical predictor availability. A year of follow-up does not imply day-level temporal resolution. The retrieved rights section did not expose a verifiable license value; institutional authorization and exact secondary-use terms remain unresolved. The described release may address longitudinal treatment/burden questions, but cannot supply next-24-hour outcomes or personalized forecasting features.

### J. Kaggle provenance: diagnostic classification, not forecasting

The [original F1000Research article](https://f1000research.com/articles/9-618/v2) traces the retrospective records to Hospital Materno Infantil de Soledad, first quarter 2013. It identifies a [Code Ocean capsule, DOI 10.24433/CO.2826453.v1](https://doi.org/10.24433/CO.2826453.v1), with `Migraine.cvs` and a description, and states CC BY 4.0 for underlying data. Features are symptoms/demographics; the target is one of seven diagnostic types.

[weinoose](https://www.kaggle.com/datasets/weinoose/migraine-classification) and [ranzeet013](https://www.kaggle.com/datasets/ranzeet013/migraine-dataset) are candidate mirrors. Their present file identity/checksums and dataset-specific terms were not verified; neither mirror nor capsule rows were downloaded. Original study provenance is established, **mirror equivalence is not**. No repeated dated diary, explicit migraine-free windows, stable longitudinal IDs, recording-time history or missingness semantics was established. Attack duration/current symptoms cannot be repurposed as future-onset labels. The Zenodo STARD checklist linked by the article is reporting guidance, not additional patient data.

### K. OpenNeuro MBSR: longitudinal imaging is not diary coverage

The official [README](https://raw.githubusercontent.com/OpenNeuroDatasets/ds005016/master/README.md) describes patients/controls and incomplete imaging sessions. The official [dataset description](https://raw.githubusercontent.com/OpenNeuroDatasets/ds005016/master/dataset_description.json) identifies snapshot DOI `10.18112/openneuro.ds005016.v1.1.3`, CC0, and [Seminowicz et al., Pain 2020, DOI 10.1097/j.pain.0000000000001860](https://doi.org/10.1097/j.pain.0000000000001860).

BIDS subject/session identifiers permit subject grouping; missing scans are documented. No released daily onset/negative diary or pre-cutoff diary availability was verified. Diagnostic group and healthy-control status cannot label a migraine patient's unobserved future day. Imaging acquisition times are not submission histories for daily predictors. This release can support appropriately scoped imaging/treatment analyses, not the intended forecasting task. The dynamic OpenNeuro page exposed no readable content; the official repository metadata supplied the evidence. CC0 metadata does not itself establish privacy safety for a proposed linkage.

### L. PhysioNet: MIMIC-IV is not a migraine diary

The [official v3.0 project](https://www.physionet.org/content/mimiciv/3.0/) documents hospitalization/ICU observations, `subject_id`, patient-specific date shifts, and the PhysioNet Credentialed Health Data License/DUA 1.5.0. The count in the table is the **whole database**, not a migraine cohort; migraine-specific N and qualifying windows were not determined. Version is pinned for this assessment, not claimed latest.

EHR measurements have irregular event/documentation times and care-dependent missingness. Migraine diagnosis codes do not verify attack onset; absent codes or absent encounters do not show no migraine. Within-person date intervals may be useful, but shifted dates are not comparable real calendar dates across patients. No community full-horizon negative coverage is established. Access requires credentialing, specified CITI training and a signed DUA. This is a repository search counterexample, not a recommendation to obtain restricted records for this task.

## Research-task feasibility

These are assessments of study design and available evidence, **not experiments run by MigraMind**. Publicly readable results from a restricted cohort do not make its task reproducible here.

| Task | Best leads / available evidence | What is supportable now |
| --- | --- | --- |
| Population-level next-24-hour forecasting | B for access audit; C/D/E methodological leads; A release ruled out | No verified eligible training dataset. Require participant-disjoint testing plus temporal validation; don't apply the single-account baseline to pooled people. |
| Personalized next-24-hour forecasting | B repeated diaries; C repeated AM/PM data; A release ruled out | Conditional acquisition/audit only for unresolved candidates. Recompute eligible observations and class counts per person after purging. Short follow-up and sparse reporting may make most individuals unevaluable. |
| Early-warning symptom modeling | D/E/F/G describe relevant data collection | Not currently reproducible from verified accessible rows. Require symptom capture before adjudicated onset, negative/control periods and distinguishing prodrome from an attack already underway. |
| Reported-factor association analysis | A workbook inspected; B is request-only | Descriptive or within-person association analysis is plausible after A identity/coding reconciliation and privacy review, or B access review. Same-day retrospective exposures cannot establish direction or causal triggers. |
| Migraine severity prediction | A contains recorded intensity; D/G/H report symptom/intensity collection | Observed-severity description may be possible after data-quality and permission review. Forecasting future severity additionally needs a prespecified at-risk target, pre-cutoff predictors and handling of days without an episode. Current-attack symptom classification is not future severity prediction. |

Cross-sectional J and sparse imaging K cannot acquire temporal forecasting labels through relabeling. Encounter-based L cannot fix missing community observation coverage by adding more diagnosis codes. For all tasks, medication, treatment allocation, symptom-driven logging and cohort selection can confound associations and change the deployment population.

## Acquisition and privacy plan

1. **A: follow up the completed workbook audit.** [Sprint 12B](PARK_DATASET_AUDIT.md) verified public access and actual schema/aggregates. Obtain an author-validated ID crosswalk, bilingual dictionary, contradiction reconciliation, diary availability/revision journal, timezone and separately verified outcome/coverage evidence before reconsidering forecasting. The published release alone is NO-GO. No patient workbook or derived patient rows belong in Git.
2. **B: prepare, do not send, a qualified research request.** Seek the earliest recorded submissions, revisions, pseudonymous IDs, complete observed/missing calendars, outcome rules, and written permission for forecasting reuse. The paper's data-request policy is evidence of a route, not a grant. Reject any final-only extract whose pre-cutoff information cannot be reconstructed.
3. **C/D/E: request availability and dictionary clarification before choosing them.** No public raw release or applicable permission was verified. Do not assume open-access publication or app terms authorize transfer to this repository. Do not pursue H as “available on request”; the source says otherwise.
4. Keep any approved records in separate access-controlled storage with a dataset-specific retention and withdrawal plan. Do not place patient rows, exact individual timelines, credentials or restricted derivatives in Git or test fixtures. Assess re-identification risk from dates, location and linkages; pseudonymous IDs do not automatically make data anonymous.
5. Respect dataset restrictions on redistribution and processing services. PhysioNet specifically explains limits on sending credentialed data to third-party services; see its [responsible-use guidance](https://www.physionet.org/news/post/gpt-responsible-use/). No restricted records were requested or downloaded in this sprint.
6. Use source-reviewed permissions. CC BY 4.0 requires attribution and change notices; CC0 is a different grant. Neither replaces a check of participant consent, permitted linkage and institutional requirements. Unreadable or unspecified license fields remain **unverified**, not permissive defaults. See the publisher-linked [CC BY 4.0 terms](https://creativecommons.org/licenses/by/4.0/).

No author, participant or data controller was contacted. Additional author requests or controlled-data acquisition require a later explicit decision; no research enrollment or data access approval was fabricated. The public Park supplement was inspected locally only for the documented audit.

## Leakage-safe evaluation requirements after access

- Freeze raw versions, dictionaries, consent/use authorization, label definitions, timezone policy, source-code versions and dataset hashes. Preserve a separate source-to-research provenance map securely; never put identities in logs.
- Audit actual event time, submission time, correction time and label availability. If a diary allows retrospective entries but historical submissions are unavailable, exclude affected windows instead of assigning arbitrary recording times.
- Define the cutoff/at-risk schedule before inspecting outcomes. Exclude ongoing/unresolved episodes for the existing onset task. Maintain separate current truth, frozen adjudication and historical eligibility; late corrections cannot silently veto older retained windows.
- Require independently reviewable source evidence for outcomes and full observation coverage. “No report”, a below-severity-threshold headache, an interictal scan, a healthy participant and “no diagnosis code” are not interchangeable negatives.
- Rebuild rolling aggregates only from prior available information. No whole-study person means, final attack duration, post-treatment response, future session counts, target-day symptom criteria or retrospectively observed future weather as pre-cutoff predictors. Weather forecasts need their historical issue time.
- Choose train/validation/test boundaries on the planned candidate grid, not retained outcomes. Purge overlapping horizons and adjudication lags; address overlapping multi-day episodes and serial dependence. Fit preprocessing and any resampling on training data only. Unknown labels must not be repaired by SMOTE or imputation.
- For population research keep participants separate where required; for personalization distinguish a predeclared warm-up from future held-out observations. Do not learn participant-specific effects from their future records. A participant-disjoint result is not proof of chronological within-person forecasting.
- Report candidate and eligible counts, exclusions, per-person coverage/classes, base-rate and naive comparators, PR-AUC where defined, Brier score and calibration. Insufficient/single-class series yield no manufactured metrics. Engineering gates require explicit research review before alteration; no clinical power or readiness claim follows from them.

## Collection alternative and final next step

If external journals cannot pass the gates, the defensible route is an approved prospective study built on Sprint 9–11: genuine research enrollment, a low-burden completed-day observation protocol, separately recorded exact onset/recovery evidence, documented independent adjudication, real availability/correction timestamps, explicit unknown/missing intervals, timezone-aware coverage and withdrawal/retention controls. Participant burden and migraine-time accessibility need protocol review. Determine duration and sample size through an appropriate design/power assessment, not by treating existing code constants as clinical requirements.

The **immediate primary activity** is Park author clarification and an N1-Headache metadata/permission audit; the Park public-release audit is complete and does not support baseline training. A later exploratory next-local-day occurrence or association study may be warranted if the evidence supports it, but must be named separately from the fixed-elapsed-24-hour incident-onset task. Today: **no real-data fit, no adapter, no clinical prediction claim**.

## Search coverage, evidence limits and validation

Repository-specific searches covered PhysioNet, Kaggle, Zenodo, Figshare and OpenNeuro, followed by original publisher/institutional records and supplementary-file inventories. Terms included migraine, diary, forecasting, longitudinal, onset, data availability and the cohort names. This was a targeted discovery exercise; absent results do not prove absence of datasets. PhysioNet hits were largely general EHR resources rather than verified prospective migraine diaries.

Browsing was available, but not uniformly: some publisher/PMC pages returned bot checks/403s, PhysioNet direct opens timed out while its indexed project metadata was readable, Kaggle returned inaccessible/empty pages, and the OpenNeuro interface required client rendering. Official repository text supplied the OpenNeuro evidence. Some findings rely on indexed **primary-source** text, explicitly not on mirror downloads. Direct public Zenodo/Figshare metadata API attempts also failed; their missing license fields were not guessed. Supplement titles and publication counts were checked for the discovery assessment. Sprint 12B subsequently inspected Park's actual workbook headers and recomputed aggregate counts/missingness outside the repository; other candidate binaries remain uninspected. No participant rows or identifiers are reproduced in documentation. The report does not claim independent verification of authors' raw data, diagnoses, licenses of uninspected mirrors or clinical findings.

Only this Markdown report and [the Park audit](PARK_DATASET_AUDIT.md) are added. No optional metadata utility was implemented: the existing revision contract already validates known research-schema fields, while the unresolved external semantics/access questions cannot be solved by a speculative validator or adapter. No patient workbook, restricted record, model artifact, patient-level data extract or new application dependency was added to the repository. No training, inference, database migration, endpoint or UI change occurred.

Validation: runtime/backend/frontend/Playwright/build suites were **not rerun for these documentation-only changes**, and no earlier pass counts are represented as new results. Sprint 12B repeated read-only workbook aggregate checks and checked documentation links, whitespace and changed-file scope. The Sprint 12 publication scope is limited to `docs/DATASET_FEASIBILITY.md` and `docs/PARK_DATASET_AUDIT.md`. Publication is authorized after final review; merging remains a separate decision.

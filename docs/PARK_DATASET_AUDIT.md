# Sprint 12B: Park smartphone diary workbook audit

Audit date: **2026-10-26**. Branch: `feat/migraine-dataset-feasibility`.

## Verdict

**NO-GO: the published workbook is Ineligible for MigraMind's current prospective next-24-hour incident-migraine-onset baseline.** The actual public workbook was retrieved and inspected, not merely its catalogue description. It contains longitudinal daily observations, explicit no-headache answers and reported headache start/end times. However, it does not establish diary submission availability, historical revisions, independently verified onset or complete rolling-horizon surveillance. Identifier and outcome contradictions also require clarification. No model was trained and no eligible sample count or performance metric was manufactured.

**CONDITIONAL GO for a separately specified descriptive diary/association study**, after identifier reconciliation, coding clarification, privacy review and a prespecified exclusion policy. Such a study would concern reported days and associations, not prospectively validated forecasting or causal triggers. A future author-supplied availability/outcome journal would be a different, newly audited dataset.

## Provenance, access and permissions

- Original publication: Park J-W, Chu MK, Kim J-M, Park S-G, Cho S-J (2016), *Analysis of Trigger Factors in Episodic Migraineurs Using a Smartphone Headache Diary Applications*, PLOS ONE 11(2):e0149577, [article and methods](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0149577).
- The publisher's Supporting Information identifies S1 as the patient/headache/all-diary XLS dataset. [Supplement DOI](https://doi.org/10.1371/journal.pone.0149577.s001); [stable direct download](https://journals.plos.org/plosone/article/file?id=10.1371/journal.pone.0149577.s001&type=supplementary). This is the original publisher attachment, not a Kaggle mirror or a Figshare table image.
- An unauthenticated publisher download succeeded (HTTP 200, `application/vnd.ms-excel`), redirecting to publisher storage at `storage.googleapis.com/plos-corpus-prod/10.1371/journal.pone.0149577/1/pone.0149577.s001.xls`. Transient signed redirect parameters are not part of the citation or dataset identity.
- Retrieved file: `pone.0149577.s001.xls`, **5,764,608 bytes**, OLE/BIFF8 Excel workbook, 1900 date system. SHA-256: `b492489aa6f98aaac56df319e09f2472d9539831dc3999c186abd2c0af94f11f`. This identifies the inspected bytes; it is not proof of clinical validity or historical capture integrity.
- The article links [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); [PLOS licensing policy](https://journals.plos.org/plosone/s/licenses-and-copyright) supplies the publisher reuse context. Preserve attribution, source, license and change notices. No separate restrictive notice was identified in the inspected worksheet headers. An exhaustive legal review of every embedded workbook object was not performed. Public availability and copyright permission do not establish individual secondary-research consent, privacy clearance or institutional approval. Those remain unverified for a MigraMind research protocol.

Only schema and aggregate findings are recorded here. The workbook and temporary parser were kept outside the repository. No participant identifiers, individual timelines, patient rows, workbook, derived patient-level extract or model artifact are included in the change. No authors were contacted or restricted data requested.

## Inspection method and row selection

The binary was read locally with `xlrd==2.0.2`, loaded from a temporary wheel without installing an application dependency. Counts below were recomputed from cells. Excel row/column references are one-based. Headers occupy rows 1–2 in the cohort sheet and rows 1–3 in diary sheets. Select data rows after those headers with nonempty columns B and C; diary rows additionally have numeric A. Do not use worksheet dimensions as record counts: sheets include auxiliary/summary rows. Do not require numeric A on the cohort sheet: 30 of its 62 records have text A.

| Sheet, exact name | Physical dimensions | Selected records | Data scope and types |
| --- | --- | --- | --- |
| `62patients` | 134 rows × 185 columns (A:GC) | 62 | Participant baseline, treatment, study-end surveys and derived totals. Mixed text/numeric/date cells; not a diary submission journal. |
| `headache diary 1099` | 1,103 × 101 (A:CW) | 1,099 | Headache-day detail, symptom-derived migraine flag, reported timing, medication, function, exposures and ongoing/no-headache flags. Text/numeric/empty cells; no Excel date-typed cells in selected rows. |
| `total diary 4579` | 4,594 × 105 (A:DA) | 4,579 | All submitted diary days, including explicit no-headache reports; same broad clinical fields plus helper columns. Text/numeric/empty cells; no Excel date-typed cells in selected rows. |

Diary numeric dates are encoded numbers, not timezone-aware instants. Empty cells and zero-length text both occur. A numeric zero is not missing, and a blank migraine flag is not a negative label. Korean header translations below are working interpretations; an author-validated dictionary, units and coding rules remain necessary. This is a schema audit, not a validated adapter for every helper column.

## Relevant actual columns

| Meaning / original header | Cohort | Headache sheet | Total diary | Observed representation / limitation |
| --- | --- | --- | --- | --- |
| Registration identifier, `등록번호` | B | B | B | Text; useful candidate grouping key, but mismatch counts below block a validated participant join. |
| Study/unique identifier | C (`연구번호`) | C (`고유번호`) | C (`고유번호`) | Text; different header meanings and incompatible value sets. Do not assume interchangeable IDs. |
| Serial number, `번호` | A (`고유번호`) | A | A | Not a unique diary key: 1,005 distinct A values in headache sheet, 3,157 in total sheet. |
| Reported start, `시작시간` | — | D | E; F helper | Numeric `YYYYMMDDHHMM`; total F is text hour helper or empty text, not submission time. |
| Reported end, `종료시간` | — | E | G; H helper | Numeric `YYYYMMDDHHMM`, blank or text `N`; total H is text hour helper or empty text. Meaning of sentinel `N` needs confirmation. |
| Duration, `지속시간` | S is baseline hours/episode | F; G largely empty helper | I text; J numeric minutes | Text duration versus derived minutes needs reconciliation; do not repair invalid intervals from duration. |
| Diary date, `날짜` | — | H | K | Numeric `YYYYMMDD`, all selected diary rows parse as dates. Not an entry timestamp or proof of completed-day coverage. |
| Severity / intensity | T:U baseline | I category; J derived flag; K `Pain intensity(VAS)` | L category; M derived flag; N `지수` | VAS available in 993 rows (1–10), absent in 106 headache rows. Binary intensity helpers must not be mistaken for VAS. |
| Pain location/quality, aggravation and symptoms | V:AC baseline | L:AI | O:AL | Text plus numeric component/derived flags; target-defining symptoms are not pre-onset predictors. |
| Migraine criteria and classification | N:O baseline diagnosis | AJ:AK criteria; AL `편두통유무` | AM:AN criteria; AO `편두통유무` | Symptom-derived 0/1 classification; blank on most no-headache days. Not independent event adjudication. |
| Medication, functional effects | Baseline and follow-up fields | AM:BF | AP:BH | Includes downstream responses/disability; not automatically known before onset. |
| Same-day exposures and helper counts | Baseline/final survey and totals | BG:CH | BI:CJ | Text and numeric flags/sums; reporting time and exposure sequence absent. |
| Relief and exercise | Baseline/final fields and totals | CI:CU | CK:CY | Text/numeric flags and durations; coding and availability require dictionary. |
| No-headache day, `두통이없는날` | — | CV | CZ | Text `Y`, `N` or blank; contradictions below. |
| Headache ongoing, `두통지속중여부` | — | CW | DA | Text `Y`, `N` or blank; no stable attack-linkage journal. |
| Study/recording start; study end | L:M; CB | — | — | Mixed cohort formats; dates do not establish availability of any daily report. |
| Recording time, `기록시간` | CV | — | — | Text survey response about recording behavior, not an event-level timestamp. |
| Registration/modification date, `등록날짜` / `수정날짜` | DH:DI | — | — | Participant-level Excel datetimes in part of the cohort; not per-diary creation/revision records. |
| End surveys, adherence and aggregate totals | CB:GC, including DK:DO | — | — | Whole-study information must not enter historical features or outcome-dependent selection. |

The cohort also contains demographics, anthropometry, diagnosis, baseline burden and therapy; these are not proven immutable pre-enrollment predictors simply because they appear on a baseline sheet. The workbook has no separate diary creation, server receipt, revision, tombstone, timezone or adjudication sheet/column identified in the inspected schema.

## Recomputed identity, time and completeness findings

### Participant linkage and temporal span

| Aggregate | Cohort | Headache sheet | Total diary |
| --- | --- | --- | --- |
| Distinct registration IDs (B) | 62 | 64 | 63 |
| Distinct C identifiers | 62 | 65 | 64 |
| B IDs not found in cohort B | — | 2 | 1 |
| C IDs not found in cohort C | — | 33 | 32 |
| Cohort C IDs absent from sheet C | — | 30 | 30 |
| B IDs mapping to more than one C | 0 | 1 | 1 |
| Reported diary-date range | — | 2014-08-13 to 2015-04-10 | 2014-08-13 to 2015-04-14 |
| Unique recorded days per B group, min / median / max | — | 1 / 15 / 60 | 12 / 75 / 108 |
| Inclusive first-to-last diary-date span per B group, min / median / max | — | 1 / 75 / 125 days | 14 / 84 / 127 days |

ID counts are unchanged by Unicode NFKC normalization and trimming surrounding whitespace. Therefore a trivial whitespace fix does not explain the mismatch. These are **identifier groups, not a verified count of distinct human participants**. All cohort B IDs appear in both diary sheets. The extra IDs and C mappings require the author's crosswalk; no aliases were guessed or merged.

There are **zero duplicate (B registration ID, diary date) keys** within each selected diary sheet. This does not prove absence of duplicate humans/attacks across identifiers. Across total-diary B groups, first-to-last-date envelopes contain **484 unrecorded dates**. This is a diagnostic under unresolved raw grouping, not an enrollment-adjusted missingness rate. Enrollment edges, reporting delays and reasons for missingness are not established by that calculation. The two diary sheets also disagree by one classified headache row: 1,099 versus 1,098. Neither sheet is silently chosen as authoritative.

The pooled multi-month date range must not be used as a person's follow-up. Even the longest raw total-diary group spans only 127 days and has at most 108 records; none meets the current baseline's 180-day/180-window engineering gates. Class sufficiency and retained forecast windows cannot be established before identity and label validity. Those gates are not clinical sample-size requirements.

### Explicit no-headache answers versus unknown outcomes

The total sheet's CZ flag contains **3,491 `Y`, 1,002 `N`, 86 blank**. DA contains **262 `Y`, 4,231 `N`, 86 blank**. AO migraine classification contains **336 ones, 762 zeros, 3,481 blanks**.

| Joint state in total diary | Rows | Interpretation for this audit |
| --- | --- | --- |
| No-headache `Y`, ongoing `N`, migraine flag blank | 3,480 | Explicit headache-free response evidence, not missing-by-absence. Still no proof of a full completed day, receipt time or independently verified 24-hour interval. |
| No-headache `Y`, ongoing `N`, migraine flag 0 / 1 | 9 / 2 | **11 conflicting rows**; exclude pending source clarification, never overwrite one field from another. |
| No-headache `N`, ongoing `Y`, migraine flag 0 / 1 | 165 / 97 | **262 ongoing-headache reports**; cannot count each as a new onset. |
| Both flags blank, migraine flag 0 / 1 | 52 / 33 | **85 classified rows with incomplete flags**, not explicit headache-free coverage. |
| Both flags and migraine classification blank | 1 | Unknown/incomplete, not a negative. |

Remaining rows have no-headache `N`, ongoing `N`: 536 non-migraine and 204 migraine classifications. A non-migraine headache is not an explicit no-episode surveillance interval for the entire horizon. All missing dates, blank flags and incomplete rows remain unknown. The paper describes an explicit headache question; its no-headache branch is an active response, not inference from nonresponse. That protocol does not resolve these workbook contradictions or establish after-day confirmation. See the [original collection method](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0149577).

### Event time, ongoing attacks and availability

Strict parsing of the numeric timestamp fields gives:

- Headache sheet: **1,099 valid reported starts**, **1,032 valid reported ends**, **61 blank ends**, **6 `N` ends**.
- Total diary: **1,098 valid reported starts**, **1,032 valid reported ends**, **3,541 blank ends**, **6 `N` ends**. Its 1,099 text-duration rows do not all have a start timestamp.
- Each sheet contains **4 end-before-start intervals** and **1 zero-length interval** among paired valid timestamps. No paired valid interval reaches 24 hours. That last observation does not prove attacks cannot span days: ongoing flags and reporting structure prevent that inference.
- All valid starts have the same calendar date as their row's diary date. This is consistency of reported event dates, **not evidence of entry time**.

Reported starts could be useful for studying reported timing after clarification, but no per-attack ID, reliable recovery/recurrence rule or independent source journal establishes that every start is a new migraine attack. The ongoing flag explicitly shows continuation. Other headaches are distinguished by an algorithmic migraine flag, not independently verified onset adjudication. Missing ends, conflicts and missing flags prevent safe reconstruction of the at-risk state.

No timezone/offset or diary receipt/edit history was identified. Country/site is not a substitute for a documented timezone. The cohort's DH/DI fields cannot be copied onto daily records: these concern the participant row, and include registration/modification dates after some study events. In the 32 Excel-date-typed cohort rows, DH ranges 2015-01-13 to 2015-01-28 and DI 2015-01-20 to 2015-04-15; remaining cohort date representations are mixed and were not normalized into inferred capture times. Survey recording-time categories likewise cannot timestamp daily submissions. Publication date and this audit's download time are dataset-access times, not historical feature availability.

Consequently it is not possible to verify that yesterday's recorded exposure was already known at today's cutoff, how late entries were handled, what values preceded a correction, or when an outcome became adjudicable. No arbitrary lag, midnight assignment or retrospective sorting repairs this evidence gap.

## Eligibility checks against the existing baseline

The inspected [dataset builder](../backend/research/revision_dataset.py), [contract](../backend/research/revision_contract.py), [baseline gates](../backend/research/baseline_v2.py) and [research policy](ML_RESEARCH_BASELINE.md) remain unchanged.

| Requirement | Finding | Decision |
| --- | --- | --- |
| Authentic accessible release | Original publisher XLS successfully retrieved and hashed | PASS for provenance/access |
| Repeated longitudinal reports | Actual diary rows and dates exist; identity reconciliation unresolved | PARTIAL; chronological sorting is possible only under provisional raw grouping |
| Features available strictly before cutoff | Reported event dates/times, no diary receipt/edit chain | FAIL for historical reconstruction |
| Independently verified incident migraine onset | Symptom-derived migraine flag, reported starts, ongoing reports; no independent evidence journal | FAIL |
| Complete 24-hour observation / no-episode coverage | Explicit no-headache responses exist, but no documented interval/after-day completion or verification history | FAIL; neither positive nor negative forecast labels are admissible |
| Missing/unknown separate from negative | Explicit flags and missing dates distinguish some states; conflicts and blanks require exclusion | PASS only for maintaining distinctions, not for verified negative labels |
| Revision/as-of/freeze auditability | Final workbook, no diary revisions/deletions or adjudication availability | FAIL; cannot construct historical feature, outcome or eligibility snapshots |
| Account/participant isolation | B/C mappings disagree across sheets | NOT VERIFIED for resolved human identity; no pooling/merging permitted |
| Chronological split with purged horizons | Dates sortable, but availability, episode boundaries and verified horizons absent | NOT VERIFIED for valid prospective evaluation |
| Personalized sufficiency | Raw groups below unchanged 180-day/180-window gates | FAIL current engineering gates; no clinical sufficiency conclusion |
| Copyright/access versus secondary-use safeguards | Public publisher CC context; protocol-specific consent/privacy clearance not established | CONDITIONAL, separate review needed |

Historical availability, outcome adjudication and build eligibility are separate clocks. The release supplies none of their required daily revision/freeze evidence. Its file hash freezes the **downloaded final artifact**, not the data that would have been known in 2014–2015. Do not create artificial `recorded_at`, `independently_verified`, complete-coverage intervals or consent references to make an adapter pass.

## Bias, leakage and supported tasks

- **Selection:** clinical smartphone users and diary-adherent completers are a selected population. The publication's recruitment/completion filter is not evidence of representativeness. End-of-study adherence filtering is future-dependent selection if used to claim an operational historical forecasting cohort.
- **Retrospective reporting and missingness:** diary date is not upload time. Delays, revisions, selective recording during symptoms and missing-not-at-random mechanisms remain unknown. Do not impute absent outcomes as headache-free or publish an enrollment-wide coverage rate from raw ID envelopes.
- **Target leakage:** same-day symptoms used in migraine classification, medication response, disability, final duration, ongoing status and whole-study summaries cannot become pre-onset features. Even lagged exposures lack verified availability. Premonitory symptoms and reported exposures need separate time definitions; associations do not establish causal triggers.
- **Evaluation:** provisional IDs permit descriptive grouped/date summaries, not proof of prospective, participant-isolated evaluation. Never pool all rows randomly or use future person means. Purging chronological calendar dates alone cannot resolve capture-time or attack-continuation leakage.
- **Task scope:** cleaned reported headache-day frequencies and exposure associations are potentially feasible. Severity description among recorded headache days is possible in principle, but severity prediction and early-warning modeling still require verified pre-outcome features and an explicitly different protocol. Population and personalized next-24-hour onset forecasting are not supported by this release under current rules.
- **Privacy:** public coded health data are not automatically anonymous. Exact dates, demographics, sites and free text can create linkage risk. Keep source material outside Git and ordinary test fixtures; do not upload it to external ML services. Copyright permission does not remove privacy obligations.

## Reproduction and unresolved access requests

Direct access **was available** in this audit. To reproduce without adding patient data to the repository:

1. Open the original article's Supporting Information and choose **S1 File (XLS)**, or use the stable publisher download above. Follow a freshly issued redirect; a cached signed URL may expire. If blocked, request that exact supplement DOI through PLOS or the corresponding author; do not substitute an unrelated mirror.
2. Store the file in an access-controlled temporary directory outside the repository. Confirm byte count and SHA-256 before comparing these findings. A changed hash requires a new versioned audit.
3. Use a separate temporary environment/parser (`xlrd==2.0.2` for BIFF8), with no application dependency change. Inspect `book.sheet_names()`, `sheet.nrows`, `sheet.ncols`, header rows and typed cells. Select rows using the rules above; count both empty cells and empty strings as absent. Never print participant rows or IDs into research reports.
4. Count B/C identifiers independently before joining; use only trim/NFKC for this audit's normalization check. Group dates by raw B, count duplicate keys, parse `YYYYMMDD` and `YYYYMMDDHHMM` strictly, and cross-tab total-sheet CZ/DA/AO. Reject conflicting/invalid values rather than repairing them. Do not attach a timezone by assumption.
5. Retain only reviewed aggregate/schema findings in documentation, then remove the temporary patient workbook. No app experiment or forecast-label extraction is required to reproduce the NO-GO finding.

Ask the authors/data controller for: a documented B/C crosswalk and reason for extra IDs; a bilingual codebook including blank/`N`/helper-column semantics; reconciliation of 1,099 versus 1,098 headache classifications and the 11 no-headache conflicts; raw submission/receipt times, timezone and immutable revision/deletion history; permissible late-entry windows and completed-day coverage rules; stable attack linkage and independently reviewable onset/recovery evidence; outcome-adjudication timestamps; and intended-use permission/consent/privacy requirements. Do not infer these answers from this workbook.

## Validation and limits

Workbook size/hash, row counts, identifier counts and key timestamp/flag aggregates were checked in repeated local read-only inspections. Two final independent workbook reads produced identical record/identifier/flag summaries and passed assertions for the three sheet counts, 3,480 explicit nonconflicting no-headache responses, 11 contradictory rows and 262 ongoing reports. The temporary workbook and parser wheel were then removed. At the audit checkpoint, both complete untracked documents passed whitespace checks; all 20 local Markdown links resolved; tracked files were unchanged and the staging area was empty. Final publication checks review the same two-document scope.

This was not independent clinical adjudication, a complete cell-by-cell error census, source-system validation or model evaluation. No forecasts, class-balance-ready sample set, clinical metrics or synthetic-data performance were produced. No baseline code/gates were relaxed. Runtime test suites are not required by this documentation-only change and were not rerun; previous sprint results are not new evidence. The audit itself did not authorize publication. Subsequent Sprint 12 finalization instructions authorize committing these two documents, pushing the feature branch and opening a PR; merging remains unauthorized.

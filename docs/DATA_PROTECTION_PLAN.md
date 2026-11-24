# Phase 6: data protection and backup security plan

## Phase 2A: isolated synthetic SQLite snapshot exercise (2026-11-24)

Added [`sqlite_exercise.py`](../prototypes/synthetic_encrypted_backup/sqlite_exercise.py)
and [synthetic tests](../prototypes/synthetic_encrypted_backup/test_sqlite_exercise.py).
The exercise creates its own new WAL-mode source with fictional records, uses
SQLite's online backup API to capture a standalone synthetic snapshot, normalizes
the copy to DELETE journal mode, encrypts with fresh in-memory AES-256-GCM key and
nonce, validates authenticated metadata and database integrity/rows, and publishes
only to a new fixed synthetic restore target with no overwrite fallback. It uses no
application input, existing database, real records, migration, persistent key or
application integration. Plaintext source, snapshot and restore exist in its own
temporary directory; cleanup is not secure deletion.

Final evidence: **12 SQLite tests passed**, **19 prior JSON tests passed**, and
the isolated synthetic CLI completed. SQLite 3.51.0 and existing cryptography
46.0.3 were used; this is not a test of pinned 50.0.2. No install occurred.
An initial 8-test run had six errors: the WAL-header backup image could not be
validated after in-memory deserialization. The copy is now normalized before
serialization. The first `-I` CLI smoke also failed because the script directory
was absent from the import path; this was corrected and rerun. The WAL test checks
committed rows and exclusion of a separate uncommitted transaction, plus a later
commit not appearing in the snapshot. No concurrent stress or power-failure test
was run. Wrong key, corruption, truncation, existing target, publication race,
injected failure and interruption are tested with newly generated fixtures.

This does **not** close SP4-01 or provide a real backup/restore feature, durable
key custody, encrypted application storage, authenticated operator provenance,
production disaster recovery, retention/erasure reconciliation or secure deletion.
Any application integration requires separate design, threat-model review and
authorization, and synthetic SQLite/WAL, key recovery, no-clobber, migrations,
session revocation and full restore testing before handling real data.

## Approved synthetic-only encrypted prototype follow-up (2026-11-10)

The user separately approved this narrow implementation on `security/data-protection` at **`07ae0b1`**, with merged PR #20 and only the existing Phase 6 plan/release edits present. Those earlier edits are preserved below. **New encryption occurs only on generated fictional JSON inside isolated temporary exercises.** No existing user data file, SQLite/WAL/SHM, backup/export, browser storage, health record or secret was accessed. Application code/configuration, production locks, migrations, OS encryption settings and cloud infrastructure were not changed. No existing environment was installed into. This does not implement the local adoption or hosting designs below.

### Prototype and cryptographic choices

Implementation and safe setup: [prototype README](../prototypes/synthetic_encrypted_backup/README.md), [implementation](../prototypes/synthetic_encrypted_backup/prototype.py), [19 focused tests](../prototypes/synthetic_encrypted_backup/test_prototype.py), [prototype-only requirements](../prototypes/synthetic_encrypted_backup/requirements.txt). The standalone entry point accepts **no arguments, input paths, key paths or destinations**. It generates 4-8 random synthetic records; it does not load an app export. The test API accepts candidate encrypted bytes, never a user file path. Private Python attributes are not a security boundary against code/debuggers running in the same process.

Uses maintained PyCA **cryptography 50.0.2**, **AES-256-GCM**, 32-byte random key, fresh 12-byte nonce and 16-byte authentication tag; no invented cipher or unauthenticated encryption. The normal exercise encrypts one generated batch with a new key per context. Negative fixtures that reseal malformed content always use fresh nonces. [PyCA AEAD documentation](https://cryptography.io/en/latest/hazmat/primitives/aead/#cryptography.hazmat.primitives.ciphers.aead.AESGCM) defines the authentication and nonce requirements. This small binary envelope is a **prototype v1 format**, not a general database-backup standard:

```text
magic | version byte | 2-byte metadata length | canonical JSON metadata
      | 12-byte nonce | ciphertext and 16-byte GCM tag
```

Exact header bytes, including magic/version/length, metadata and nonce, are AES-GCM associated data. After bounded framing checks, the tag is verified **before parsing metadata/plaintext**. Strict canonical JSON, duplicate-key, schema/type/range/version/algorithm/identity/count checks then apply. Decrypted data must equal this run's generated batch. Maximum envelope **64 KiB**, metadata **2 KiB**. Tests change still-valid JSON metadata while forbidding any parser call, proving rejection at AEAD authentication rather than merely a later schema mismatch. This fixes the earlier hash-only demonstration's weakness **inside this prototype**, not in MigraMind's existing export/backup flows.

The earlier GnuPG recommendation remains a possible future operational-backup design. This approved AEAD experiment is deliberately different: no recipient distribution, PKI/signatures, persistent archive key, key escrow or KMS. Symmetric authentication demonstrates possession of the current ephemeral key, not a named operator; a key holder can forge an archive. It does not establish trusted provenance, rollback freshness or authorized account ownership in a production recovery process.

### Keys and failure/recovery guarantees

- Keys are generated by `AESGCM.generate_key(256)` and exist only in process memory. No hardcoded keys, key arguments/env values, printed keys, key files or decryption keys beside the backup. Tests inspect only files they generated and verify no key bytes are persisted without using key operands in failure diagnostics.
- Context exit drops key/plaintext/backup references and removes its own generated sandbox. Keys intentionally become unavailable afterward; there is **no cross-process or durable recovery**. Python/native immutable buffers cannot be reliably zeroized. Memory inspection, paging/crash dumps, abnormal-termination leftovers and secure erasure are not solved. No host policy/ACL change is made by this prototype.
- Authentication and all validation finish before plaintext staging; tests prohibit staging calls for rejected candidates. A new `mkstemp` file in the owned sandbox is written, flushed and fsynced, then published to a **fixed new recovery name** by `os.link`. There is no arbitrary output path, `os.replace` or overwrite fallback. Existing valid targets and competing publications survive failure byte-for-byte. Unsupported hard links fail closed.
- A hard link gives no-clobber atomic name publication on the tested local filesystems, **not proven power-loss durability**. Directory fsync, remote filesystems, disk-full/crash stress, hostile same-user/multiuser manipulation and operator recovery guarantees remain unverified. Staging cleanup is best effort on error, with context cleanup afterward; cleanup is not secure deletion. Plaintext JSON exists briefly only for the generated recovery within the sandbox.

### Dependency provenance and isolated environments

Only the prototype requirement file was added: **cryptography==50.0.2**, **cffi==2.1.1**, **pycparser==3.11**, and **typing_extensions==4.16.0 on Python <3.11**. Windows installed three packages; WSL installed four. Each exact version's public PyPI metadata was checked (no listed advisory entries at review time). Wheels came from `files.pythonhosted.org`; platform-specific SHA-256 and install reports were retained. This is version/registry evidence, not complete vulnerability, publisher-signature or FIPS verification, including for bundled OpenSSL.

New Windows environment: `%TEMP%/migramind-encrypted-poc-pmnef2jf/windows-venv`, **Python 3.13.12**, cryptography **50.0.2**, OpenSSL **4.0.3 (29 Sep 2026)**. New final WSL environment: `/tmp/migramind-synthetic-aead-final-j2gahf5e/venv`, **Python 3.10.12**, same cryptography/OpenSSL. Prototype supports Python 3.10+; this WSL run is **not** evidence for MigraMind's separate Python 3.13 application/CI installation. Neither environment contains/uses the application or its DB. No dependency was added to application locks.

Setup uses `venv --without-pip`, which avoids WSL's missing ensurepip without installing system packages. A downloaded **pip 26.3** universal wheel was SHA-256-checked against official PyPI metadata, then invoked with `runpy.run_module(..., alter_sys=True)` under the new venv interpreter. Subsequent pip commands use explicit official index, config null-device, empty temporary netrc, isolated/noninteractive/no-cache mode, wheel-only installs, 20s network timeouts and one allowed retry. Keys are generated only later inside tests/demos; installer logs contain no test-key material. The README includes a portable isolated setup recipe and exact commands.

### Actual test evidence and recorded failures

| Check | Result |
| --- | --- |
| Final Windows suite | **19 passed**, zero failed/skipped, **0.736s unittest / 1.683s process wall**. |
| Final WSL suite | **19 passed**, zero failed/skipped, **0.223s unittest / 0.418s wall**. Same scenarios, not 38 independent workflows. |
| Standalone demos | Authenticated JSON recovery passed on both; output reports synthetic status/count/round-trip only, not keys, plaintext records or ciphertext. Final Windows **0.366s**, WSL **0.116s** process wall. Counts vary randomly and are not clinical metrics. |
| Dependency compatibility | `pip check` exit 0 on both; Windows **1.86s**, final WSL **0.417s**. Installed version/host/hash metadata recorded separately from application requirements. |
| Authentication/format cases | Wrong key; modified valid JSON metadata; nonce/ciphertext/tag changes; magic/version/length bounds; truncation/append/oversize/non-byte input; duplicate/noncanonical/invalid metadata; valid-tag malformed metadata/payload; type/range/original-batch/cross-exercise checks passed. |
| Recovery failure cases | No staging before successful validation; no valid-target overwrite on rejection or even valid repeated restore; fsync/link failures preserve prior target; concurrent publication wins without overwrite; temporary cleanup/reference release checks passed. |
| Source/docs integrity | Final local links/line bounds, whitespace, Python compilation/setup-example syntax and scope checks preserve all pre-existing source/production locks/configuration and original Phase 6 report bodies. No app tests or migrations were needed/run. |

**Failures/development runs, retained:** initial WSL suite passed **17 tests in 0.165s** before two more cases and stronger pre-parse/pre-staging assertions were added. Initial Windows setup failed **before dependency installation/tests** because a custom verified-wheel launcher set argv to `pip`, triggering pip's Windows self-modification guard (**8.20s**). Corrected the temporary launcher to standard module semantics with `alter_sys=True`; did not disable/patch pip's protection or change versions. One corrected bootstrap succeeded (**32.96s**), then dependency install (**14.53s**) and the then-current 19-test suite passed (**0.687s / 1.89s wall**). The final strengthened Windows suite above also passed; this was a source/test update, not a flaky rerun until green.

The initial WSL temporary environment was not available for a later invocation; no cause is asserted. Final verification created another **new** isolated WSL target, not an existing user environment: venv **0.116s**, bootstrap **5.443s**, pinned installation **4.238s**, followed by final tests above. Initial WSL setup/install had also succeeded (**0.12s / 5.74s / 4.24s**). The conditional typing_extensions version first resolved on WSL was then explicitly pinned for reproducibility. No cryptographic/unit assertion failed or timeout occurred; no different cryptography version was substituted. Windows pip logs show zero retry/resume messages. The retained reports distinguish initial and final runs; new environment setup is not a production deployment.

Evidence root `%TEMP%/migramind-encrypted-poc-pmnef2jf/`: source baseline, public dependency metadata, verified pip wheel, installation reports/artifact hashes, original refused bootstrap log, Windows initial/final results, WSL captured initial/final results, tests/demos/version logs and final integrity report. No keys or generated plaintext/ciphertext are deliberately retained in those reports; exercise files are cleaned on normal context exit. No actual user data was used to verify preservation.

### Remaining blockers and next approval boundary

**SP4-01 remains High/open.** The production application still uses its existing SQLite/plaintext export mechanisms. This prototype supplies no SQLite/WAL snapshot consistency, real-account restore, session revocation, retention/withdrawal reconciliation, durable key recovery, independent-device/off-host recovery, operator identity separation, OS storage protection or hosted/KMS evidence. No OS encryption/key deployment, data relocation, app integration, migration, credential change or cloud infrastructure is authorized. Earlier Windows ACL probe failure and all public/real-data/manual/research release blockers remain recorded below.

Only `prototypes/synthetic_encrypted_backup/{prototype.py,test_prototype.py,requirements.txt,README.md}` and this plan/release report change. Prior audit/source/requirements/locks/settings remain intact. No commit, push, PR, merge or deployment. Any durable keys, real input/output paths or integration require a new design/review/approval, not removal of the synthetic restrictions.

## Historical design and plaintext synthetic-drill evidence

Prepared **2026-11-10 (Asia/Calcutta)** on `security/data-protection`. Starting HEAD **`07ae0b1`**, merge of PR #20 (`a57bc4c`); branch and clean working tree verified before work. Reviewed the [security/privacy audit](SECURITY_PRIVACY_AUDIT.md), [release-readiness evidence](RELEASE_READINESS.md), application/research source, CI and existing operations guidance.

**Design and bounded synthetic validation only.** No application, database, existing backup, migration, dependency, lock, secret or production setting changed. No encryption enabled, key generated, existing data relocated, app started, provisioning performed or infrastructure created. The JSON-only drills below use fictional files in newly created temporary directories; they are not database or encrypted-backup tests. All adoption/implementation steps require separate approval before execution.

## Decision and remaining risks

Recommend layered local device/storage protection plus separately encrypted, recoverable portable copies. Keep the current fictional loopback demonstration boundary while actual protection is unverified. Do not introduce SQLCipher, field encryption or a hosting stack during this phase.

| Audit risk | Remaining exposure / status |
| --- | --- |
| **SP4-01 / High: application-unencrypted files and copies** | Ordinary SQLite/JSON lacks application encryption. Someone obtaining a real-data file, unlocked device or plaintext synced/exported copy can bypass HTTP account isolation. Actual full-disk encryption, active data path, cloud sync scope and existing copy inventory remain unknown; no exposure/compromise is asserted. **Open; real-data release blocker.** |
| **SP4-05 / Medium: retention/erasure across copies** | Corrections/deletions retain private daily history until account erasure; downloads, prior backups, shared text and unassigned legacy rows are not erased by account deletion. No enacted all-copy retention/withdrawal/restore-erasure process. **Open; real-data/research blocker.** |
| **SP4-06 / Medium: hosted operations** | Templates do not verify storage/TLS/KMS/grants/logs/backup recovery or an operator's incident process. **Open; public-hosting blocker, including synthetic hosting.** |
| Other release gates | Authentication/recovery, abuse controls, CSP compatibility, human accessibility/device and research/clinical gates remain as documented. PR #20's installer bootstrap does not encrypt data; these drills do not supply additional installer/CI/clinical evidence. |

## Threat model and trust boundaries

Assets include migraine/medication notes, numeric observations and precise times, revision history, identity/contact/profile information, support choices/feedback, consent receipts, database authentication/session metadata, derived datasets and every retained copy. A full database backup includes security tables excluded from normal JSON export, so it needs stricter handling than a public synthetic example.

| Threat / actor | Intended controls | Residual boundary |
| --- | --- | --- |
| Lost/stolen powered-off device or removable disk | Active OS full-disk encryption on every relevant volume; protected recovery custody | Does not protect an unlocked/mounted system or copies elsewhere. Protection state/suspension and coverage need owner verification. |
| Another ordinary local OS account or accidental broad sharing | Private nonsynced directory, explicit/inherited file permissions, separate profiles and recipient review | Same-user malware/browser extension, SYSTEM/root/admin takeover and authorized application access are not excluded by owner ACLs. |
| Cloud sync/version-history, leaked export or stolen backup | Avoid live-data sync; encrypt portable copies before transfer; separate keys and storage identity | Local disk encryption decrypts reads for the sync client. A recipient who decrypts can keep plaintext; prior remote versions require separate retention action. |
| Corruption, interrupted capture, ransomware or accidental overwrite | Consistent snapshot, integrity/authenticity verification, exclusive new targets, versioned offline/immutable recovery copy | Encryption alone does not prevent deletion/ransomware. A checksum without trusted provenance does not authenticate the snapshot. |
| Lost key, departed operator or bad recovery | Named custodian, separate recoverable key escrow, tested independent restore and version metadata | Loss of all required key/recovery material may be permanent data loss. Storing the key with the backup defeats separation. |
| Restore resurrects withdrawn data or old sessions | Review deletion/retention ledger and revoke restored sessions before serving; isolated validation and approval | A historical backup is not automatically consistent with later account deletion. Restore must not silently republish removed information. |
| Compromised application/authorized database operator | Existing ownership/CSRF/session controls; future restricted identities and key separation | At-rest encryption does not fix IDOR, XSS, authorization bugs, clinical validity or an application entitled to decrypt. Those remain independent gates. |

## Storage and copy inventory: confirmed mechanisms versus unknown copies

**Confirmed** below means source or recorded synthetic behavior establishes a mechanism, not that an existing personal file was inspected. No actual `.env`, database, backup, download, OS recovery key, browser profile or cloud account was opened. Paths are source defaults/proposals, not discovery of active private data.

| Location / flow | Source evidence / current protection | Gap and next adoption check |
| --- | --- | --- |
| SQLite main file | [main.py:18](../backend/app/main.py#L18) loads settings and creates ordinary SQLAlchemy engine; [security.py:70](../backend/app/security.py#L70) defaults to relative `sqlite:///./migramind.db`. Foreign keys on, SQL echo off, parameters hidden. Usual backend working directory would put the fallback there; active URL unknown. | No application encryption. Future owner must approve an explicit absolute private data root; never rely on the fallback or inspect private config in this audit. |
| Stored health and security rows | [models](../backend/app/main.py#L31), [daily models](../backend/app/prospective_models.py#L6). Diary, medications, wellness/early symptoms, daily values/revisions, contacts, personal caregiver notes, preferences, feedback/consent; email/password hash, session digest/CSRF/expiry also persisted. | Protect the entire database/history/security metadata, not only current notes. Passwords remain one-way hashes. Admin/offline access bypasses HTTP account ownership. |
| Journals/WAL/SHM, spill, free pages | SQLite can create sidecar/temporary files; current engine enables foreign keys but does not attest journal/temp/secure-delete mode. See [SQLite temporary files](https://www.sqlite.org/tempfiles.html). Actual files/modes unknown. | Cover sidecars, OS temp, paging/hibernation and crash locations where relevant. SQL DELETE/file deletion is not a verified physical-erasure method. No sidecar was accessed or created here. |
| Account JSON download | [tracking_routes.py:89](../backend/app/tracking_routes.py#L89), [main.tsx:85](../frontend/src/main.tsx#L85). Current-account attachment includes histories/contacts/profile; excludes password/session tables and unclaimed legacy rows. Blob URL revoked; no-store. | Plaintext device file remains after revocation/logout/deletion. Download destination and OS copies unknown. No-store is not encryption or download erasure. |
| Research-preparation download | [research_quality.py:124](../backend/app/research_quality.py#L124), [ResearchQuality.tsx:9](../frontend/src/ResearchQuality.tsx#L9). Explicit literal consent/scope, numeric/history allowlist, mapped IDs, warnings that data is private/not de-identified/not training-ready. | Precise timelines and old numeric values remain sensitive; pseudonymization is not anonymization. Consent for this download is not off-host transfer/research enrollment. |
| Backups/snapshots | [privacy guide](authentication-privacy.md) documents historical ignored `backend/.research/backups/`; existence/content not checked. [operations runbook](OPERATIONS_RUNBOOK.md#encrypted-backup-retention-and-restore--proposed-procedure) proposes encrypted backups/restore; not installed. | A documented or proposed copy is not proof of current encrypted recoverability. Owner must privately inventory local/off-host versions and retention; no enumeration of existing backups here. |
| Browser memory/storage/cache | [api.ts:1](../frontend/src/api.ts#L1) holds CSRF in memory and uses credentials/no-store/no-referrer; [Authentication.tsx](../frontend/src/Authentication.tsx) clears/remounts on session changes. HttpOnly cookie is set by [auth.py:105](../backend/app/auth.py#L105). localStorage stores theme and [random session-change signal](../frontend/src/sessionEvents.ts#L1). No application health IndexedDB/service-worker storage found in the reviewed source. | DOM/React state, browser profile/cookie persistence, swap/session restore, autofill, extensions and screenshots remain platform/user-dependent. Existing profile/cache was not inspected. |
| Clipboard/native share/SMS/location | [SupportCard.tsx:4](../frontend/src/SupportCard.tsx#L4), [SOSMessage.tsx:17](../frontend/src/SOSMessage.tsx#L17), [assistance.ts](../frontend/src/assistance.ts). Explicit previews/actions; optional location stays in preview rather than API payload. No caregiver-access/public-link/automatic-delivery endpoint. | Clipboard history/sync, composer drafts, screenshots, recipients/carriers/device services may retain plaintext. App encryption cannot revoke these. No native handler was activated. |
| Logs and diagnostics | [PrivateBoundary](../backend/app/security.py#L90), [error handlers](../backend/app/main.py#L179), [fixed events](../backend/app/deployment.py#L11); [launcher:29](../backend/app/serve.py#L29) disables access logs. nginx/systemd are examples only. | No raw payload logging found in reviewed paths, but raw uvicorn defaults, infrastructure errors, memory dumps and unreviewed tooling may retain metadata. Actual logs not read. Log minimization/retention remains necessary even on encrypted storage. |
| Research/ML artifacts | [cli.py:65](../backend/research/cli.py#L65), [baseline_cli.py:38](../backend/research/baseline_cli.py#L38): explicit output directory, report JSON and opt-in derived dataset JSON; [support_evaluation.py](../backend/research/support_evaluation.py) can write a simulated aggregate report. Reviewed runtime serves no model; these paths do not serialize a model. | Derived dates/features/labels, input hashes and small-cohort aggregates may reveal information. Actual output locations/files unknown; arbitrary model/pickle copies are hypothetical, not discovered. |
| Test/CI/temp artifacts | [test_auth.py:13](../backend/tests/test_auth.py#L13) uses in-memory synthetic accounts; [manual fixture](../frontend/test-fixtures/manual-accessibility.ts) is database-free; [CI helper:103](../scripts/ci_browser.py#L103) normally creates a new temporary DB. Browser diagnostics/screenshots and developer copies may be produced by tests/tools. | Synthetic-only artifacts here; temporary/ignored does not mean encrypted, secure-erased or outside all OS backups. Full CI/database harness was not run in Phase 6. |
| Repository/sync/hosting | Checkout `C:/Users/srish/OneDrive/Desktop/migramind` is confirmed. [.gitignore](../.gitignore) excludes local records/artifacts/secrets, not cloud sync. [nginx root](../deploy/nginx-demo.conf.example#L16) is frontend dist; [service template](../deploy/migramind-demo.service.example#L9) uses a dedicated identity/private temp and proposed `/var/lib/migramind-demo` writes. | OneDrive sync scope, remote version history, redirected folders, device encryption, OS backup and actual hosted permissions unknown. No static database-serving route found; that does not attest an operator's server root. |

## Local-prototype control design

| Control | Proposed adoption and acceptance | Limit / approval boundary |
| --- | --- | --- |
| OS full-disk/volume encryption | Device owner verifies active BitLocker/Device Encryption or approved Linux equivalent, not suspended/clear-key protection; cover data, temp, download, paging and removable volumes as applicable. Privately verify recovery readiness. [Microsoft overview](https://learn.microsoft.com/en-us/windows/security/operating-system-security/data-protection/bitlocker/). | Not enabled/inspected here. Protects covered offline media, not an unlocked app, admin/malware, decrypted export or plaintext synced elsewhere. Do not print recovery keys or change BIOS/device policy during an audit. |
| Durable nonsynced root | Owner selects `<approved-private-data-root>` outside source/OneDrive/shared/download/temp trees, verifies sync/backup policy and capacity, then approves an explicit absolute URL in a later task. Keep source/venv/builds separate. New synthetic demo must retain required `migramind-synthetic-demo.sqlite` basename. | `%LOCALAPPDATA%` may be a candidate, not a guarantee of exclusion. `%TEMP%` is suitable for fictional drills, not durable records. No live path/config change or automatic relocation is authorized. |
| Restricted permissions | Windows: protect new data-directory DACL; allow owner and required SYSTEM/service identities only, with inheritance for DB/sidecars/staging. Linux: private owner directory `0700`, files `0600`, process umask `0077`; separate service identity if later hosted. Grant runtime only required rights; keep backup/restore administration separate where feasible. | Same-user processes and privileged admins/root remain trusted. Do not remove recovery/system access blindly or apply recursive ACL changes to existing paths. Windows read-only probe was blocked; effective multi-identity testing remains a gate. |
| Exports and manual sharing | Synthetic-only for now. For real workflows, approve a recipient, purpose and restricted download/staging policy before export; protect portable copies before off-host transfer. Minimize preview text and avoid clinical identifiers when unnecessary. | Current UI exports plaintext. Encrypting a download afterward does not erase the original; adding encrypted UI export is a separately approved feature. Copy/share delivery and recipient retention cannot be guaranteed or revoked by MigraMind. |
| Backups and snapshots | After approval, use a consistent SQLite snapshot via reviewed online backup API/quiescence into a **new** restricted target; then an approved encryption format before portable/off-host storage. Keep one independently protected offline/immutable recovery copy and a versioned manifest. See [SQLite backup API](https://www.sqlite.org/backup.html). | Never blindly copy only a live `.db` while WAL/writers may be active. JSON drills do not prove SQLite consistency. Protected plaintext staging is still plaintext to the running OS; limit it and approve retention. Encryption cannot stop an authorized destructive actor. |
| Integrity/provenance | Manifest binds snapshot identity, source schema/release, capture time, ciphertext hash/size, format/key version and recovery requirements, without raw health/credential fields. Use authenticated encryption and signed or otherwise independently authenticated/protected provenance; verify before restore. | SHA-256 detects accidental mismatch only if its manifest is trusted. Someone replacing both can forge a match, as demonstrated below. Public-recipient encryption alone does not identify the sender. No signing/encryption key was generated. |
| Recovery keys | Name device owner and backup key custodian; separate device-unlock, archive-decryption and application credentials. Use approved protected recovery custody independent of the data/same synced folder, with an offline/separate administrative recovery route and reviewed recipient fingerprints. | Do not derive archive keys from an account password/hash or appoint a trusted contact as key custodian automatically. Loss of all copies may make recovery impossible. Shared cloud recovery accounts can be a correlated compromise; owner must assess MFA/custody privately. No key-management implementation here. |
| Retention and deletion | Approve schedules for snapshots, staging, logs, exports, derived datasets and shared copies; record withdrawal/account-erasure handling and review restored data before serving. Existing runbook's daily backup, 7 daily/4 weekly copies, 24h RPO/4h RTO are proposals only. | No schedule, deletion job or measured recovery SLA exists. Retention and immutable-copy choices must reconcile erasure duties; no legal/compliance certification. Do not delete existing copies during this task. |

Minimization and protection-layer choices follow [OWASP cryptographic-storage guidance](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html). Database/field encryption is a separate threat-model decision, not required to demonstrate fictional records and not implemented by this plan. It would still leave plaintext in authorized app responses and require driver/schema/history/analytics/recovery compatibility work.

Practical default for the next **proposed** portable-backup prototype: reuse the existing runbook's **GnuPG recipient-encryption** approach, with independently verified recipient fingerprint and backup-identity signature/authenticated provenance. A consistent SQLite snapshot would first reside only in approved restricted/encrypted local staging; ciphertext alone would transfer off-host. Restrict the signing/decryption identities separately and test restored bytes, signatures, tampering, wrong recipient and lost-key recovery before adopting it. [GnuPG operations](https://gnupg.org/documentation/manuals/gnupg/Operational-GPG-Commands.html) distinguish encryption from signing; possession of a public encryption key is not sender authentication. Tool/version, custody and retention remain approval decisions; GnuPG was not installed or executed, and no keys/files were encrypted. Current plaintext UI downloads would still need their own approved handling rather than being implicitly secured by this backup prototype.

## Step-by-step adoption plan - execute only after specific approval

1. **Name owners and scope.** Approve data classes, intended users, permitted recipients, local/hosted boundary, operator, privacy owner, key custodian and incident contact. Keep synthetic-only operation until gates are met. Do not infer consent or production authorization from this document.
2. **Obtain private device/path attestation.** Owner confirms volume protection/lock/recovery status and privately inventories active DB path, sidecars, downloads, backups, sync versions and derived outputs. Record coverage/status, not records/keys. This examination of actual private settings/copies was deliberately not performed here.
3. **Rehearse in a new empty root.** Validate ACLs, inheritance, identity boundaries, free space, overwrite refusal and recovery with synthetic JSON first, then separately approved synthetic SQLite/WAL fixtures. Stop on unavailable privilege, ambiguous paths, unknown schema or any negative check unexpectedly permitting a write; do not relax permissions to pass.
4. **Approve a backup format and custody.** Select maintained encryption tooling, trusted recipients and separate recovery storage; validate wrong-key/recipient, tamper/truncation, rotation and recovery on another approved device using fictional data. These encryption/key exercises require separate approval and have not run.
5. **Approve any real-data capture/cutover separately.** Explicitly name source, new target, consistent snapshot method, readers/writers to stop, key/storage coverage, rollback snapshot and retention owners. No in-place conversion, migration or generic directory move. Existing source remains restricted and unchanged until independently verified cutover/recovery and an explicit retirement decision.
6. **Protect exports and artifacts.** Choose whether real exports remain disallowed or require a separately approved protected workflow. Cover download/staging remnants, clipboard/share recipients, research datasets and logs. Never upload real files into issue trackers, Git, CI or these review tools to demonstrate safety.
7. **Run a complete recovery rehearsal.** Restore synthetic data into another empty protected target, verify source/schema/history/owner isolation, disable restored sessions and reapply later erasure decisions before serving. Validate key recovery without putting key material in reports. Measure RPO/RTO with a representative fixture; no performance inference from tiny JSON timings.
8. **Approve operational retention and incidents.** Assign backup monitoring/failure response, off-host/offline custody, key rotation/recovery, expiry review and incident stop/resume authority. Record version/date of the approved runbook; do not automatically delete old backups or keys.
9. **Make a release decision.** Only mark a control complete with its named evidence. Recheck independent authentication, abuse, hosting, accessibility, privacy/research and clinical gates; encryption cannot close them by itself. Any implementation must be a separately reviewed change with explicit target/data authorization.

## Future-hosting design - separate from local adoption

Production currently requires a dedicated **synthetic PostgreSQL** target, verified database TLS and explicit HTTPS origins/hosts. Preserve those guards; do not expose development SQLite or flip to development mode to accept real data.

| Boundary | Proposed hosted control and required evidence |
| --- | --- |
| Data/snapshot storage | Provider/OS encryption for database volumes, WAL, snapshots, replicas, staging and backup copies; verify actual configuration, keys and restore behavior. PostgreSQL `sslmode=verify-full` is transit protection, not at-rest encryption. No default upstream PostgreSQL transparent-encryption capability is assumed. [PostgreSQL encryption options](https://www.postgresql.org/docs/current/encryption-options.html). |
| Transport | TLS at ingress and verified TLS to DB/backup services, reviewed CA/hostname/proxy trust, private DB networking and secure cookies; no insecure fallback, public repository root or public bucket/volume. Actual certificate/network testing pending. |
| Identity/KMS | Separate application, migration/admin, backup-writer, restore-reader and key-administrator identities. KMS-managed envelope keys, environment separation, narrow encrypt/decrypt grants, protected key versions, value-free access audit and rotation/recovery. Keep keys out of DB/source/VITE values; no implementation/provider selection here. A runtime entitled to decrypt can still expose plaintext if compromised. |
| Backup capture/custody | Consistent logical/physical/PITR capture with WAL requirements documented; ciphertext plus authenticated manifest, restricted off-host/offline or approved immutable copy, protected transfer and retention. Runtime must not have broad delete-backup/key-admin rights. |
| Restore | New isolated target/network, release/schema/key pairing, approved DB grants, tenant/history consistency, stale-session revocation and erasure reconciliation before ingress. A restored TLS endpoint or marker alone is insufficient. No PostgreSQL/cloud exercise ran. |
| Logs/operations | Payload minimization, restricted/encrypted log/crash storage, retention and aggregate backup-age/failure/recovery monitoring; no secrets/raw health traces. Named operators perform incident/key-loss/restore drills and authorize resumption. |

Application-layer field encryption could reduce a DB-only leak if keys are truly separate, but requires new schema/history/query/export design and does not protect an authorized compromised app. End-to-end/client-held encryption would also change server analytics and recovery semantics. Neither is approved or introduced. No public/real-health deployment follows from this hosting design.

## Acceptance criteria and evidence gates

| Gate | Acceptance evidence required | Current status |
| --- | --- | --- |
| A1 - known devices/paths/copies | Owner-approved private inventory and sync/retention classification without publishing data | **Pending; unknown actual settings/copies** |
| A2 - active encryption and recovery | Covered volumes/snapshots/copies, independent key custody and successful synthetic lost-key/recipient/rotation recovery drills | **Not run; no encryption/key operation authorized** |
| A3 - least privilege | Root and inherited child ACL/mode checks, actual runtime read/write, denied unintended identity/access and retained recovery access | **Partial**: new Windows root/child/write checks; WSL modes/owner denial passed. Windows read-only ACL probe blocked; no second identity tested |
| A4 - safe file backup/restore mechanics | New targets only, equality, overwrite/path refusal, corruption/truncation/schema/missing-copy rejection | **Passed for JSON fixtures only**, same 12 cases on Windows and WSL |
| A5 - authentic backup provenance | Trusted signing/authentication and tamper/replacement/wrong-key tests tied to approved identity/format | **Pending**; unkeyed hash limitation demonstrated, not solved |
| A6 - database consistency | Approved new synthetic SQLite/WAL/locking/crash/foreign-key/revision/schema/owner tests, later hosted equivalents | **Not run; no database files touched** |
| A7 - independent recovery | New protected host/target, key recovery, session revocation, erasure reconciliation and measured RPO/RTO | **Pending**; toy same-host file restore is not disaster recovery |
| A8 - retention/incidents/release | Named operators/custodians, schedules, monitoring and reviewed erasure/rollback/incident decisions; remaining release gates closed separately | **Pending; no storage/public release clearance** |

## Safe validation actually performed

Windows evidence root: `%TEMP%/migramind-phase6-22cc9c45cc224e1a8c04afad1a1752e0/`, created new outside the checkout. This proves location separation from the repository, **not exclusion from all OS backup/sync or volume encryption**. Restricted its DACL before writing fixture contents to two inheritable FullControl allow entries: current OS SID and SYSTEM, with inheritance from parent disabled. Verified that the child sentinel, generated source, snapshot and restored file (four files) inherited only those FullControl entries and the owner could write/read. No current user SID/name, credentials or record values are published here.

**Windows failure retained:** setting a separate new read-only probe directory's ACL failed with `PrivilegeNotHeldException` / **`SeSecurityPrivilege` missing**. Did not acquire privileges, weaken policy, create another OS user or retry that ACL operation. A failed ACL application is not assumed atomic; no denial/effective permission result is claimed for that probe. Subsequent read-only inspection reconfirmed the successful root/child checks; the probe directory was not used for data. Identified the one just-created root by its exact synthetic marker after the early failure and recorded status; did not inspect unrelated temp directories or existing backups.

WSL evidence root: `/tmp/migramind-phase6-bf4jtg8d`, new fixture only. Standard-library Python **3.10.12**, non-root identity: umask **0077**, root directory **0700**, JSON fixture **0600**; after changing only a new probe file to **0400**, an ordinary owner write raised `PermissionError` as expected. This validates that local permission action under this token, not another identity, OS encryption, supported-version app installation or a second physical machine. WSL needs no venv/app dependency for this JSON drill; Phase 5 Python 3.13/CI limits are not closed by it.

The same temporary Python helper ran these **12 cases per OS** (not 24 independent scenarios): exact-byte snapshot; manifest hash/length; fresh restore bytes/semantics; existing-backup refusal; existing-restore refusal; corrupt-copy rejection; truncated-copy rejection; unknown-schema rejection; outside-root destination rejection; outside-root source rejection; missing-copy rejection; original source/snapshot/restore unchanged after negative cases. Windows helper **0.044s**, WSL helper **0.002s**: tiny synthetic timings, not service RTO claims. All 12 passed in each; no helper rerun or hidden failure. No symlink/race/adversarial multiuser stress test was performed.

**Checksum limit demonstration:** a newly generated corrupt counterpart was rejected against the original manifest; replacing its manifest digest with the counterpart's digest made the hash check accept it. This is expected and is **not authenticated-backup success**. Original fixture source, backup and restore were left unchanged. No actual backup was corrupted, overwritten or opened. All artifacts are plaintext fictional JSON/text, not a DB or encrypted container. No encryption, key, `.db`/SQLite file, application import or native handler was involved.

Retained local artifacts: `windows-permissions.json`, `backup-recovery-results.json`, `linux-drill-results.json`, fixture-only helper/logs and `source-baseline.json` (hashes of permitted tracked source only). Linux output was captured in the same process into the Windows evidence root; no dependence on future availability of `/tmp`. Synthetic artifacts are retained for review, not uploaded or automatically deleted.

Documentation validation also compiled and executed the minimal reproduction block below once, exit 0 in **0.170s**, in another automatically generated synthetic temp directory. This is a smoke test of the reduced documentation example, not another full 12-case batch. `documentation-reproduction-result.json`/log and `windows-permissions-followup.json` retain the checks. Final whitespace/local-link/line-reference and source/requirement/lock integrity checks confirm only this plan and the release report change. The security audit and all previous release evidence remain preserved.

### Minimal portable file-drill reproduction (subset, not additional counted tests)

Run the following standard-library Python in a new process. It creates its **own new** temporary target; accepts no user DB/path/backup argument; uses no application import, encryption or key. Do not replace the fixture with actual records. This reduced example checks round-trip, exclusive-write refusal and corruption detection only; the retained helper above performed the full 12-case set.

```python
from pathlib import Path
import tempfile, json, hashlib

root = Path(tempfile.mkdtemp(prefix='migramind-phase6-repro-'))
source = root / 'synthetic.json'
source.write_text(json.dumps({'kind': 'SYNTHETIC_ONLY', 'records': []}))
original = source.read_bytes()
backup = root / 'synthetic.snapshot'
with backup.open('xb') as stream:
    stream.write(original)
expected = hashlib.sha256(original).hexdigest()
assert hashlib.sha256(backup.read_bytes()).hexdigest() == expected
restored = root / 'synthetic-restored.json'
with restored.open('xb') as stream:
    stream.write(backup.read_bytes())
assert restored.read_bytes() == original
try:
    with backup.open('xb'):
        pass
except FileExistsError:
    pass
else:
    raise AssertionError('Must refuse an existing target')
corrupt = root / 'new-corrupt-counterpart.snapshot'
with corrupt.open('xb') as stream:
    stream.write(original + b'corrupt')
assert hashlib.sha256(corrupt.read_bytes()).hexdigest() != expected
assert source.read_bytes() == backup.read_bytes() == original
print('Synthetic-only file round-trip/refusal/corruption checks passed:', root)
```

This subset does **not** set private ACLs or establish encrypted backup/storage. For permission reproduction, use a new empty fixture directory and the platform's reviewed ACL/mode procedure; on Windows inspect a protected current-SID/SYSTEM DACL and inherited child before data creation, and stop on the recorded privilege error rather than enabling privileges. See [Microsoft Set-Acl](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.security/set-acl?view=powershell-7.5). On approved non-root Linux, apply `0700` directory / `0600` fixture and test a separate `0400` fixture with ordinary write; never use these instructions recursively on an existing location. Other-user denial still needs a separately approved identity test, not real credentials supplied to this agent.

## Phase 2D synthetic version-aware recovery

The synthetic backup exercise builds new SQLite fixtures with the actual Alembic
chain through 009 and 010, using a programmatically bound temporary engine rather
than the repository's default database URL. Its authenticated schema field binds
the archive to the Alembic revision; missing, unknown and inconsistent revisions
are refused. A 009 copy is upgraded to 010 only after authentication and fixture
validation, in a separately created staging database. Sessions are removed, and
the test confirms rejection of a corresponding synthetic credential after upgrade.
The versioned reader intentionally refuses the older unversioned exercise formats;
their existing readers remain unchanged.

Comparison of migrated 010 against models identified two Alembic `modify_type`
differences: wellness `sleep_hours` and `screen_hours`, reflected as FLOAT versus
model DOUBLE. This is a limited comparison, not full schema equivalence proof.
A synthetic deletion after backup demonstrated that recovery can resurrect the
deleted account and episode. No authoritative deletion history or reconciliation
is provided. All recovered copies report activation blocked; this is a prototype
contract rather than protection against manual file copying. Real deployment also
requires independently reviewed migration paths, deletion reconciliation, key
custody, access controls, durable storage and session invalidation.

## Phase 2C application-model synthetic recovery

An isolated test creates current SQLAlchemy metadata and fictional relational
fixtures, then uses the existing Phase 2B authenticated passphrase backup to
restore into a fresh target. It compares schema and all rows with a generated
fixture, checks SQLite integrity and foreign keys, and tests the actual in-process
API's rejection of an old synthetic login session and per-account episode access.
The copied login-session table is cleared before encryption. This validates a
current-model synthetic case only: `create_all` does not stamp or exercise
Alembic migrations or prove compatibility of an older database. The application
was imported with dotenv loading suppressed and an in-memory default engine; API
requests used an override to the fresh synthetic restored database.

Restoring an older backup can reintroduce an account or records deleted after the
backup. Session removal alone does not reconcile those deletions. No deletion
ledger or replay mechanism is implemented here. Review and implement deletion
reconciliation, real-schema migration and version policy, session revocation,
key custody, access control, file protection and durability before real-data use.
Temporary plaintext files and best-effort cleanup remain limitations.

## Phase 2B synthetic passphrase recovery

The isolated `prototypes/synthetic_encrypted_backup/recoverable_sqlite.py`
exercise uses SQLite's online backup API on its own generated WAL database,
removes fictional sessions from the copy, and authenticates a versioned synthetic
envelope with AES-256-GCM and a key derived by scrypt from a test passphrase.
Random salts and nonces are independently generated; KDF parameters are fixed
and checked before derivation. A fresh process can recover the exact fictional
relational records using the passphrase, without the original derived key.
Restore creates a new temporary target and refuses overwrite. This does not
integrate with the application or establish recovery of its real schema.

Passphrase loss means permanent loss of this backup; human passphrase entropy,
offline guessing resistance, recovery custody and rotation need separate design.
Passphrases and derived keys are not deliberately logged or saved; Python memory
cannot be reliably zeroized. Plaintext synthetic snapshots and restore files
exist temporarily, cleanup is best effort, and no secure erasure or crash/power
durability is established. Synthetic session omission does not prove live
session invalidation or deletion reconciliation. Real integration remains gated
on reviewed key custody, authorization, schema compatibility, storage and
filesystem protections, durability, restore validation and independent security
and privacy review. See the prototype README for scope and test commands.

## Recovery, rollback and incident procedure - proposed, not executed

1. Stop/fence the affected runtime and shared/export paths on suspected exposure, corruption, failed authenticity, wrong key or unknown source. Preserve minimal restricted metadata; never copy raw health records into tickets/logs for troubleshooting.
2. Have the owner identify the authorized snapshot, schema/release, key version/recipient and trusted manifest using private records. Verify provenance and ciphertext integrity **before** restoring; fail closed on missing material. Do not trust a matching hash downloaded beside an untrusted file.
3. Restore only into a separately approved **new empty protected target**, initially offline. Retain original/source and earlier recovery copy under access/retention control. Confirm schema, counts/history, timestamps, account ownership and sidecar permissions with synthetic rehearsal first. No active target overwrite or live raw `.db` copy.
4. Before serving any restored DB, review subsequent erasures/withdrawals and invalidate restored sessions through an approved target-specific procedure. Account deletion or previously revoked sessions must not silently be undone by a snapshot. No such DB operation occurred here.
5. Record errors and measured recovery evidence without payloads/keys; only the named operator/security/privacy owner authorizes cutover/resumption. Never bypass TLS, key checks, demo provenance or isolation to achieve a green check.
6. If rollback is necessary, stop writers and pair validated code, schema, storage and key versions with the approved snapshot. Reconcile post-cutover changes; do not silently discard later records by reverting an old file. Prefer holding offline to an incompatible or plaintext public fallback.
7. Retire staging, failed candidates, expired backups and old key versions only under separate reviewed retention/erasure approval, with precisely verified targets. No recursive cleanup, secure-delete claim or deletion of existing data is part of this plan. Recovery keys must remain available while any approved backup needs them.

## Unresolved questions and approval boundary

- Who owns the device/data, storage policy, backup job, key custody, retention/deletion decisions and incident authorization? Is independent recovery custody feasible for this local prototype?
- Which actual devices/volumes, source URL, sidecars, downloads, remote versions and backups hold data? Are protection and sync exclusions active, and are recovery keys correlated with the same cloud account? Unknown; no private settings/copies inspected.
- Are real exports/sharing needed at all? Which recipient and protected format would be approved, and how are plaintext predecessors and external copies handled?
- What RPO/RTO, retention/withdrawal rules, offline/immutable-copy policy and restore acceptance apply? Current suggestions are not measured or approved obligations.
- What explains the Windows read-only ACL operation's privilege requirement on the intended platform, and what least-privilege owner/service procedure will pass independent identity tests without broad elevation? Current partial evidence cannot close this.
- Which maintained backup/encryption tooling and key recovery process will be selected? Windows/Linux encrypted SQLite/WAL recovery, encrypted archive/key tests and hosted/KMS exercises remain unperformed.

**Stop point:** this design and synthetic evidence only. Request explicit approval for a separately scoped next implementation, such as an encrypted **synthetic-only** backup/restore prototype. Any device encryption setting, real-data path/ACL/capture/move, key deployment, migration or hosting action still requires its own concrete authorization. No commit, push, PR, merge or deployment.

# Synthetic authenticated-backup experiment

## Phase 2A: synthetic SQLite/WAL exercise

[`sqlite_exercise.py`](sqlite_exercise.py) is a separate, synthetic-only exercise;
it creates its own fresh temporary SQLite source, fictional rows, ephemeral key,
and fixed backup/restore paths. It accepts **no input paths or CLI arguments**,
does not import the app, and cannot back up an existing MigraMind database. The
original JSON exercise described below remains unchanged.

The source is kept open in WAL mode with auto-checkpoint disabled. SQLite's online
`Connection.backup` creates a consistent copy including committed WAL state. The
exercise changes **only the copied snapshot** to DELETE journal mode so it can be
validated as a standalone file; source journal mode remains WAL. A synthetic
plaintext snapshot exists briefly in the newly created temporary directory before
encryption and is removed best-effort. AES-256-GCM with a fresh ephemeral key and
nonce authenticates the SQLite bytes and synthetic metadata; strict metadata,
same-exercise identity and snapshot hash are checked after authentication.
The decrypted snapshot is deserialized and checked for integrity, expected object
shape and exact generated rows before a staging file is created. Publication uses
`os.link` for a new-only destination, with no overwrite fallback; unsupported hard
links fail closed. Temporary plaintext staging and recovered SQLite exist inside
the exercise directory until cleanup. No secure erasure is claimed.

Run using an already available compatible Python/cryptography environment:

```text
python -I -B -m unittest discover -s prototypes/synthetic_encrypted_backup -p test_sqlite_exercise.py -v
python -I -B prototypes/synthetic_encrypted_backup/sqlite_exercise.py
```

The 2026-11-24 run used existing **cryptography 46.0.3** and SQLite 3.51.0, not
the prototype's pinned 50.0.2; no dependency was installed or changed. Eight
initial SQLite tests contained six errors caused by a WAL-header image not being
openable via in-memory deserialization; that was fixed by normalizing the copy.
An initial isolated CLI smoke test also failed because Python `-I` omitted the
script directory; the import was corrected. The final expanded **12 SQLite tests**,
original **19 JSON tests**, and isolated CLI passed. These are synthetic checks,
not evidence for all SQLite configurations or real application backups.

The key is not persisted or reliably zeroized; the output is intentionally not
recoverable after context exit. There is no key recovery, app/schema migration,
real user input, durable backup, retention, crash/power-loss durability, concurrent
writer stress, authenticated human identity, filesystem-adversary or production
guarantee. WAL is tested with one committed and one uncommitted synthetic writer,
not exhaustive concurrency. Same-user code can access private Python attributes.
The existing release and real-data storage gates remain open.

**Not a MigraMind backup tool.** No SQLite, app imports, input files, key files,
browser storage or user paths. Python **3.10+**; separate dependencies in this
directory only. Production requirements/locks are unchanged.

Each run generates 4-8 random **SYNTHETIC_ONLY** JSON records and one fresh
256-bit AES key in memory. PyCA `cryptography==50.0.2` implements **AES-256-GCM**,
with a random 12-byte nonce and 16-byte authentication tag. A fresh key is used
for every exercise; there is no reuse/counter/rotation service. The v1 envelope
is a prototype format, not a cryptographic algorithm:

```text
MAGIC | version (1 byte) | metadata length (2-byte big endian)
      | canonical JSON metadata | nonce (12 bytes) | ciphertext + tag
```

The entire exact header, including metadata and nonce, is associated data.
Metadata is authenticated before JSON parsing, then strict version, algorithm,
classification, schema, identity/count, duplicate-key and canonical-encoding
checks apply. Decrypted data must match this run's generated schema and batch.
Inputs are bounded at 64 KiB, metadata at 2 KiB. There is no user-data encryption
API/CLI; the command refuses every argument.

## Safe isolated setup and run

Never install into the app's `.venv` or use real data to try this experiment.
Run the following Python setup **from the repository root** using a standalone
Python 3.10+ interpreter (save the block as a temporary script if needed). It
creates its own new venv, uses only the prototype requirement file, verifies an
official pip wheel, and works without system `ensurepip`. No system packages,
credentials or existing environments are modified. Network access to public
PyPI is needed. Do not bypass TLS or add an alternate unreviewed index on failure.

```python
from pathlib import Path
import hashlib, json, os, subprocess, sys, tempfile, urllib.request

source = Path('prototypes/synthetic_encrypted_backup').resolve()
assert (source / 'requirements.txt').is_file()
run = Path(tempfile.mkdtemp(prefix='migramind-aead-setup-'))
(run / 'tmp').mkdir()
(run / 'empty.netrc').write_text('')
allowed = {'PATH', 'SYSTEMROOT', 'WINDIR', 'COMSPEC', 'PATHEXT',
           'USERPROFILE', 'LOCALAPPDATA', 'HOMEDRIVE', 'HOMEPATH'}
env = {k: v for k, v in os.environ.items() if k.upper() in allowed}
env.update(PIP_CONFIG_FILE=os.devnull, NETRC=str(run / 'empty.netrc'),
           TEMP=str(run / 'tmp'), TMP=str(run / 'tmp'), TMPDIR=str(run / 'tmp'))
subprocess.run([sys.executable, '-I', '-B', '-m', 'venv', '--without-pip',
                str(run / 'venv')], check=True, timeout=90, env=env)
py = run / ('venv/Scripts/python.exe' if os.name == 'nt' else 'venv/bin/python')
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
with opener.open('https://pypi.org/pypi/pip/26.3/json', timeout=20) as response:
    meta = json.load(response)
assert not meta['info']['yanked'] and not meta['vulnerabilities']
item = next(x for x in meta['urls'] if x['filename'] == 'pip-26.3-py3-none-any.whl')
assert item['url'].startswith('https://files.pythonhosted.org/')
with opener.open(item['url'], timeout=20) as response:
    wheel_bytes = response.read()
assert hashlib.sha256(wheel_bytes).hexdigest() == item['digests']['sha256']
wheel = run / item['filename']
wheel.write_bytes(wheel_bytes)
launch = ("import sys,runpy;sys.path.insert(0,sys.argv.pop(1));"
          "runpy.run_module('pip',run_name='__main__',alter_sys=True)")
flags = ['--isolated', '--disable-pip-version-check', '--no-input', '--no-cache-dir',
         'install', '--index-url', 'https://pypi.org/simple', '--only-binary=:all:',
         '--timeout', '20', '--retries', '1', '--resume-retries', '0']
subprocess.run([str(py), '-I', '-B', '-c', launch, str(wheel), *flags, 'pip==26.3'],
               check=True, timeout=180, env=env)
subprocess.run([str(py), '-I', '-B', '-m', 'pip', *flags, '-r',
                str(source / 'requirements.txt')], check=True, timeout=240, env=env)
subprocess.run([str(py), '-I', '-B', '-m', 'pip', 'check'],
               check=True, timeout=30, env=env)
subprocess.run([str(py), '-I', '-B', '-m', 'unittest', 'discover', '-s', str(source),
                '-p', 'test_prototype.py', '-v'], check=True, timeout=120, env=env)
subprocess.run([str(py), '-I', '-B', str(source / 'prototype.py')],
               check=True, timeout=30, env=env)
print('Prototype environment retained for review:', run)
```

Dependencies: `cryptography==50.0.2`, `cffi==2.1.1`, `pycparser==3.11`, plus
`typing_extensions==4.16.0` on Python <3.11. Versions were checked against public
PyPI metadata; artifact hashes/install reports are recorded in the Phase 6
documentation. This is not application lock modification, a full advisory scan,
package-signature verification or FIPS certification. Refresh metadata before
future installs; untrusted package contents remain dangerous.

## Recovery and key lifecycle

Keys never enter arguments, environment variables, output, files or backup
metadata. There is no hardcoded key or persisted decryption key beside the
backup. `TemporaryDirectory` owns all generated files and removes them on normal
context exit; references to keys/plaintext are dropped even on context failure.
After process/context exit the backup is intentionally **not recoverable**.
This is not key escrow or durable recovery. Python immutable bytes, native
buffers, debugger access, paging and OS crash dumps cannot be reliably zeroized
or protected by this demo. Abnormal termination may leave synthetic files;
cleanup is not secure erasure. No host ACL/encryption policy is changed.

Authentication and validation finish in memory before any plaintext staging.
Recovery writes a new `mkstemp` file inside the owned sandbox, flushes/fsyncs it,
then atomically **publishes a new name** with a hard link. No `os.replace`,
overwriting fallback or caller-selected destination exists. Existing targets,
including a concurrent publication, are preserved. Unsupported hard links fail
closed. Staging is cleaned on failure where possible, with context cleanup as
fallback. Atomic publication is not a filesystem/power-loss durability proof;
directory fsync, disk-full/crash fault testing and hostile multiuser races are
not established. The no-clobber guarantee does not protect an unlocked sandbox
from other processes running as the same OS user.

Tests exercise wrong key, metadata/ciphertext/nonce/tag changes, truncation,
length/version/format/schema/duplicate-key validation, authenticated malformed
payloads, no staging before validation, I/O failure and publication races,
unchanged valid recovery targets and context cleanup. Test resealing always
uses a fresh nonce; keys/payloads are never failure-assertion operands or output.

## What remains unproved

No live SQLite/WAL snapshot consistency, account isolation after database
restore, session revocation, retention/withdrawal reconciliation, off-host
backup, durable keys/KMS, operator identities, signatures/PKI, OS permissions,
another device, deployment or clinical/privacy compliance. AES-GCM authenticates
possession of the ephemeral symmetric key, not a named backup operator; a key
holder can forge a new archive. A production format/capture/key lifecycle needs
separate design and approval. Do not remove these boundaries to use real data.
See [data protection plan](../../docs/DATA_PROTECTION_PLAN.md) and
[release gates](../../docs/RELEASE_READINESS.md).

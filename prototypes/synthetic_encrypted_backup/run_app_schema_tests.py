"""Launch synthetic model tests with isolated imports and no environment files."""
import os
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[2]
prototype = Path(__file__).resolve().parent
site = root / 'backend' / '.venv' / ('Lib/site-packages' if os.name == 'nt' else 'lib')
if os.name != 'nt':
    candidates = list(site.glob('python*/site-packages')) if site.exists() else []
    if len(candidates) != 1: raise SystemExit('Existing backend dependencies unavailable')
    site = candidates[0]
if not site.is_dir(): raise SystemExit('Existing backend dependencies unavailable')
allowed = {'PATH', 'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'TMPDIR'}
env = {k: v for k, v in os.environ.items() if k.upper() in allowed}
env.update(DATABASE_URL='sqlite://', APP_ENV='development', DATA_MODE='local',
           MIGRAMIND_SYNTHETIC_SCHEMA_TEST='isolated-model-exercise')
launch = ('import sys,runpy; sys.path.insert(0,sys.argv[3]); sys.path.insert(0,sys.argv[1]); '
          'sys.path.insert(0,sys.argv[2]); sys.argv=sys.argv[:1]; '
          'runpy.run_module("application_schema_tests",run_name="__main__",alter_sys=True)')
result = subprocess.run([sys.executable, '-I', '-B', '-c', launch, str(prototype),
                         str(root / 'backend'), str(site)], env=env, timeout=120)
raise SystemExit(result.returncode)

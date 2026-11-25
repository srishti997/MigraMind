"""Launch versioned synthetic checks with the Phase 2C restricted environment."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_app_schema_tests import run

if __name__ == '__main__':
    raise SystemExit(run('versioned_tests'))

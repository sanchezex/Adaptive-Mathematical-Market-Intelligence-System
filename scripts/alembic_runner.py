"""Small helper to run alembic programmatically using env vars.

Usage:
    python3 scripts/alembic_runner.py upgrade head
    python3 scripts/alembic_runner.py downgrade -1
"""
import sys
import subprocess
from pathlib import Path


def main(argv):
    here = Path(__file__).resolve().parents[1]
    # ensure alembic package available
    cmd = [sys.executable, '-m', 'alembic'] + argv
    # set working dir to repo root so alembic.ini is found
    subprocess.check_call(cmd, cwd=str(here))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('usage: alembic args...')
        sys.exit(1)
    main(sys.argv[1:])

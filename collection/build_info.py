"""Версия сборки для /health/ (файл BUILD_COMMIT.txt создаётся при build)."""

import os
from pathlib import Path

_BUILD_FILE = Path(__file__).resolve().parent.parent / 'BUILD_COMMIT.txt'


def get_git_commit() -> str | None:
    commit = os.environ.get('DJANGO_BUILD_COMMIT', '').strip()
    if not commit and _BUILD_FILE.is_file():
        commit = _BUILD_FILE.read_text(encoding='utf-8').strip()
    return commit or None

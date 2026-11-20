"""SQLite connection helper for HRA-001.

SQLite foreign-key enforcement is a per-connection setting, not a property
stored permanently in the database file. Every application connection must be
created through get_connection() so PRAGMA foreign_keys is enabled and checked.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Union

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "app.db"


def get_connection(
    db_path: Union[str, Path, None] = None,
    *,
    create: bool = False,
    read_only: bool = False,
    timeout: float = 30.0,
) -> sqlite3.Connection:
    """Return a SQLite connection with FK enforcement enabled.

    Args:
        db_path: Optional database path. Defaults to ``data/app.db``.
        create: Set True only for database generation/setup. Normal application
            code should leave this False to avoid silently creating an empty DB.
        read_only: Set True for safe read-only queries from the application.
        timeout: SQLite lock timeout in seconds.

    Raises:
        FileNotFoundError: If the database does not exist and create=False.
        RuntimeError: If the SQLite runtime does not enable foreign keys.
    """
    path = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
    path = path.expanduser().resolve()
    if not path.exists() and not create:
        raise FileNotFoundError(
            f"Database not found at {path}. Run `python src/generate_data.py` first."
        )
    if create:
        path.parent.mkdir(parents=True, exist_ok=True)

    if read_only:
        uri_path = f"file:{path.as_posix()}?mode=ro"
        conn = sqlite3.connect(uri_path, uri=True, timeout=timeout)
    else:
        conn = sqlite3.connect(str(path), timeout=timeout)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    enabled = conn.execute("PRAGMA foreign_keys").fetchone()[0]
    if enabled != 1:
        conn.close()
        raise RuntimeError("SQLite foreign-key enforcement could not be enabled.")
    return conn

# debug_db.py
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any
from .db import DB_PATH


TARGET_TABLES = ["users", "images", "distributions", "leaks"]


def resolve_db_path(db_name: str = "drm.db") -> Path:
    """
    Resolve database path in a predictable way:
    1) If db_name is absolute, use it
    2) Else resolve from current working directory
    """
    p = Path(db_name)
    return p if p.is_absolute() else (Path.cwd() / p).resolve()


def connect_db(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def list_tables(conn: sqlite3.Connection) -> list[str]:
    query = """
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        ORDER BY name
    """
    rows = conn.execute(query).fetchall()
    return [r["name"] for r in rows]


def fetch_all_rows(conn: sqlite3.Connection, table_name: str) -> list[dict[str, Any]]:
    rows = conn.execute(f"SELECT * FROM {table_name}").fetchall()
    return [dict(r) for r in rows]


def debug_database(db_name: str = "drm.db") -> dict[str, Any]:
    result: dict[str, Any] = {
        "db_path": None,
        "exists": False,
        "connected": False,
        "tables": [],
        "data": {},
        "errors": [],
    }

    db_path = resolve_db_path(db_name)
    result["db_path"] = str(db_path)
    result["exists"] = db_path.exists()

    print(f"[INFO] Database absolute path: {db_path}")
    print(f"[INFO] File exists: {db_path.exists()}")

    try:
        with connect_db(db_path) as conn:
            result["connected"] = True
            print("[INFO] SQLite connection successful.")

            tables = list_tables(conn)
            result["tables"] = tables
            print(f"[INFO] Tables found: {tables if tables else 'None'}")

            for table in TARGET_TABLES:
                if table not in tables:
                    msg = f"Table '{table}' does not exist."
                    print(f"[WARN] {msg}")
                    result["errors"].append(msg)
                    continue

                rows = fetch_all_rows(conn, table)
                result["data"][table] = rows
                print(f"[INFO] {table}: {len(rows)} row(s)")
                for i, row in enumerate(rows, start=1):
                    print(f"  {table}[{i}] -> {row}")

    except sqlite3.Error as e:
        msg = f"SQLite error: {e}"
        print(f"[ERROR] {msg}")
        result["errors"].append(msg)
    except Exception as e:
        msg = f"Unexpected error: {e}"
        print(f"[ERROR] {msg}")
        result["errors"].append(msg)

    return result


if __name__ == "__main__":
    # Change this if needed:
    # debug_database("ethical_drm/drm.db")
    debug_database(str(DB_PATH))

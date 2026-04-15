from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).resolve().parents[1] / "drm.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _column_names(cursor: sqlite3.Cursor, table_name: str) -> set[str]:
    cursor.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cursor.fetchall()}


def _ensure_users_schema(cursor: sqlite3.Cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE
        )
        """
    )

    columns = _column_names(cursor, "users")
    if "username" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN username TEXT")
    if "password_hash" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")

    cursor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username_unique
        ON users(username)
        """
    )


def init_db() -> None:
    with get_connection() as conn:
        cursor = conn.cursor()

        _ensure_users_schema(cursor)

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT,
                uploaded_by TEXT
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS distributions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_id INTEGER,
                user_id TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS leaks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_path TEXT,
                detected_user TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS auth_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                session_token TEXT UNIQUE NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        conn.commit()


# =========================
# AUTH OPERATIONS
# =========================
def create_user(username: str, password_hash: str) -> bool:
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, user_id)
                VALUES (?, ?, ?)
                """,
                (username, password_hash, username),
            )
            conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def get_user_by_username(username: str) -> sqlite3.Row | None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, username, password_hash, user_id
            FROM users
            WHERE username = ?
            """,
            (username,),
        )
        return cursor.fetchone()


def create_auth_session(username: str, session_token: str) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO auth_sessions (username, session_token)
            VALUES (?, ?)
            """,
            (username, session_token),
        )
        conn.commit()


def get_auth_session(session_token: str) -> sqlite3.Row | None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT username, session_token
            FROM auth_sessions
            WHERE session_token = ?
            """,
            (session_token,),
        )
        return cursor.fetchone()


def delete_auth_session(session_token: str) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM auth_sessions WHERE session_token = ?",
            (session_token,),
        )
        conn.commit()


# =========================
# IMAGE OPERATIONS
# =========================
def insert_image(file_path, uploaded_by):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO images (file_path, uploaded_by) VALUES (?, ?)",
            (file_path, uploaded_by),
        )
        conn.commit()
        return cursor.lastrowid


def get_image_id(file_path):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM images WHERE file_path=?",
            (file_path,),
        )
        row = cursor.fetchone()
        return row[0] if row else None


def get_image_by_path(file_path):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM images WHERE file_path=?",
            (file_path,),
        )
        row = cursor.fetchone()
        return row[0] if row else None


def insert_image_if_not_exists(file_path, uploaded_by):
    """
    Returns image_id.
    If the image already exists -> returns existing id.
    Else -> inserts and returns new id.
    """
    existing_id = get_image_by_path(file_path)
    if existing_id:
        return existing_id
    return insert_image(file_path, uploaded_by)


# =========================
# DISTRIBUTION OPERATIONS
# =========================
def insert_distribution(image_id, user_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO distributions (image_id, user_id) VALUES (?, ?)",
            (image_id, user_id),
        )
        conn.commit()


def fetch_users_by_image(image_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id FROM distributions WHERE image_id=?",
            (image_id,),
        )
        return [row[0] for row in cursor.fetchall()]


# =========================
# LEAK OPERATIONS
# =========================
def insert_leak(image_path, user_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO leaks (image_path, detected_user) VALUES (?, ?)",
            (image_path, user_id),
        )
        conn.commit()

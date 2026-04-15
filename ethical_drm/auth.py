import hashlib
import hmac
import os
import secrets

from database.db import (
    create_auth_session,
    create_user,
    delete_auth_session,
    get_auth_session,
    get_user_by_username,
)

PBKDF2_ALGORITHM = "sha256"
PBKDF2_ITERATIONS = 200_000
SALT_SIZE = 16


def _hash_password(password: str, salt: bytes | None = None) -> str:
    if salt is None:
        salt = os.urandom(SALT_SIZE)

    pwd_hash = hashlib.pbkdf2_hmac(
        PBKDF2_ALGORITHM,
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )

    return f"pbkdf2_{PBKDF2_ALGORITHM}${PBKDF2_ITERATIONS}${salt.hex()}${pwd_hash.hex()}"


def _verify_password(password: str, stored_password_hash: str) -> bool:
    try:
        algo, iterations, salt_hex, expected_hash_hex = stored_password_hash.split("$")
        if algo != f"pbkdf2_{PBKDF2_ALGORITHM}":
            return False

        new_hash = hashlib.pbkdf2_hmac(
            PBKDF2_ALGORITHM,
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterations),
        ).hex()

        return hmac.compare_digest(new_hash, expected_hash_hex)
    except (ValueError, TypeError):
        return False


def register_user(username: str, password: str) -> tuple[bool, str]:
    username = username.strip()

    if len(username) < 3:
        return False, "Username must be at least 3 characters."
    if len(password) < 8:
        return False, "Password must be at least 8 characters."

    password_hash = _hash_password(password)
    created = create_user(username, password_hash)

    if not created:
        return False, "Username already exists."

    return True, "Account created successfully."


def authenticate_user(username: str, password: str) -> bool:
    user = get_user_by_username(username.strip())

    if not user:
        return False

    stored_hash = user["password_hash"]
    if not stored_hash:
        return False

    return _verify_password(password, stored_hash)


def create_login_session(username: str) -> str:
    session_token = secrets.token_urlsafe(32)
    create_auth_session(username=username.strip(), session_token=session_token)
    return session_token


def restore_login_from_token(session_token: str) -> str | None:
    session = get_auth_session(session_token)
    if not session:
        return None
    return session["username"]


def logout_session(session_token: str) -> None:
    delete_auth_session(session_token)

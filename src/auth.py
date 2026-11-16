"""Login and signed session tokens.

The user's role is decided by the server at login and stored inside a signed token. Every
/ask request must carry that token, and the API reads the role from it. The role is never
taken from the question text or from a field the user can edit, so a student cannot claim
to be a lecturer. In a real deployment the role would come from university single sign-on.
"""
import base64
import hashlib
import hmac
import logging
import os
import secrets
import time

# The signing key must not live in the repository: anyone who read a hard-coded key could
# forge an admin token. If SESSION_SECRET is not set we generate a random key per process,
# so tokens simply stop working after a restart (users log in again).
_env_secret = os.getenv("SESSION_SECRET")
if _env_secret:
    SECRET = _env_secret.encode()
else:
    SECRET = secrets.token_bytes(32)
    logging.getLogger(__name__).warning(
        "SESSION_SECRET not set: using a random per-process key (tokens reset on restart)")
TTL_SECONDS = 8 * 3600

# Demo user directory: username -> role (stands in for the university's identity system).
USERS = {"student1": "student", "lecturer1": "lecturer", "admin1": "admin"}


def _sign(payload: bytes) -> str:
    return hmac.new(SECRET, payload, hashlib.sha256).hexdigest()


def issue_token(username: str) -> str:
    role = USERS[username]
    payload = f"{username}|{role}|{int(time.time()) + TTL_SECONDS}".encode()
    return base64.urlsafe_b64encode(payload).decode() + "." + _sign(payload)


def read_token(token: str) -> dict:
    """Returns {"username", "role"} or raises ValueError if the token is invalid or expired."""
    try:
        b64, sig = token.rsplit(".", 1)
        payload = base64.urlsafe_b64decode(b64.encode())
    except Exception as e:
        raise ValueError("malformed token") from e
    if not hmac.compare_digest(_sign(payload), sig):
        raise ValueError("bad signature")
    try:
        username, role, exp = payload.decode().split("|")
        exp = int(exp)
    except ValueError as e:
        raise ValueError("malformed token") from e
    if exp < time.time():
        raise ValueError("token expired")
    if USERS.get(username) != role:
        raise ValueError("role no longer valid")
    return {"username": username, "role": role}

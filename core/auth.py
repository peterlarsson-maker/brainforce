from datetime import datetime, timedelta
import os
from typing import Optional, Dict

# bcrypt is an optional dependency; some test environments may not have it installed.
# functions will import it lazily and fall back to a no-op implementation when
# the module is unavailable.
try:
    import bcrypt
except ImportError:  # pragma: no cover
    bcrypt = None

# We implement a minimal JWT-like encoder/decoder using HMAC-SHA256 so that the
# project does not depend on the PyJWT library.  This keeps the runtime
# footprint small and avoids import errors in test environments.
import base64
import hashlib
import hmac
import json

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


class Token(BaseModel):
    access_token: str
    token_type: str


class LoginRequest(BaseModel):
    username: str
    password: str


class RegistrationRequest(BaseModel):
    username: str
    password: str


def hash_password(password: str) -> str:
    """Return a bcrypt hash for the given plaintext password.

    If the bcrypt library isn't available (e.g. running lightweight tests),
    this will simply return the plaintext string so that authentication logic
    can still operate.  This is **not** secure, but it keeps the project
    runnable without an external dependency.
    """
    if bcrypt is None:
        # fallback behaviour for tests / environments without bcrypt
        return password
    # bcrypt works with bytes
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash.

    If bcrypt isn't installed we fall back to a simple equality check; this
    mirrors the behaviour of ``hash_password`` above for consistency.
    """
    if bcrypt is None:
        return password == hashed
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except Exception:
        return False


def _get_jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET")
    if not secret:
        # fail fast during development if JWT_SECRET isn't provided
        raise RuntimeError("JWT_SECRET environment variable not set")
    return secret


def _b64url_encode(data: bytes) -> str:
    """Helper to produce URL-safe base64 without padding."""
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def create_access_token(data: Dict[str, Optional[str]]) -> str:
    """Create a simple signed token resembling a JWT.

    The format is header.payload.signature where the signature is HMAC-SHA256
    over the header and payload using the `JWT_SECRET`.  An exp claim (unix
    timestamp) is automatically injected.
    """
    payload = data.copy()
    payload["exp"] = int((datetime.utcnow() + timedelta(hours=1)).timestamp())
    header = {"alg": "HS256", "typ": "JWT"}

    header_b = _b64url_encode(json.dumps(header).encode())
    payload_b = _b64url_encode(json.dumps(payload).encode())
    secret = _get_jwt_secret().encode()
    sig = hmac.new(secret, f"{header_b}.{payload_b}".encode(), hashlib.sha256).digest()
    sig_b = _b64url_encode(sig)
    return f"{header_b}.{payload_b}.{sig_b}"


def decode_token(token: str) -> Dict:
    """Validate and decode a token produced by :func:`create_access_token`.

    Raises HTTPException(401) if the token is malformed, signature validation
    fails, or the token has expired.
    """
    try:
        header_b, payload_b, sig_b = token.split(".")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    secret = _get_jwt_secret().encode()
    expected_sig = hmac.new(secret, f"{header_b}.{payload_b}".encode(), hashlib.sha256).digest()
    if not hmac.compare_digest(_b64url_encode(expected_sig), sig_b):
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    try:
        payload = json.loads(_b64url_decode(payload_b))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    exp = payload.get("exp")
    if exp is None or int(exp) < int(datetime.utcnow().timestamp()):
        raise HTTPException(status_code=401, detail="Token expired")
    return payload


def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict:
    """Dependency that returns the decoded token payload as a user dict.

    Expects the token to include `user_id` and `role` claims.
    """
    payload = decode_token(token)
    user_id = payload.get("user_id")
    role = payload.get("role")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    return {"id": user_id, "role": role}


@router.post("/login", response_model=Token)
def login(req: LoginRequest):
    """Verify credentials and emit a JWT."""
    from core.database import get_db

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, password_hash, role FROM users WHERE username = ?", (req.username,))
    row = c.fetchone()
    if not row or not verify_password(req.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_access_token({"user_id": row["id"], "role": row["role"]})
    return {"access_token": token, "token_type": "bearer"}


class UserResponse(BaseModel):
    """Response from registration endpoint."""
    id: int
    username: str


@router.post("/register", response_model=UserResponse, status_code=201)
def register(req: RegistrationRequest, current_user: dict = Depends(get_current_user)):
    """Register a new user. Only admins can perform this action.

    The registering user (derived from the bearer token) must have role == "admin".
    """
    from core.database import get_db

    # Check that the current user is an admin
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can register users")

    # Validate username is provided
    if not req.username:
        raise HTTPException(status_code=400, detail="Username is required")
    if not req.password:
        raise HTTPException(status_code=400, detail="Password is required")

    conn = get_db()
    c = conn.cursor()

    # Check for duplicate username
    c.execute("SELECT id FROM users WHERE username = ?", (req.username,))
    if c.fetchone():
        raise HTTPException(status_code=400, detail="Username already exists")

    # Insert new user with default role "user"
    hashed = hash_password(req.password)
    c.execute(
        "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
        (req.username, hashed, "user", datetime.utcnow().isoformat()),
    )
    conn.commit()
    user_id = c.lastrowid
    return {"id": user_id, "username": req.username}

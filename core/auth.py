from datetime import datetime, timedelta
import os
from typing import Optional, Dict

# bcrypt is a required dependency for secure password hashing.
try:
    import bcrypt
except ImportError as e:
    raise RuntimeError(f"bcrypt library is required for password hashing. Install it: pip install bcrypt") from e

# We implement a minimal JWT-like encoder/decoder using HMAC-SHA256 so that the
# project does not depend on the PyJWT library.  This keeps the runtime
# footprint small and avoids import errors in test environments.
import base64
import hashlib
import hmac
import json

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# Simple in-memory rate limiter for login attempts
# Tracks failed login attempts per IP address with expiration after 5 minutes
_login_attempts = {}  # {ip: [(timestamp, failed), ...]}
_RATE_LIMIT_MAX_ATTEMPTS = 5
_RATE_LIMIT_WINDOW_SECONDS = 300  # 5 minutes


def _get_client_ip(request: Request) -> str:
    """Extract client IP from request, handling X-Forwarded-For header."""
    if request.headers.get("x-forwarded-for"):
        return request.headers.get("x-forwarded-for").split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _check_rate_limit(ip: str) -> bool:
    """Check if IP is within rate limit. Remove expired entries. Returns True if OK."""
    now = datetime.utcnow().timestamp()
    
    # Clean up expired entries
    if ip in _login_attempts:
        _login_attempts[ip] = [
            ts for ts in _login_attempts[ip]
            if now - ts < _RATE_LIMIT_WINDOW_SECONDS
        ]
        if not _login_attempts[ip]:
            del _login_attempts[ip]
    
    # Check limit
    if ip in _login_attempts and len(_login_attempts[ip]) >= _RATE_LIMIT_MAX_ATTEMPTS:
        return False
    return True


def _record_failed_login(ip: str) -> None:
    """Record a failed login attempt for the given IP."""
    now = datetime.utcnow().timestamp()
    if ip not in _login_attempts:
        _login_attempts[ip] = []
    _login_attempts[ip].append(now)


def _reset_login_attempts(ip: str) -> None:
    """Reset (clear) login attempts for the given IP after successful login."""
    if ip in _login_attempts:
        del _login_attempts[ip]


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

    Requires bcrypt to be installed. Raises RuntimeError if bcrypt is unavailable.
    """
    # bcrypt works with bytes
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash.

    Requires bcrypt to be installed. Raises RuntimeError if bcrypt is unavailable.
    """
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

    Performs strict validation:
    - Token must have 3 parts (header.payload.signature)
    - Header algorithm must be HS256
    - Signature must be valid
    - Payload must include user_id, role, and exp claims
    - Token must not be expired

    Raises HTTPException(401) if any validation fails.
    """
    try:
        header_b, payload_b, sig_b = token.split(".")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    # Validate signature first (no change to existing logic)
    secret = _get_jwt_secret().encode()
    expected_sig = hmac.new(secret, f"{header_b}.{payload_b}".encode(), hashlib.sha256).digest()
    if not hmac.compare_digest(_b64url_encode(expected_sig), sig_b):
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    # Decode and validate header
    try:
        header = json.loads(_b64url_decode(header_b))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    if header.get("alg") != "HS256":
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    # Decode and validate payload
    try:
        payload = json.loads(_b64url_decode(payload_b))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    # Validate required claims are present
    if payload.get("user_id") is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    if payload.get("role") is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    if payload.get("exp") is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    # Validate token is not expired
    exp = payload["exp"]
    try:
        exp_timestamp = int(exp)
    except (ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    if exp_timestamp < int(datetime.utcnow().timestamp()):
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
def login(req: LoginRequest, request: Request):
    """Verify credentials and emit a JWT.
    
    Rate limited to 5 failed attempts per IP per 5 minutes.
    """
    ip = _get_client_ip(request)
    
    # Check rate limit before processing
    if not _check_rate_limit(ip):
        raise HTTPException(status_code=429, detail="Too many failed login attempts. Try again later.")
    
    from core.database import get_db

    conn = get_db()
    try:
        c = conn.cursor()
        c.execute("SELECT id, password_hash, role FROM users WHERE username = ?", (req.username,))
        row = c.fetchone()
        if not row or not verify_password(req.password, row["password_hash"]):
            # Record failed attempt and return 401
            _record_failed_login(ip)
            raise HTTPException(status_code=401, detail="Invalid username or password")
        # Successful login: reset rate limit counter
        _reset_login_attempts(ip)
        token = create_access_token({"user_id": row["id"], "role": row["role"]})
        return {"access_token": token, "token_type": "bearer"}
    finally:
        conn.close()


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
    try:
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
    finally:
        conn.close()

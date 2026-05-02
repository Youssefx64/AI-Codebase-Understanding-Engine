"""JWT authentication and password-hashing service."""

from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from jose import JWTError, jwt

from core.config import get_settings
from core.exceptions import AppError
from core.logging import get_logger

logger = get_logger(__name__)

TOKEN_TYPE = "bearer"
ALGORITHM = "HS256"


class AuthService:
    """Stateless service for password hashing and JWT management."""

    def __init__(self) -> None:
        self._settings = get_settings()

    # ── Password ──────────────────────────────────────────────────────────────

    def hash_password(self, plain: str) -> str:
        return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def verify_password(self, plain: str, hashed: str) -> bool:
        try:
            return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
        except Exception:
            return False

    # ── JWT ───────────────────────────────────────────────────────────────────

    def create_access_token(self, user_id: str, email: str) -> str:
        expire = datetime.utcnow() + timedelta(
            minutes=self._settings.jwt_access_token_expire_minutes
        )
        payload = {
            "sub": user_id,
            "email": email,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access",
        }
        return jwt.encode(payload, self._settings.jwt_secret, algorithm=ALGORITHM)

    def decode_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(
                token, self._settings.jwt_secret, algorithms=[ALGORITHM]
            )
            return payload
        except JWTError as exc:
            raise AppError(
                code="INVALID_TOKEN",
                message="Could not validate credentials.",
                status_code=401,
            ) from exc

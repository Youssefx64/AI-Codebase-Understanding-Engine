"""Auth routes: register, login, me."""

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select

from core.exceptions import AppError
from core.logging import get_logger
from infrastructure.database.orm_models import UserORM
from infrastructure.database.postgres import get_session
from services.auth_service import AuthService, TOKEN_TYPE

import uuid

router = APIRouter(prefix="/auth", tags=["Auth"])
logger = get_logger(__name__)


# ── Request / Response schemas ────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: str = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, description="Minimum 8 characters")


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = TOKEN_TYPE
    user_id: str
    email: str
    username: str


class UserProfile(BaseModel):
    user_id: str
    email: str
    username: str
    created_at: str


# ── Dependency: extract current user from Authorization header ────────────────

async def get_current_user(authorization: str = Header(default="")) -> UserORM:
    """Parse Bearer token and return the UserORM row."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.removeprefix("Bearer ").strip()
    svc = AuthService()
    try:
        payload = svc.decode_token(token)
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    user_id = payload.get("sub")
    async with get_session() as session:
        user = await session.get(UserORM, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest) -> TokenResponse:
    svc = AuthService()

    async with get_session() as session:
        existing_email = await session.execute(
            select(UserORM).where(UserORM.email == payload.email)
        )
        if existing_email.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Email already registered")

        existing_username = await session.execute(
            select(UserORM).where(UserORM.username == payload.username)
        )
        if existing_username.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Username already taken")

        user = UserORM(
            user_id=str(uuid.uuid4()),
            email=payload.email,
            username=payload.username,
            hashed_password=svc.hash_password(payload.password),
        )
        session.add(user)

    logger.info("User registered", user_id=user.user_id, email=user.email)

    token = svc.create_access_token(user.user_id, user.email)
    return TokenResponse(
        access_token=token,
        user_id=user.user_id,
        email=user.email,
        username=user.username,
    )


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest) -> TokenResponse:
    svc = AuthService()

    async with get_session() as session:
        result = await session.execute(
            select(UserORM).where(UserORM.email == payload.email)
        )
        user = result.scalar_one_or_none()

    if not user or not svc.verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    logger.info("User logged in", user_id=user.user_id)

    token = svc.create_access_token(user.user_id, user.email)
    return TokenResponse(
        access_token=token,
        user_id=user.user_id,
        email=user.email,
        username=user.username,
    )


@router.get("/me", response_model=UserProfile)
async def me(current_user: UserORM = Depends(get_current_user)) -> UserProfile:
    return UserProfile(
        user_id=current_user.user_id,
        email=current_user.email,
        username=current_user.username,
        created_at=current_user.created_at.isoformat(),
    )

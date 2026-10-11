"""
User Authentication Router.

Endpoints for User Signup, Login, Profile Info (Me), and Logout.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

from app.core.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.core.database import get_supabase
from app.models.schemas import (
    AuthTokenResponse,
    MessageResponse,
    UserLoginRequest,
    UserResponse,
    UserSignupRequest,
)

router = APIRouter(prefix="/auth", tags=["User Authentication"])

# Local In-Memory Auth Fallback Store (email -> user_dict) if Supabase table is unavailable
IN_MEMORY_USERS: Dict[str, dict] = {}


@router.post("/signup", response_model=AuthTokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(payload: UserSignupRequest):
    """Registers a new user account and returns a JWT access token."""
    email_clean = payload.email.strip().lower()
    
    # Check if user already exists
    supabase = None
    try:
        supabase = get_supabase()
    except Exception:
        pass

    user_data = None

    if supabase:
        try:
            res = supabase.table("users").select("*").eq("email", email_clean).execute()
            if res.data and len(res.data) > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="An account with this email already exists.",
                )
        except HTTPException:
            raise
        except Exception as err:
            logger.warning(f"Supabase select users query failed, checking in-memory store: {err}")

    if email_clean in IN_MEMORY_USERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists.",
        )

    # Hash Password & Prepare User Record
    user_id = str(uuid.uuid4())
    pw_hash = hash_password(payload.password)
    created_at = datetime.now()

    new_user = {
        "id": user_id,
        "email": email_clean,
        "full_name": payload.full_name.strip(),
        "password_hash": pw_hash,
        "role": "user",
        "created_at": created_at.isoformat(),
    }

    # Save User to DB or Fallback
    saved = False
    if supabase:
        try:
            res = supabase.table("users").insert(new_user).execute()
            if res.data and len(res.data) > 0:
                user_data = res.data[0]
                saved = True
        except Exception as err:
            logger.warning(f"Failed to insert user into Supabase: {err}")

    if not saved:
        IN_MEMORY_USERS[email_clean] = new_user
        user_data = new_user

    # Generate JWT Token
    access_token = create_access_token(data={"sub": user_id, "email": email_clean, "name": payload.full_name})
    
    logger.success(f"User signed up successfully: {email_clean}")

    user_resp = UserResponse(
        id=user_data["id"],
        email=user_data["email"],
        full_name=user_data["full_name"],
        role=user_data.get("role", "user"),
        created_at=created_at,
    )

    return AuthTokenResponse(access_token=access_token, token_type="bearer", user=user_resp)


@router.post("/login", response_model=AuthTokenResponse)
async def login(payload: UserLoginRequest):
    """Authenticates user email & password and returns a JWT access token."""
    email_clean = payload.email.strip().lower()
    supabase = None
    try:
        supabase = get_supabase()
    except Exception:
        pass

    user_record = None

    if supabase:
        try:
            res = supabase.table("users").select("*").eq("email", email_clean).execute()
            if res.data and len(res.data) > 0:
                user_record = res.data[0]
        except Exception as err:
            logger.warning(f"Supabase login query error: {err}")

    if not user_record:
        user_record = IN_MEMORY_USERS.get(email_clean)

    if not user_record or not verify_password(payload.password, user_record["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate JWT Token
    access_token = create_access_token(
        data={
            "sub": user_record["id"],
            "email": user_record["email"],
            "name": user_record["full_name"],
        }
    )

    logger.info(f"User logged in: {email_clean}")

    user_resp = UserResponse(
        id=str(user_record["id"]),
        email=user_record["email"],
        full_name=user_record["full_name"],
        role=user_record.get("role", "user"),
    )

    return AuthTokenResponse(access_token=access_token, token_type="bearer", user=user_resp)


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    """Returns the profile information of the currently logged-in user."""
    return UserResponse(
        id=current_user["sub"],
        email=current_user.get("email", ""),
        full_name=current_user.get("name", "User"),
        role="user",
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(current_user: dict = Depends(get_current_user)):
    """Logs out current user session."""
    return MessageResponse(message=f"Logged out successfully for user {current_user.get('email')}")

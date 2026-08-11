from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from api.auth import authenticate_user, create_token
from api.schemas import TokenRequest, TokenResponse

router = APIRouter(tags=["auth"])


@router.post("/token", response_model=TokenResponse)
async def login(request: TokenRequest) -> TokenResponse:
    """Authenticate a user and issue a bearer token."""
    if not authenticate_user(request.username, request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_token(request.username)
    return TokenResponse(access_token=token, username=request.username)
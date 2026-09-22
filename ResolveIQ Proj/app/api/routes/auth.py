from fastapi import APIRouter, HTTPException, Depends, Header, status
from typing import Optional
from app.schemas.auth import UserLogin, UserRegister, UserResponse, JiraConnectionResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

_auth_service = AuthService()


def get_auth_service() -> AuthService:
    return _auth_service


def get_current_user(
    authorization: Optional[str] = Header(None),
    service: AuthService = Depends(get_auth_service)
) -> UserResponse:
    """Dependency that requires a valid ResolveIQ authenticated user."""
    return require_authenticated_user(authorization=authorization, service=service)


def require_authenticated_user(
    authorization: Optional[str] = Header(None),
    service: AuthService = Depends(get_auth_service)
) -> UserResponse:
    """Strict authentication dependency that requires a valid ResolveIQ user token."""
    if not authorization or not authorization.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to perform this action."
        )

    token = authorization.replace("Bearer ", "").strip()
    user = service.get_user_by_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token."
        )
    return user



@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new ResolveIQ user"
)
async def register_user(
    reg_data: UserRegister,
    service: AuthService = Depends(get_auth_service)
) -> UserResponse:
    try:
        return await service.register(reg_data)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )


@router.post(
    "/login",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Login to ResolveIQ account"
)
async def login_user(
    login_data: UserLogin,
    service: AuthService = Depends(get_auth_service)
) -> UserResponse:
    try:
        return await service.login(login_data)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(ve)
        )


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user profile"
)
async def get_me(
    current_user: UserResponse = Depends(require_authenticated_user)
) -> UserResponse:
    return current_user


@router.get(
    "/jira-connection",
    response_model=JiraConnectionResponse,
    status_code=status.HTTP_200_OK,
    summary="Check read-only Jira connection status for the authenticated user"
)
async def check_jira_connection(
    service: AuthService = Depends(get_auth_service)
) -> JiraConnectionResponse:
    """Verifies connected Jira account without exposing any tokens or credentials to the client."""
    return await service.get_jira_connection_status()

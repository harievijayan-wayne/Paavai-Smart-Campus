from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, UserRegisterRequest, Token, UserAuthResponse
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate user and generate JSON Web Token.
    Validates password hash and returns role context.
    """
    service = AuthService(db)
    return await service.authenticate(login_data)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    reg_data: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user account with role-specific profile (Student or Faculty).
    """
    service = AuthService(db)
    user = await service.register(reg_data)
    full_user = await service.user_repo.get_with_profile(user.id)
    return full_user


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve details and profile information of the currently authenticated user.
    """
    return current_user

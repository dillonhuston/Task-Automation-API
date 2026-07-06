"""
Authentication routes for Task Automation API.
Provides user registration, login, and token retrieval endpoints.
"""


from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user import User, UserCreate, UserLoginSuccess, UserLogin
from app.models.database import get_db

from app.services.user_service import UserService
from app.dependencies.dependency import get_userservice
from app.utils.logger import SingletonLogger

from app.Encryption_Services.keyGenerator import KeyHandler


router = APIRouter(prefix="/auth", tags=["Auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


logger = SingletonLogger().get_logger()
handler = KeyHandler()

@router.post("/register", response_model=User, status_code=201)
async def register(
    user: UserCreate,
    user_service: UserService = Depends(get_userservice),
    db: AsyncSession = Depends(get_db)) -> User:
   
    register =  await user_service.register_user(db, user)
    if not register:
        raise HTTPException(status_code=401, detail="Unable to register user")
    return register


@router.post("/login", response_model=UserLoginSuccess, status_code=200)
async def login(
    user: UserLogin,
    user_service: UserService = Depends(get_userservice),
    db: AsyncSession = Depends(get_db)):

    login =  await user_service.login_user(db, user)
    if not login:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return login
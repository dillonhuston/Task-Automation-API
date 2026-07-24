"""
Utility functions for authentication and token verification.
Provides get_current_user and admin_required dependencies.
"""

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.Database.DatabaseOperations import DatabaseOperations
from app.dependencies.dependency import get_jwt_handler, get_database_operations
from app.auth.jwt import JWTHandler

from ..dependencies.constants import HTTP_STATUS_UNAUTHORIZED
from ..models.database import get_db
from ..models.user import UserModel
from ..utils.logger import SingletonLogger

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


#TODO Remove all db calls, create this as a class service, also remove the fastapi HTTP constants and exception add global handlers instead of FastAPI default

def get_logger():
    """Return a singleton logger instance."""
    return SingletonLogger().get_logger()


async def get_current_user(
    jwthandler: JWTHandler = Depends(get_jwt_handler),
    databaseops: DatabaseOperations = Depends(get_database_operations),
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> UserModel:
    logger = get_logger()
    try:
        payload = await jwthandler.verify_token(token)
        logger.info("JWT payload: sub=%s id=%s", payload.get("sub"), payload.get("id"))

        user_id = payload.get("id")
        if not user_id:
            logger.error("Token missing 'id' user ID")
            raise HTTPException(
                status_code=HTTP_STATUS_UNAUTHORIZED,
                detail="Invalid authentication token"
            )

        user = await databaseops.GetUserByID(db, user_id)
        if not user:
            logger.warning("User not found in DB for ID %s", user_id)
            raise HTTPException(
                status_code=HTTP_STATUS_UNAUTHORIZED,
                detail="User not found or unauthorized"
            )

        return user

    except ValueError as exc:  # <-- MUST match JWTHandler.verify_token
        logger.error("Token verification failed: %s", exc)
        raise HTTPException(
            status_code=HTTP_STATUS_UNAUTHORIZED,
            detail="Invalid token"
        ) from exc


def admin_required(current_user: UserModel = Depends(get_current_user)) -> UserModel:
    """
    Ensure the current user has admin privileges.
    
    Raises:
        HTTPException: If user is not admin.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

"""
Utility functions for authentication and token verification.
Provides get_current_user and admin_required dependencies.
"""

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from ..auth.auth import verify_token
from ..dependencies.constants import HTTP_STATUS_UNAUTHORIZED
from ..models.database import get_db
from ..models.user import UserModel
from ..utils.logger import SingletonLogger

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


#TODO Remove all db calls, create this as a class service, also remove the fastapi HTTP constants and exception add global handlers instead of FastAPI default

def get_logger():
    """Return a singleton logger instance."""
    return SingletonLogger().get_logger()


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> UserModel:
    """
    Retrieve the current user based on JWT token and DB lookup.
    
    Raises:
        HTTPException: If token is invalid or user not found.
    """
    logger = get_logger()
    try:
        payload = verify_token(token)
        user_id = payload.get("sub")

        if user_id is None:
            logger.error("Token missing 'sub' user ID")
            raise HTTPException(
                status_code=HTTP_STATUS_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
        #TODO remove ALL these db calls 
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            logger.warning("User not found in DB for ID %s", user_id)
            raise HTTPException(
                status_code=HTTP_STATUS_UNAUTHORIZED,
                detail="User not found or unauthorized"
            )

        return user
    except jwt.InvalidTokenError as exc:
        logger.error("Invalid token format")
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

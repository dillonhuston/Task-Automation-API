import jwt
from datetime import datetime, timedelta, timezone
from typing import Any

from app.settings import settings
from app.utils.logger import SingletonLogger

logger = SingletonLogger().get_logger()


class JWTHandler:
    def __init__(self):
        self.secret = settings.JWT_SECRET.get_secret_value()
        self.algorithm = settings.JWT_ALGORITHM
        self.expiration_minutes = settings.JWT_EXPIRATION_MINUTES

    async def jwt_generate(self, payload: dict[str, Any]) -> str:
        
        to_encode = payload.copy()
        expire = datetime.now(timezone.utc) + timedelta(minutes=self.expiration_minutes)
        to_encode.update({"exp": expire})

        token = jwt.encode(to_encode, self.secret, algorithm=self.algorithm)
        logger.info("Token generated for user ID: %s", payload.get("id"))
        return token

    async def verify_token(self, token: str) -> dict:

        try:
            return jwt.decode(token, self.secret, algorithms=[self.algorithm])
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            raise ValueError("Invalid token provided")
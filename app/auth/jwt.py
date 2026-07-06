import jwt
from datetime import datetime, timedelta, timezone
from typing import Any
from app.config import Config
from app.utils.logger import SingletonLogger

class JWTHandler:
    def __init__(self, config: Config, logger: SingletonLogger):
        self.config = config
        self.logger = logger.get_logger()

    async def jwt_generate(self, payload: dict[str, Any]) -> str:
        to_encode = payload.copy()
        expire = datetime.now(timezone.utc) + timedelta(hours=24)
        to_encode.update({"exp": expire})
        
        token = jwt.encode(to_encode, self.config.SECRET_KEY, algorithm="HS256")
        self.logger.info("Token generated for user ID: %s", payload.get("id"))
        return token

    async def verify_token(self, token: str) -> dict:
        try:
            return jwt.decode(token, self.config.SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            self.logger.warning("Token expired")
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError:
            self.logger.warning("Invalid token")
            raise ValueError("Invalid token provided")
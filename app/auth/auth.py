"""Authentication module for JWT token creation, verification, and password hashing."""

from passlib.hash import  pbkdf2_sha256
from ..utils.logger import SingletonLogger


logger = SingletonLogger().get_logger()


class AuthService:
    def __init__(self): 
        pass
        

    def hash_password(self, password: str) -> str:
            return pbkdf2_sha256.hash(password)

    def verify_password(self, password: str, password_hash: str) -> bool:
            return pbkdf2_sha256.verify(password, password_hash)


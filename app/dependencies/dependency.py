from app.services.user_service import UserService
from app.Database.DatabaseOperations import DatabaseOperations
from app.auth.auth import AuthService
from app.Encryption_Services.keyGenerator import KeyHandler
from app.config import Config

from app.auth.jwt import JWTHandler
from app.utils.logger import SingletonLogger


def get_userservice():
    config = Config()

    logger = SingletonLogger()
    databaseops = DatabaseOperations()
    authservice = AuthService(config)
    keygen  = KeyHandler()
    jwthandler = JWTHandler(config, logger)

    return UserService(databaseops, authservice, keygen, jwthandler)   


def get_jwt_handler():
    logger = SingletonLogger()
    config = Config()
    return JWTHandler(config, logger)

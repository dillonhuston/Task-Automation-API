from app.Database.DatabaseOperations import DatabaseOperations
from app.auth.auth import AuthService
from app.Encryption.keyGenerator import KeyHandler
from app.Encryption.encryptionService import EncryptionService
from app.auth.jwt import JWTHandler
from app.utils.logger import SingletonLogger
from app.FileManager.fileOperations import fileOperations
from app.config import Config


def get_database_operations():
    return DatabaseOperations()

def get_userservice():
    from app.services.user_service import UserService


    config = Config()

    logger = SingletonLogger()
    databaseops = DatabaseOperations()
    authservice = AuthService(config)
    keygen  = KeyHandler(DatabaseOperations)
    jwthandler = JWTHandler(config, logger)

    return UserService(databaseops, authservice, keygen, jwthandler)   


def get_jwt_handler():
    logger = SingletonLogger()
    config = Config()
    return JWTHandler(config, logger)


def get_file_service():
    return fileOperations(DatabaseOperations, KeyHandler)


def get_encryption_service():
    # only instantiate what you need here
    keygen = KeyHandler()
    fileservice = fileOperations()
    return EncryptionService(keyhandler=keygen, fileoperations=fileservice)  
from app.Database.DatabaseOperations import DatabaseOperations
from app.auth.auth import AuthService
from app.Encryption.keyGenerator import KeyHandler
from app.Encryption.encryptionService import EncryptionService
from app.auth.jwt import JWTHandler
from app.utils.logger import SingletonLogger
from app.FileManager.fileOperations import fileOperations
from app.config import Config
from app.FileManager.fileManager import fileManager
from app.TaskService.taskService import TaskService


def get_database_operations():
    return DatabaseOperations()


def get_userservice():
    from app.services.user_service import UserService
    
    config = Config()
    logger = SingletonLogger()
    databaseops = DatabaseOperations()
    authservice = AuthService(config)
    keygen = KeyHandler(databaseops)  # Fixed: pass instance, not class
    jwthandler = JWTHandler(config, logger)

    return UserService(databaseops, authservice, keygen, jwthandler)


def get_jwt_handler():
    logger = SingletonLogger()
    config = Config()
    return JWTHandler(config, logger)


def get_file_service():
    # Fixed: create instances, don't pass classes
    db_ops = DatabaseOperations()
    keyhandler = KeyHandler(db_ops)
    config = Config()
    return fileOperations(dboperations=db_ops, keyhandler=keyhandler, config=config)


def get_encryption_service():
    db_ops = DatabaseOperations()
    keygen = KeyHandler(db_ops)
    file_ops = fileOperations(db_ops, keygen, Config())
    return EncryptionService(keyhandler=keygen, fileoperations=file_ops)


def get_file_manager():
    # Fixed: return instance, not class
    db_ops = DatabaseOperations()
    keyhandler = KeyHandler(db_ops)
    config = Config()
    return fileManager(db_ops, keyhandler, config)


def get_task_service():
    # Fixed: pass instance, not class
    return TaskService(fileservice=get_file_manager(), databaseops=get_database_operations())
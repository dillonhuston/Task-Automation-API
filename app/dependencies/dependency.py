from app.services.user_service import UserService
from app.Database.DatabaseOperations import DatabaseOperations
from app.auth.auth import AuthService
from app.Encryption_Services.keyGenerator import KeyHandler



def get_userservice():
    databaseops = DatabaseOperations()
    authservice = AuthService()
    keygen  = KeyHandler()
    return UserService(databaseops, authservice, keygen)   
from app.Database.DatabaseOperations import DatabaseOperations
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import UserCreate
from app.models.user import UserModel


from app.auth.auth import AuthService
from app.Encryption_Services.keyGenerator import KeyHandler

class UserService():


    def __init__(self, DbOperations: DatabaseOperations, authservice: AuthService, keygenerator: KeyHandler) -> None:
        self.dboperations = DbOperations
        self.authservice = authservice
        self.encryptionkeygen = keygenerator


    async def register_user(self, db: AsyncSession, user: UserCreate):

        if await self.dboperations.GetUserByUsername(db,user.username):
            raise ValueError("User already exists") #TODO add custom exception handle 
        
        hashed_password = self.authservice.hash_password(user.password)

        new_user = UserModel(
            username = user.username,
            email = user.email,
            password = hashed_password)
        
        return await self.dboperations.AddUser(db, new_user)
            






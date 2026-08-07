from app.Database.DatabaseOperations import DatabaseOperations
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import UserCreate, UserLogin
from app.models.user import UserModel

from app.dependencies.dependency import JWTHandler
from app.auth.auth import AuthService
from app.Encryption.keyGenerator import KeyHandler


class UserService():


    def __init__(self, DbOperations: DatabaseOperations, authservice: AuthService, keygenerator: KeyHandler, jwthandler: JWTHandler) -> None:
        self.dboperations = DbOperations
        self.authservice = authservice
        self.encryptionkeygen = keygenerator
        self.jwthandler = jwthandler
    
        


    async def register_user(self, db: AsyncSession, user: UserCreate):

        if await self.dboperations.GetUserByUsername(db, str(user.username)):
            raise ValueError("User already exists") #TODO add custom exception handle 
        
        hashed_password = self.authservice.hash_password(user.password)

        new_user = UserModel(
            username = user.username,
            is_admin = user.admin,
            email = user.email,
            hashed_password = hashed_password)
        
        return await self.dboperations.AddUser(db, new_user)
    

    async def login_user(self, db: AsyncSession, user_data: UserLogin):
        user = await self.dboperations.GetUserByUsername(db, user_data.username)
        if not user or not self.authservice.verify_password(user_data.password, str(user.hashed_password)):
            raise ValueError("Password or user does not exist.") # TODO remove this and replace with custom exception handler. Lets just focus on getting auth working

        payload = {
            "sub": user.username,
            "id": str(user.id)
        }

        token = await self.jwthandler.jwt_generate(payload)

        return{
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "access_token": token,
            "token_type": "bearer"
        }






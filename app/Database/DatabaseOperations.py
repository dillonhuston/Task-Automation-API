from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import UserModel

class DatabaseOperations():

    async def GetUserByUsername(self, db: AsyncSession, username: str):
        result = await db.execute(select(UserModel).where(UserModel.username == username))
        user =  result.scalar_one_or_none() #Chnage to scalr not user
        return user


    async def AddUser(self, db: AsyncSession, user: UserModel):
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user


        
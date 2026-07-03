from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import UserModel

class DatabaseOperations():

    async def GetUserByUsername(self, db: AsyncSession, username: str):
        user = await db.execute(select(UserModel).where(UserModel.username == username))
        return user 


    async def AddUser(self, db: AsyncSession, user: UserModel):
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user


        
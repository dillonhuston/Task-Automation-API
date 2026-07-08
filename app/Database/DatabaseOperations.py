import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import UserModel
from app.models.file import FileModel
from app.schemas.file import FileSave
class DatabaseOperations():

    async def GetUserByUsername(self, db: AsyncSession, username: str)-> UserModel:
        result = await db.execute(select(UserModel).where(UserModel.username == username))
        user =  result.scalar_one_or_none() 
        return user

    async def GetFileByID(self, db: AsyncSession, file_id: str):
        result = await db.execute(select(FileModel).where(FileModel.id == file_id))
        file = result.scalar_one_or_none()
        return file

    async def AddUser(self, db: AsyncSession, user: UserModel):
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def AddFile(self, db: AsyncSession, file_data: FileSave):
        new_file = FileModel(
            id=str(uuid.uuid4()),
            filename=file_data.original_filename,  
            user_id=file_data.user_id,
            file_path=file_data.file_path,
            file_hash=file_data.file_hash,
            nonce=file_data.nonce.hex()
        )
        
        db.add(new_file)
        await db.commit()
        await db.refresh(new_file)
        return new_file
        
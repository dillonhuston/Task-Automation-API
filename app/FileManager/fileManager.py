from fastapi import Depends, UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import get_db
from app.FileManager.fileOperations import fileOperations
from app.Encryption_Services.encryptionService import EncryptionService
from app.Database.DatabaseOperations import DatabaseOperations
from app.FileHash.API.HashFile import HashHandler
from app.utils.logger import SingletonLogger

from app.schemas.file import FileSave
import os


"""gotta make this a celery process or seperate thread"""
class fileManager:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db
        self.dboperation = DatabaseOperations()
        self.encryption = EncryptionService()
        self.fileoperations = fileOperations()
        self.logger = SingletonLogger().get_logger()

    async def uploadFile(self, user_id: str, file: UploadFile):  
        try:
            self.fileoperations.validate_file(file)
            # File operations now manages open/close inside save_file
            filename, file_path = self.fileoperations.save_file(file, user_id)
            
            file_hash = HashHandler(file_path).hash_file()
            nonce = self.encryption.encrypt(file_path=file_path, user_id=user_id, db=self.db)

            file_data = FileSave(
                original_filename=file.filename or "unnamed_file",
                user_id=user_id,
                file_path=file_path,
                file_hash=file_hash,
                nonce=nonce
            )

            # DatabaseOperations now handles the creation of the FileModel
            saved_file = await self.dboperation.AddFile(self.db, file_data)

            return {
                "id": saved_file.id,
                "filename": saved_file.filename,
                "file_path": saved_file.file_path,
                "file_hash": saved_file.file_hash,
                "nonce": saved_file.nonce
            }

        except Exception as e:
            self.logger.exception("Upload failed: %s", e)
            raise HTTPException(status_code=500, detail="Upload processing failed")
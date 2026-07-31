import os
from datetime import datetime, timezone

from fastapi import Depends, UploadFile, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Config
from app.Database.DatabaseOperations import DatabaseOperations
from app.Encryption.encryptionService import EncryptionService
from app.Encryption.keyGenerator import KeyHandler
from app.FileManager.fileOperations import fileOperations
from app.FileHash.API.HashFile import HashHandler
from app.schemas.file import FileSave
from app.models.database import get_db
from app.utils.logger import SingletonLogger

logger = SingletonLogger().get_logger()


class fileManager:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db
        self.dboperation = DatabaseOperations()
        self.keyhandler = KeyHandler(DatabaseOperations())
        self.fileoperations = fileOperations(DatabaseOperations(), self.keyhandler)
        self.encryption = EncryptionService(KeyHandler, self.fileoperations)
        self.logger = SingletonLogger().get_logger()
        self.config = Config()

    async def uploadFile(self, user_id: str, file: UploadFile):
        try:
            await self.fileoperations.validate_file(file)

            os.makedirs(self.config.BASE_DIR, exist_ok=True)
            filename = f"{user_id}_{datetime.now(tz=timezone.utc):%Y-%m-%d_%H-%M-%S}_{file.filename}"
            file_path = os.path.join(self.config.BASE_DIR, filename)

            file.file.seek(0)
            plaintext = await file.read()

            with open(file_path, "wb") as f:
                f.write(plaintext)

            file_hash = HashHandler(file_path).hash_file()

            nonce, ciphertext = await self.encryption.encrypt(
                user_id=user_id,
                plaintext=plaintext,
                db=self.db,
            )

            await self.fileoperations.overwrite_file(file_path, nonce + ciphertext)

            file_data = FileSave(
                original_filename=filename or "unnamed_file",
                user_id=user_id,
                file_path=file_path,
                file_hash=file_hash,
                nonce=nonce,
            )

            saved_file = await self.dboperation.AddFile(self.db, file_data)

            return {
                "id": saved_file.id,
                "filename": saved_file.filename,
                "file_path": saved_file.file_path,
                "file_hash": saved_file.file_hash,
                "nonce": saved_file.nonce,
            }

        except Exception as e:
            logger.exception("Upload failed: %s", e)
            raise HTTPException(status_code=500, detail="Upload processing failed") from e

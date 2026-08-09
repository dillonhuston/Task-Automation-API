import os
from datetime import datetime, timezone
from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.settings import settings
from app.Database.DatabaseOperations import DatabaseOperations
from app.Encryption.encryptionService import EncryptionService
from app.Encryption.keyGenerator import KeyHandler
from app.FileManager.fileOperations import fileOperations
from app.FileHash.API.HashFile import HashHandler
from app.schemas.file import FileSave
from app.utils.logger import SingletonLogger
from exceptions.exceptions import FileError

logger = SingletonLogger().get_logger()


class fileManager:
    def __init__(self, db_ops: DatabaseOperations = None, keyhandler: KeyHandler = None):
        self.db_ops = db_ops or DatabaseOperations()
        self.keyhandler = keyhandler or KeyHandler(self.db_ops)
        self.fileoperations = fileOperations(
            dboperations=self.db_ops,
            keyhandler=self.keyhandler,
        )
        self.encryption = EncryptionService(self.keyhandler, self.fileoperations)

    async def uploadFile(self, user_id: str, file: UploadFile, db: AsyncSession):
        try:
            await self.fileoperations.validate_file(file)

            upload_dir = os.path.join(settings.BASE_DIR, "tmp/uploads")
            os.makedirs(upload_dir, exist_ok=True)

            filename = f"{user_id}_{datetime.now(tz=timezone.utc):%Y-%m-%d_%H-%M-%S}_{file.filename}"
            file_path = os.path.join(upload_dir, filename)

            await file.seek(0)
            plaintext = await file.read()

            with open(file_path, "wb") as f:
                f.write(plaintext)

            file_hash = HashHandler(file_path).hash_file()

            nonce, ciphertext = await self.encryption.encrypt(
                user_id=user_id,
                plaintext=plaintext,
                db=db,
            )

            await self.fileoperations.overwrite_file(file_path, nonce + ciphertext)

            file_data = FileSave(
                original_filename=filename or "unnamed_file",
                user_id=user_id,
                file_path=file_path,
                file_hash=file_hash,
                nonce=nonce,
            )

            saved_file = await self.db_ops.AddFile(db, file_data)

            return {
                "id": saved_file.id,
                "filename": saved_file.filename,
                "file_path": saved_file.file_path,
                "file_hash": saved_file.file_hash,
                "nonce": saved_file.nonce,
            }
        except FileError:
            raise
        except Exception as e:
            logger.exception("Upload failed: %s", e)
            raise HTTPException(
                status_code=500,
                detail="Upload processing failed"
            )
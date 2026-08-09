import os
import mimetypes
from datetime import datetime
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.settings import settings
from app.dependencies.constants import MAX_UPLOAD_SIZE_MB
from app.schemas.file import Downloadfile
from app.Database.DatabaseOperations import DatabaseOperations
from app.Encryption.encryptionService import EncryptionService
from app.Encryption.keyGenerator import KeyHandler
from app.utils.logger import SingletonLogger
from app.exceptions.exceptions import FileError, AuthenticationError, FileProcessingError

logger = SingletonLogger().get_logger()


class fileOperations:
    def __init__(self, dboperations: DatabaseOperations, keyhandler: KeyHandler):
        self.dboperation = dboperations
        self.keyhandler = keyhandler
        self.encryptionservice = EncryptionService(self.keyhandler, self)

    async def save_file(self, file: UploadFile, user_id: str) -> tuple[str, str]:
        try:
            filename = f"{user_id}_{datetime.now():%Y-%m-%d_%H-%M-%S}_{file.filename}"
            upload_dir = os.path.join(settings.BASE_DIR, "tmp/uploads")
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, filename)

            contents = await file.read()
            with open(file_path, "wb") as f:
                f.write(contents)

            await file.seek(0)
            logger.info("File saved: %s at %s", filename, file_path)
            return filename, file_path
        except FileError:
            raise
        except Exception as exc:
            logger.exception("Error saving file: %s", exc)
            raise FileProcessingError(detail="Failed to save file to the path provided")

    async def validate_file(self, file: UploadFile) -> None:
        try:
            data = await file.read()
            size_bytes = len(data)
            await file.seek(0)

            size_mb = size_bytes / (1024 * 1024)
            if size_mb > MAX_UPLOAD_SIZE_MB:
                logger.warning("Upload rejected: file too large (%.2f MB)", size_mb)
                raise FileError(
                    detail=f"File exceeds max allowed size of {MAX_UPLOAD_SIZE_MB} MB",
                )
        except FileError:
            raise
        except Exception as exc:
            logger.exception("Error validating file size: %s", exc)
            raise FileProcessingError("Can not validate file size.")

    async def list_files(self, db: AsyncSession, user_id: str):
        files = await self.dboperation.ReturnUserFiles(db, user_id)
        if not files:
            return []
        return [
            {
                "id": f.id,
                "filename": f.filename,
                "filepath": f.file_path,
                "file_hash": f.file_hash,
            }
            for f in files
        ]

    async def download_file(self, db: AsyncSession, file_id: str, user_id: str):
        try:
            file = await self.dboperation.GetFileByID(db, file_id)
        except FileError:
            raise
        except Exception as e:
            logger.warning("No file available for user %s: %s", user_id, e)
            raise FileError(detail="No file found for the current user")

        encrypted_data = await self.read_file(file.file_path)
        nonce = encrypted_data[:12]
        ciphertext = encrypted_data[12:]

        decrypted_data = await self.encryptionservice.decrypt(
            user_id=user_id,
            ciphertext=ciphertext,
            nonce=nonce,
            db=db,
        )

        original_filename = file.filename or "downloaded_file"
        media_type, _ = mimetypes.guess_type(original_filename)
        if media_type is None:
            media_type = "application/octet-stream"

        return Downloadfile(
            original_filename=original_filename,
            data=decrypted_data,
            media_type=media_type,
        )

    async def read_file(self, file_path: str) -> bytes:
        try:
            with open(file_path, "rb") as f:
                return f.read()
        except FileProcessingError:
            raise
        except Exception as e:
            raise FileError(
                "Failed to read file. File could have no contents or does not exist."
            )

    async def overwrite_file(self, file_path: str, encrypted_bytes: bytes) -> int:
        try:
            with open(file_path, "wb") as f:
                return f.write(encrypted_bytes)
        except FileProcessingError:
            raise
        except Exception as e:
            raise FileProcessingError(f"Failed to write data to path")
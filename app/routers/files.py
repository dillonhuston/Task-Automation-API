"""
File management endpoints for Task Automation API.
Includes upload, list, and delete functionality.
"""


from io import BytesIO
from typing import List, Dict, Any

from fastapi.responses import StreamingResponse
from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.auth_utils import get_current_user
from app.dependencies.dependency import get_file_service, get_database_operations
from app.models.database import get_db
from app.models.user import UserModel
from app.models.file import FileModel

from app.FileManager.fileOperations import fileOperations
from app.Encryption_Services.encryptionService import EncryptionService
from app.Database.DatabaseOperations import DatabaseOperations
from app.utils.logger import SingletonLogger
from app.dependencies.constants import (
    HTTP_STATUS_BAD_REQUEST,
)

router = APIRouter(prefix="/files", tags=["Files"])
logger = SingletonLogger().get_logger()


@router.get("/list")
async def list_files(
    fileservice: fileOperations = Depends(get_file_service),
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    files = await fileservice.list_files(db, user.id)
    if not files:
        raise HTTPException(
            status_code=404,
            detail="Can not find any files mathchin the current user."
        )
    return files



@router.get("/download/{file_id}")
async def download_file(
    file_id: str,
    dboperations: DatabaseOperations = Depends(get_database_operations),
    fileservice: fileOperations = Depends(get_file_service),
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(get_current_user)):

    file = dboperations.GetFileByID(db, file_id)
    if not file:
        raise HTTPException(404, "File not found")

    try:
        decrypted = fileservice.download_file(db, file_id, user_id=str(user.id))   

        return StreamingResponse(
            BytesIO(decrypted.data),
            media_type=decrypted.media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{decrypted.original_filename}"'
            }
        )
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Download failed for file %s (user %s): %s", file_id, user.id, e)
        raise HTTPException(status_code=500, detail="Failed to decrypt file")
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth_utils import get_current_user
from app.dependencies.dependency import get_file_service, get_database_operations
from app.models.database import get_db
from app.models.user import UserModel

from app.FileManager.fileOperations import fileOperations
from app.Database.DatabaseOperations import DatabaseOperations

router = APIRouter(prefix="/files", tags=["Files"])


@router.get("/list")
async def list_files(
    fileservice: fileOperations = Depends(get_file_service),
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    files = await fileservice.list_files(db, str(user.id))
    if not files:
        raise HTTPException(status_code=404, detail="Can not find any files matching the current user.")
    return files


@router.get("/download/{file_id}")
async def download_file(
    file_id: str,
    dboperations: DatabaseOperations = Depends(get_database_operations),
    fileservice: fileOperations = Depends(get_file_service),
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(get_current_user)):
    file = await dboperations.GetFileByID(db, file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    decrypted = await fileservice.download_file(db=db, file_id=file_id, user_id=str(user.id))

    return StreamingResponse(
        BytesIO(decrypted.data),
        media_type=decrypted.media_type,
        headers={"Content-Disposition": f'attachment; filename="{decrypted.original_filename}"'},
    )

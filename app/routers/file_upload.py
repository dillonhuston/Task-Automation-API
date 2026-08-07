from fastapi import APIRouter, Depends, File,UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.file import FileResponse
from app.FileManager.fileManager import fileManager
from app.models.database import get_db
from app.models.user import UserModel
from app.dependencies.auth_utils import get_current_user
from app.dependencies.dependency import get_file_manager

router = APIRouter(prefix="/files", tags=["Files"])


@router.post("/upload", response_model=FileResponse)
async def uploadfile(
    file: UploadFile = File(),
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    manager: fileManager = Depends(get_file_manager)):
    
    return await manager.uploadFile(user.id, file, db)
from fastapi import APIRouter, Depends, File,UploadFile
from app.schemas.file import FileResponse
from app.FileManager.fileManager import fileManager
from app.models.user import UserModel
from app.dependencies.auth_utils import get_current_user

router = APIRouter(prefix="/files", tags=["Files"])


@router.post("/upload", response_model=FileResponse)
async def uploadfile(
    file: UploadFile = File(),
    user: UserModel = Depends(get_current_user),
    manager: fileManager = Depends()):
    
    return await manager.uploadFile(user.id, file)
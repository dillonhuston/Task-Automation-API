from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional


class FileSave(BaseModel):

    original_filename:str
    user_id:str
    file_path: str
    file_hash: str
    nonce: bytes


"""Schema for returning files"""
class FileResponse(BaseModel):
    id: str
    filename: str
    file_path: str
    file_hash: str

class FileUploadRequest(BaseModel):
    filename: str
    file_hash: Optional[str] = None

class Downloadfile(BaseModel):
    data: bytes
    media_type: str
    original_filename:str

    




__all__ = ["FileResponse", "FileUploadRequest"]

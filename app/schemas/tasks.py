"""
Schemas for task-related data models and validation.
"""

from datetime import datetime, timezone
from typing import Optional
from app.models.user import UserModel
from enum import Enum
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from fastapi import File, UploadFile


def aware_utcnow() -> datetime:
    """Return current UTC time with timezone awareness."""
    return datetime.now(timezone.utc)

class TaskType(str, Enum):
    """Enum for task types with UPPER_CASE naming style."""
    REMINDER = "reminder"
    FILE_CLEANUP = "file_cleanup"
 
# removed file param
class AddTask(BaseModel):
    """Schema for adding a task with optional file upload."""
    title: str
    description: Optional[str] = None 
    receiver_email: str
    task_type: TaskType
    schedule_time: datetime
    webhook_url: Optional[str] = None
  


class TaskStatus(str, Enum):
    """Enum for task statuses with UPPER_CASE naming style."""
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    RUNNING = "running"
    CANCELED = "canceled"
    FAILED = "failed"





class FileTypes(str, Enum):

    """gonna have to get a libary to mkae this more easier.
       rather than typing out the every file type
    """
    PNG = ".png"
    JPED = ".jpeg"
    MP3 = ".mp3"
    MP4 = ".mp4"
    TXT = ".txt"




class TaskCreate(BaseModel):
    """Schema for creating a task."""
    task_type: TaskType
    schedule_time: datetime
    title: str
    receiver_email: str
    webhook_url: Optional[str] = None




    @field_validator("schedule_time")
    @classmethod
    def validate_future_time(cls, v: datetime) -> datetime:
        """Ensure schedule_time is in the future."""
        now = datetime.utcnow()
        if v.tzinfo is not None:
            v = v.replace(tzinfo=None)
        if v <= now:
            raise ValueError("schedule_time must be in the future")
        return v


class TaskResponse(BaseModel):
    """Schema for returning task data"""
    id: str
    user_id: str
    task_type: str
    schedule_time: datetime
    status: str
    title: Optional[str] = None  
    receiver_email: Optional[str] = None 

    model_config = {
        "from_attributes": True
    }

    

class Task(BaseModel):
    id: str
    user_id: str
    task_type: str
    schedule_time: datetime
    status: str
    title: Optional[str] = None  
    receiver_email: Optional[str] = None
    file_id: Optional[str] = None  
        

class TaskHistoryS(BaseModel):
    task_type: str
    status: str
    details: str
    user_id: str

    model_config = {
        "from_attributes": True
    }


# In app/schemas/tasks.py
class ScheduleTask(BaseModel):
    user_id: str
    task_type: TaskType
    task_data: TaskCreate
    receiver_email: Optional[str] = None  
    webhook_url: Optional[str] = None    
 


__all__ = [
    "TaskStatus", 
    "TaskType", 
    "TaskCreate", 
    "TaskResponse", 
    "TaskHistoryS", 
    "ScheduleTask",
    "AddTask",
    "Task"
]
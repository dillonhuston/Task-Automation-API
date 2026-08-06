"""
Task scheduling service for managing task creation and scheduling.
"""

from uuid import uuid4
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.tasks import Task as TaskSchema, TaskStatus, TaskResponse, ScheduleTask
from app.Database.DatabaseOperations import DatabaseOperations
from app.FileManager.fileManager import fileManager
from app.utils.celery_instance import celery_app
from app.utils.logger import SingletonLogger
from app.utils.discord import send_discord_notification
from app.dependencies.constants import (
    TASK_STATUS_SCHEDULED,
    TASK_TYPE_REMINDER,
    TASK_TYPE_FILE_CLEANUP,
)


class TaskService:
    """
    Service for scheduling tasks and managing task lifecycle.
    """
    
    def __init__(
        self, 
        fileservice: Optional[fileManager] = None,
        databaseops: Optional[DatabaseOperations] = None
    ):
        """
        Initialize task service.
        
        Args:
            fileservice: File manager service
            databaseops: Database operations service
        """
        self.fileservice = fileservice
        self.databaseops = databaseops or DatabaseOperations()
        self.logger = SingletonLogger().get_logger()

    async def schedule_task(self, db: AsyncSession, task_data: ScheduleTask) -> TaskResponse:
        """
        Schedule a new task in the database and send via Celery.

        Args:
            db: Async SQLAlchemy session
            task_data: ScheduleTask data with task details

        Returns:
            TaskResponse: Pydantic validated task
        """
        uploaded_file = None
        file_id = None
        
        # Handle file upload if present
        if task_data.file is not None and task_data.file.filename:
            try:
                file_mgr = fileManager(db=db)
                uploaded_file = await file_mgr.uploadFile(
                    user_id=task_data.user_id, 
                    file=task_data.file
                )
                file_id = uploaded_file.get('id') if uploaded_file else None
                self.logger.debug(f"Uploaded file for task: {file_id}")
            except Exception as e:
                self.logger.error(f"Failed to upload file for task: {e}")
                file_id = None

        # Create new task
        new_task = TaskSchema(
            id=str(uuid4()),
            user_id=task_data.user_id,
            task_type=task_data.task_type.value,
            schedule_time=task_data.task_data.schedule_time,
            status=TaskStatus.SCHEDULED.value,
            receiver_email=task_data.task_data.receiver_email,
            title=task_data.task_data.title,
            file_id=file_id
        )

        # Save to database
        saved_task = await self.databaseops.AddTask(db, new_task)

        # Log the task creation
        self.logger.info(
            "New task scheduled: %s (ID: %s) for user %s at %s, receiver: %s",
            saved_task.task_type,
            saved_task.id,
            saved_task.user_id,
            saved_task.schedule_time,
            saved_task.receiver_email,
        )
        
        # Send Discord notification
        try:
            send_discord_notification(
                webhook_url=task_data.task_data.webhook_url,
                status=TASK_STATUS_SCHEDULED,
                task_name=task_data.task_data.title,
                message=f"Task: {task_data.task_data.title} has Scheduled for {saved_task.schedule_time}, and email has been sent to you"
            )
        except Exception as e:
            self.logger.error(f"Failed to send Discord notification: {e}")

        # Schedule Celery task
        if task_data.task_type.value == TASK_TYPE_REMINDER:
            celery_app.send_task(
                name="app.tasks.tasks.send_reminder",
                args=[str(saved_task.id), task_data.task_data.receiver_email, file_id],
                eta=saved_task.schedule_time,
            )
            self.logger.debug(f"Scheduled reminder task {saved_task.id}")
        elif task_data.task_type.value == TASK_TYPE_FILE_CLEANUP:
            celery_app.send_task(
                name="app.tasks.tasks.file_cleanup",
                args=[str(saved_task.id), task_data.task_data.receiver_email],
                eta=saved_task.schedule_time
            )
            self.logger.debug(f"Scheduled file cleanup task {saved_task.id}")
        
        return TaskResponse.model_validate(saved_task)
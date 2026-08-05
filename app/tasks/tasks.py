"""
Celery tasks for handling scheduled jobs such as file cleanup and sending reminders.
Refactored with proper OOP using DatabaseOperations.
"""

import os
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv

from celery import shared_task
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tasks import Task, TaskHistory
from app.models.file import FileModel
from app.utils.celery_instance import celery_app
from app.utils.email import send_completion_email
from app.utils.logger import SingletonLogger
from app.utils.discord import send_discord_notification
from app.dependencies.constants import (
    TASK_STATUS_RUNNING,
    TASK_STATUS_COMPLETED,
    TASK_STATUS_FAILED,
    FILE_STORAGE_DIR,
)
from app.Database.DatabaseOperations import DatabaseOperations
from app.models.database import get_db

load_dotenv()
logger = SingletonLogger().get_logger()
db_ops = DatabaseOperations()


async def log_task_history(
    db: AsyncSession,
    task_type: str,
    status: str,
    details: str,
    user_id: str,
    executed_at: str) -> None:
    """
    Log task history to database.
    
    Args:
        db: Database session
        task_type: Type of task
        status: Task status
        details: Task details
        user_id: User ID
        executed_at: Execution timestamp
    """
    await db_ops.add_task_history(
        db=db,
        task_type=task_type,
        status=status,
        details=details,
        user_id=user_id,
        executed_at=executed_at
    )


@celery_app.task(name="app.tasks.tasks.file_cleanup")
async def file_cleanup(task_id: str, receiver_email: Optional[str] = None) -> None:
    """
    Delete files older than 1 day and update task status.
    
    Args:
        task_id: ID of the cleanup task
        receiver_email: Optional email to send completion notification
    """
    logger.info(f"Starting file cleanup task {task_id}")
    task = None
    
    try:
        async for db in get_db():
            task = await db_ops.get_task_by_id(db, task_id)
            
            if not task:
                logger.warning(f"No task found with ID {task_id}")
                return
            
            # Mark task as running
            await db_ops.update_task_status(db, task_id, TASK_STATUS_RUNNING)
            
            # Delete old files
            threshold = datetime.now() - timedelta(days=1)
            deleted_count = 0
            
            if os.path.exists(FILE_STORAGE_DIR):
                for filename in os.listdir(FILE_STORAGE_DIR):
                    filepath = os.path.join(FILE_STORAGE_DIR, filename)
                    if os.path.isfile(filepath):
                        mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                        if mtime < threshold:
                            os.remove(filepath)
                            deleted_count += 1
                            logger.debug(f"Deleted old file: {filename}")
            
            logger.info(f"Deleted {deleted_count} old files.")
            
            # Mark task as completed
            await db_ops.update_task_status(db, task_id, TASK_STATUS_COMPLETED)
            
            details_msg = f"Deleted {deleted_count} files"
            
            # Send notifications if email present
            if receiver_email:
                send_completion_email(task_id, receiver_email)
                send_discord_notification()
                logger.info(f"Sent task completion email to {receiver_email}")
                details_msg += f", email sent to {receiver_email}"
            else:
                logger.warning(f"Task {task_id} has no receiver_email. No email sent.")
                details_msg += ", no email sent"
            
            # Log task history
            await log_task_history(
                db=db,
                task_type="file_cleanup",
                status="COMPLETED",
                details=details_msg,
                user_id=task.user_id,
                executed_at=datetime.now().isoformat()
            )
            
    except Exception as e:
        logger.exception(f"File cleanup failed for task_id={task_id}: {e}")
        
        if task:
            try:
                async for db in get_db():
                    await db_ops.update_task_status(db, task_id, TASK_STATUS_FAILED)
                    await log_task_history(
                        db=db,
                        task_type="file_cleanup",
                        status="FAILED",
                        details=str(e),
                        user_id=task.user_id,
                        executed_at=datetime.now().isoformat()
                    )
            except Exception as db_error:
                logger.error(f"Failed to update task status after failure: {db_error}")


@celery_app.task(name="app.tasks.tasks.send_reminder")
async def send_reminder(
    task_id: str,
    receiver_email: str,
    file_id: Optional[str] = None) -> None:
    """
    Send reminder email for a scheduled task.
    
    Args:
        task_id: ID of the reminder task
        receiver_email: Email to send reminder to
        file_id: Optional file ID to include in reminder
    """
    logger.info(f"Starting reminder task {task_id} for {receiver_email}")
    task = None
    
    try:
        async for db in get_db():
            # Get the task
            task = await db_ops.get_task_by_id(db, task_id)
            
            if not task:
                logger.warning(f"No task found with ID {task_id}")
                return
            
            # Get file if provided
            file = None
            if file_id:
                file = await db_ops.get_file_by_id(db, file_id)
                if not file:
                    logger.warning(f"No file found with ID {file_id}")
            
            # Update task status to running
            await db_ops.update_task_status(db, task_id, TASK_STATUS_RUNNING)
            
            # Log reminder schedule
            reminder_time = task.schedule_time
            if reminder_time:
                logger.info(
                    f"[Reminder] Task scheduled for {reminder_time} | Type: {task.task_type}"
                )
            else:
                logger.warning("Task has no schedule_time set.")
            
            # Send reminder email
            send_completion_email(task_id, receiver_email, file_id)
            logger.info(f"Sent reminder email to {receiver_email}")
            
            # Log task history
            await log_task_history(
                db=db,
                task_type="send_reminder",
                status="COMPLETED",
                details=f"Reminder email sent to {receiver_email}",
                user_id=task.user_id,
                executed_at=reminder_time.isoformat() if reminder_time else datetime.now().isoformat()
            )
            
    except Exception as e:
        logger.exception(f"Reminder task failed for ID {task_id}: {e}")
        
        if task:
            try:
                async for db in get_db():
                    await db_ops.update_task_status(db, task_id, TASK_STATUS_FAILED)
                    await log_task_history(
                        db=db,
                        task_type="send_reminder",
                        status="FAILED",
                        details=str(e),
                        user_id=task.user_id,
                        executed_at=datetime.now().isoformat()
                    )
            except Exception as db_error:
                logger.error(f"Failed to update task status after reminder failure: {db_error}")


__all__ = ["shared_task", "send_reminder", "file_cleanup"]
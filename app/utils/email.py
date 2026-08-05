"""
Module for handling email notifications with Celery tasks.
Includes reminder and completion email functionality.
"""

import os
import ssl
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.celery_instance import celery_app
from app.models.database import AsyncSessionLocal
from app.utils.logger import SingletonLogger
from app.Encryption.encryptionService import EncryptionService
from app.models.tasks import Task
from app.models.file import FileModel
from app.dependencies.constants import (
    TASK_STATUS_SCHEDULED,
    TASK_STATUS_COMPLETED,
    TASK_STATUS_FAILED,
)

logger = SingletonLogger().get_logger()

#TODO Implement config 
load_dotenv()
EMAIL_ADDRESS = os.getenv("EMAIL")
EMAIL_PASSWORD = os.getenv("PASSWORD")
SMTP_PORT = 465
SMTP_SERVER = "smtp.gmail.com"

if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
    logger.critical("EMAIL or PASSWORD environment variable is missing")
    raise ValueError("Missing EMAIL or PASSWORD in .env file")


@celery_app.task(
    name="app.utils.email.send_email_task",
    bind=True,
    autoretry_for=(smtplib.SMTPException,),
    retry_backoff=True,
    max_retries=3,
)
def send_email_task(
    self,
    receiver_email: str,
    task_id: str,
    file_id: str | None,
    email_type: str):

    """Send email for a task, handling reminders and completions."""
    import asyncio
    
    async def _async_send():
        async with AsyncSessionLocal() as db:
            task = await db.get(Task, task_id)
            if not task:
                logger.error("Task %s not found", task_id)
                return "Task Not Found"

            if not receiver_email:
                logger.warning("Task %s has no receiver email", task_id)
                task.status = TASK_STATUS_FAILED
                await db.commit()
                return "No Email Provided"

            decrypted_bytes = None
            file = None
            
            if file_id is not None:
                file = await db.get(FileModel, file_id)
                if file and file.filename:
                    encryptionservice = EncryptionService()
                    nonce_bytes = bytes.fromhex(file.nonce)
                    decrypted_bytes = encryptionservice.decrypt(
                        file_path=file.file_path,
                        user_id=file.user_id,
                        db=db,
                        nonce=nonce_bytes,
                    )

            # Email content
            if email_type == TASK_STATUS_COMPLETED:
                subject = f"Task '{task.title}' Completed"
                body = f"Task ID: {task.id}\nTitle: {task.title}\nScheduled Time: {task.schedule_time}"
            elif email_type == TASK_STATUS_SCHEDULED:
                subject = f"Reminder: Task '{task.title}' Due"
                body = f"Task ID: {task.id}\nTitle: {task.title}\nScheduled Time: {task.schedule_time}"
            else:
                return "Invalid Email Type"

            # Send email
            msg = EmailMessage()
            msg["From"] = EMAIL_ADDRESS
            msg["To"] = receiver_email
            msg["Subject"] = subject
            msg.set_content(body)

            if decrypted_bytes and file:
                msg.add_attachment(
                    decrypted_bytes,
                    maintype="application",
                    subtype="octet-stream",
                    filename=file.filename,
                )

            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
                server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                server.send_message(msg)

            if email_type == TASK_STATUS_COMPLETED:
                task.status = TASK_STATUS_COMPLETED
                await db.commit()

            logger.info("Email sent to %s for task %s", receiver_email, task_id)
            return "Success"
    
    return asyncio.run(_async_send())


def schedule_reminder(task_id: str, receiver_email: str):
    """Schedule an email reminder."""
    send_email_task.delay(
        receiver_email=receiver_email,
        task_id=task_id,
        file_id=None,
        email_type=TASK_STATUS_SCHEDULED
    )


def send_completion_email(task_id: str, file_id: str, receiver_email: str):
    """Send a completion notification email."""
    send_email_task.delay(
        receiver_email=receiver_email,
        task_id=task_id,
        file_id=file_id,
        email_type=TASK_STATUS_COMPLETED
    )
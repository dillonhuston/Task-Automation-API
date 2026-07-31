"""
Module for handling email notifications with Celery tasks.
Includes reminder and completion email functionality.
"""

import os
import ssl
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv
from sqlalchemy.orm import Session

from app.utils.celery_instance import celery_app
from app.models.database import SessionLocal
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

# Load environment variables
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
    task_id: int,
    file_id: int | None,  # Made optional; reminders may not need a file
    email_type: str,
):
    """Send email for a task, handling reminders and completions."""
    db: Session = SessionLocal()
    task: Task | None = None
    file: FileModel | None = None
    decrypted_bytes = None
    encryptionservice = EncryptionService()

    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            logger.error("Task %d not found", task_id)
            return "Task Not Found"

        # Validate receiver email early
        if not receiver_email:
            logger.warning("Task %d has no receiver email", task_id)
            task.status = TASK_STATUS_FAILED
            db.merge(task)
            db.commit()
            return "No Email Provided"

        # Fetch and decrypt file only if file_id is provided (completion emails)
        if file_id is not None:
            file = db.query(FileModel).filter(FileModel.id == file_id).first()
            if file and file.filename:
                nonce_bytes = bytes.fromhex(file.nonce)
                decrypted_bytes = encryptionservice.decrypt(
                    file_path=file.file_path,
                    user_id=file.user_id,
                    db=db,
                    nonce=nonce_bytes,
                )
                if not isinstance(decrypted_bytes, (bytes, bytearray)):
                    raise ValueError("Decryption did not return bytes")

        # Determine email content based on type
        if email_type == TASK_STATUS_COMPLETED:
            subject = f"Task '{task.title}' Completed"
            body = (
                f"Dear recipient,\n\n"
                f"You have a task scheduled .\n\n"
                f"Task ID: {task.id}\n"
                f"Title: {task.title}\n"
                f"Scheduled Time: {task.schedule_time}\n\n"
                f"Please find the processed file attached (if applicable).\n\n"
                f"Best regards,\nThe Team"
            )
        elif email_type == TASK_STATUS_SCHEDULED:
            subject = f"Reminder: Task '{task.title}' Due"
            body = (
                f"Dear recipient,\n\n"
                f"This is a reminder for your upcoming task.\n\n"
                f"Task ID: {task.id}\n"
                f"Title: {task.title}\n"
                f"Scheduled Time: {task.schedule_time}\n\n"
                f"Please ensure everything is ready.\n\n"
                f"Best regards,\nThe Team"
            )
        else:
            logger.error("Invalid email_type: %s for task %d", email_type, task_id)
            return "Invalid Email Type"

        # Create email message
        msg = EmailMessage()
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = receiver_email
        msg["Subject"] = subject
        msg.set_content(body)

        # Attach decrypted file if available
        if decrypted_bytes and file:
            msg.add_attachment(
                decrypted_bytes,
                maintype="application",
                subtype="octet-stream",
                filename=file.filename,
            )

        # Send email
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)

        logger.info("Email sent successfully to %s for task %d (%s)", receiver_email, task_id, email_type)

        # Update task status only on successful send (for completion emails)
        if email_type == TASK_STATUS_COMPLETED:
            task.status = TASK_STATUS_COMPLETED
            db.merge(task)
            db.commit()

        return "Success"

    except smtplib.SMTPException as smtp_err:
        logger.error("SMTP error while sending email for task %d: %s", task_id, smtp_err)
        if task:
            task.status = TASK_STATUS_FAILED
            db.merge(task)
            db.commit()
        raise self.retry(exc=smtp_err)

    except Exception as exc:
        logger.exception("Unhandled error in send_email_task for task %d: %s", task_id, exc)
        if task:
            task.status = TASK_STATUS_FAILED
            db.merge(task)
            db.commit()
        raise

    finally:
        db.close()


# Helper functions to schedule emails
def schedule_reminder(task_id: int, receiver_email: str):
    """Schedule an email reminder for the specified task (no file attached)."""
    send_email_task.delay(
        receiver_email=receiver_email,
        task_id=task_id,
        file_id=None,  # not needed                  
        email_type=TASK_STATUS_SCHEDULED
    )


def send_completion_email(task_id: int, file_id: int, receiver_email: str):
    """Send a completion notification email with decrypted file attached."""
    send_email_task.delay(
        receiver_email=receiver_email,
        task_id=task_id,
        file_id=file_id,
        email_type=TASK_STATUS_COMPLETED
    )
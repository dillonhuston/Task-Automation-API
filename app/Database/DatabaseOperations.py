import uuid
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc
from app.models.user import UserModel
from app.models.tasks import Task as TaskModel
from app.models.file import FileModel
from app.schemas.file import FileSave
from app.schemas.tasks import Task
from app.utils.logger import SingletonLogger


class DatabaseOperations():
    """Database operations handler."""
    
    def __init__(self):
        self.logger = SingletonLogger().get_logger()

    """User operations"""
    
    async def GetUserByUsername(self, db: AsyncSession, username: str) -> UserModel:
        result = await db.execute(select(UserModel).where(UserModel.username == username))
        user = result.scalar_one_or_none()
        return user

    async def AddUser(self, db: AsyncSession, user: UserModel):
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def GetUserByID(self, db: AsyncSession, user_id: str):
        result = await db.execute(select(UserModel).where(UserModel.id == user_id))
        user = result.scalar_one_or_none()
        return user

    """File operations"""

    async def GetFileByID(self, db: AsyncSession, file_id: str):
        result = await db.execute(select(FileModel).where(FileModel.id == file_id))
        file = result.scalar_one_or_none()
        return file

    async def AddFile(self, db: AsyncSession, file_data: FileSave):
        new_file = FileModel(
            id=str(uuid.uuid4()),
            filename=file_data.original_filename,
            user_id=file_data.user_id,
            file_path=file_data.file_path,
            file_hash=file_data.file_hash,
            nonce=file_data.nonce.hex()
        )
        db.add(new_file)
        await db.commit()
        await db.refresh(new_file)
        return new_file

    async def ReturnUserFiles(self, db: AsyncSession, user_id: str):
        result = await db.execute(select(FileModel).where(FileModel.user_id == user_id))
        files = result.scalars().all()
        return files

    """Encryption related"""

    async def AddUserKey(self, db: AsyncSession, user_id: str, key_hex: str):
        cmd = update(UserModel).where(UserModel.id == user_id).values(encryption_key=key_hex)
        result = await db.execute(cmd)
        await db.commit()
        return result.rowcount

    """Task operations"""
    async def AddTask(self, db: AsyncSession, task: Task):
        new_task = TaskModel(
            id=task.id,
            user_id=task.user_id,
            task_type=task.task_type,
            schedule_time=task.schedule_time,  # Fixed: was task.task_type
            status=task.status,
            receiver_email=task.receiver_email,
            title=task.title,
            file_id=task.file_id
        )
        db.add(new_task)
        await db.commit()
        await db.refresh(new_task)
        return new_task

    async def ReturnTask(self, db: AsyncSession, task_id: str):
        result = await db.execute(select(TaskModel).where(TaskModel.id == task_id))
        task = result.scalar_one_or_none()
        return task

    async def ReturnUserTasks(self, db: AsyncSession, user_id: str) -> List[TaskModel]:
        """Return all tasks for a user."""
        result = await db.execute(select(TaskModel).where(TaskModel.user_id == user_id))
        tasks = result.scalars().all()
        return tasks

    async def ReturnUserTaskHistory(self, db: AsyncSession, user_id: str) -> List[TaskModel]:
        """Return all task history for a user."""
        from app.models.tasks import TaskHistory
        result = await db.execute(
            select(TaskHistory)
            .where(TaskHistory.user_id == user_id)
            .order_by(desc(TaskHistory.executed_at))
        )
        history = result.scalars().all()
        return history

    async def ReturnTaskHistoryByTask(self, db: AsyncSession, user_id: str, task_type: str) -> List[TaskModel]:
        """Return task history for a specific task type."""
        from app.models.tasks import TaskHistory
        result = await db.execute(
            select(TaskHistory)
            .where(TaskHistory.user_id == user_id)
            .where(TaskHistory.task_type == task_type)
            .order_by(desc(TaskHistory.executed_at))
        )
        history = result.scalars().all()
        return history

    async def DeleteTask(self, db: AsyncSession, task_id: str) -> bool:
        """Delete a task by ID."""
        task = await self.ReturnTask(db, task_id)
        if task:
            await db.delete(task)
            await db.commit()
            self.logger.info(f"Deleted task {task_id}")
            return True
        return False

    async def update_task_status(self, db: AsyncSession, task_id: str, status: str) -> Optional[TaskModel]:
        try:
            cmd = update(TaskModel).where(TaskModel.id == task_id).values(status=status)
            result = await db.execute(cmd)
            await db.commit()

            if result.rowcount > 0:
                self.logger.info(f"Updated task {task_id} status to: {status}")
                return await self.ReturnTask(db, task_id)
            else:
                self.logger.warning(f"Task {task_id} not found for status update")
                return None
        except Exception as e:
            self.logger.error(f"Error updating task status for {task_id}: {e}")
            await db.rollback()
            raise

    async def add_task_history(
        self,
        db: AsyncSession,
        task_type: str,
        status: str,
        details: str,
        user_id: str,
        executed_at: str) -> TaskModel:

        """Add task history."""
        try:
            from app.models.tasks import TaskHistory
            history = TaskHistory(
                task_type=task_type,
                status=status,
                details=details,
                user_id=user_id,
                executed_at=executed_at
            )
            db.add(history)
            await db.commit()
            self.logger.info(f"Added task history entry for user: {user_id}")
            return history
        except Exception as e:
            self.logger.error(f"Error adding task history: {e}")
            await db.rollback()
            raise
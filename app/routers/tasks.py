"""
Task management routes for Task Automation API.
"""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.tasks import AddTask, TaskCreate, TaskResponse, TaskHistoryS, ScheduleTask
from app.models.user import UserModel
from app.dependencies.auth_utils import get_current_user
from app.dependencies.dependency import get_task_service
from app.models.database import get_db
from app.TaskService.taskService import TaskService
from app.Database.DatabaseOperations import DatabaseOperations
from app.utils.logger import SingletonLogger
from app.dependencies.constants import HTTP_STATUS_BAD_REQUEST, HTTP_STATUS_NOT_FOUND

router = APIRouter(prefix="/tasks")
logger = SingletonLogger().get_logger()
db_ops = DatabaseOperations()


def validate_uuid(task_id: str) -> UUID:
    try:
        return UUID(task_id)
    except ValueError:
        raise HTTPException(400, "Invalid task ID format")


@router.post("/schedule", response_model=TaskResponse)
async def schedule_task_endpoint(
    task: AddTask,
    taskservice: TaskService = Depends(get_task_service),
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(get_current_user)) -> TaskResponse:

    try:
        task_data = ScheduleTask(
            user_id=str(user.id),
            task_type=task.task_type,
            task_data=TaskCreate(
                title=task.title,
                description=task.description,
                receiver_email=task.receiver_email,
                schedule_time=task.schedule_time,
                webhook_url=task.webhook_url,
                task_type=task.task_type
            )
        )
        new_task = await taskservice.schedule_task(db=db, task_data=task_data)
        logger.info(f"Task scheduled: {new_task.id} for user {user.id}")
        return new_task
    except Exception as e:
        logger.exception(f"Error scheduling task: {e}")
        raise HTTPException(HTTP_STATUS_BAD_REQUEST, "Failed to schedule task")


@router.get("/list_tasks", response_model=List[TaskResponse])
async def list_tasks_endpoint(
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(get_current_user)) -> List[TaskResponse]:

    try:
        tasks = await db_ops.ReturnUserTasks(db, str(user.id))
        return [TaskResponse.model_validate(task) for task in tasks]
    except Exception as e:
        logger.error(f"Error retrieving tasks: {e}")
        raise HTTPException(HTTP_STATUS_BAD_REQUEST, "Error retrieving tasks")


@router.get("/task_history", response_model=List[TaskHistoryS])
async def get_task_history_endpoint(
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(get_current_user)) -> List[TaskHistoryS]:

    try:
        history = await db_ops.ReturnUserTaskHistory(db, str(user.id))
        return [TaskHistoryS.model_validate(entry) for entry in history]
    except Exception as e:
        logger.error(f"Error retrieving history: {e}")
        raise HTTPException(HTTP_STATUS_BAD_REQUEST, "Error retrieving history")


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_by_id_endpoint(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(get_current_user)) -> TaskResponse:

    validate_uuid(task_id)
    task = await db_ops.ReturnTask(db, task_id)
    if not task or task.user_id != str(user.id):
        raise HTTPException(HTTP_STATUS_NOT_FOUND, "Task not found")
    return TaskResponse.model_validate(task)


@router.post("/cancel_task/{task_id}", response_model=TaskResponse)
async def cancel_task_endpoint(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(get_current_user)) -> TaskResponse:

    validate_uuid(task_id)
    task = await db_ops.ReturnTask(db, task_id)
    if not task or task.user_id != str(user.id):
        raise HTTPException(HTTP_STATUS_NOT_FOUND, "Task not found")
    
    await db_ops.update_task_status(db, task_id, "CANCELLED")
    task = await db_ops.ReturnTask(db, task_id)
    
    logger.info(f"Task {task_id} cancelled by user {user.id}")
    return TaskResponse.model_validate(task)


@router.delete("/delete_task/{task_id}", response_model=TaskResponse)
async def delete_task_endpoint(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(get_current_user)) -> TaskResponse:

    validate_uuid(task_id)
    task = await db_ops.ReturnTask(db, task_id)
    if not task or task.user_id != str(user.id):
        raise HTTPException(HTTP_STATUS_NOT_FOUND, "Task not found")
    
    task_response = TaskResponse.model_validate(task)
    await db_ops.DeleteTask(db, task_id)
    
    logger.info(f"Task {task_id} deleted by user {user.id}")
    return task_response


@router.get("/history/{task_id}", response_model=List[TaskHistoryS])
async def get_task_history_by_task_endpoint(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(get_current_user)) -> List[TaskHistoryS]:

    validate_uuid(task_id)
    task = await db_ops.ReturnTask(db, task_id)
    if not task or task.user_id != str(user.id):
        raise HTTPException(HTTP_STATUS_NOT_FOUND, "Task not found")
    
    history = await db_ops.ReturnTaskHistoryByTask(db, str(user.id), task.task_type)
    return [TaskHistoryS.model_validate(entry) for entry in history]
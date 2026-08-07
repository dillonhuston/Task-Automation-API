"""
Admin routes for Task Automation API.
All database interactions use DatabaseOperations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.dependencies.auth_utils import admin_required
from app.dependencies.dependency import get_database_operations
from app.models.database import get_db
from app.models.user import UserModel
from app.models.tasks import Task as TaskModel
from app.Database.DatabaseOperations import DatabaseOperations

router = APIRouter(prefix="/admin", tags=["Admin"])

#sTODO
@router.get("/users", dependencies=[Depends(admin_required)])
async def list_users(
    db: AsyncSession = Depends(get_db),
    db_ops: DatabaseOperations = Depends(get_database_operations)):
    
    users = await db_ops.GetUsers(db)
    if not users:
        raise HTTPException(
            status_code=404,
            detail="Not able to return any users. Are you sure they exist?"
                )
    return users


@router.delete("/users/{user_id}", dependencies=[Depends(admin_required)])
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    db_ops: DatabaseOperations = Depends(get_database_operations)): 

    deleted =  await db_ops.DeleteUser(db, user_id)
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Not able to delete user. Are you sure they exist?"
        )
    return{"message": "Succesfully removed user from database"}



@router.get("/history", dependencies=[Depends(admin_required)])
async def list_tasks(
    db: AsyncSession = Depends(get_db),
    db_ops: DatabaseOperations = Depends(get_database_operations)):

    tasks = await db_ops.ReturnAllTaskHistory(db, 5)
    if not tasks:
        return {"message": "No tasks to list."}
    return tasks


@router.delete("/tasks/{task_id}", dependencies=[Depends(admin_required)])
async def cancel_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    db_ops: DatabaseOperations = Depends(get_database_operations)):

    deleted = await db_ops.DeleteTask(db, task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": f"Task {task_id} successfully cancelled."}


@router.get("/summary", dependencies=[Depends(admin_required)])
async def get_summary(
    db: AsyncSession = Depends(get_db),
    db_ops: DatabaseOperations = Depends(get_database_operations)):

    user_count = await db_ops.GetUserCount(db)
    task_count = await db_ops.GetTaskCount(db)
    return {
        "total_users": user_count,
        "total_tasks": task_count
    }
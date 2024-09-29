from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from app.backend.db_depends import get_db
from typing import Annotated
from app.models import Task, User
from app.schemans import CreateTask, UpdateTask
from sqlalchemy import insert, select, update, delete
from slugify import slugify

router = APIRouter()

# Возвращает список всех задач
@router.get("/")
def all_tasks(db: Annotated[Session, Depends(get_db)]):
    tasks = db.scalars(select(Task)).all()
    return tasks

# Возвращает задачи по ID или выбрасывает исключение, если задача не найдена
@router.get("/{task_id}")
def task_by_id(task_id: int, db: Annotated[Session, Depends(get_db)]):
    task = db.scalar(select(Task).where(Task.id == task_id))
    if task is not None:
        return task
    raise HTTPException(status_code=404, detail="Task was not found")

# Создает новую задачу, используя данные из модели CreateTask. Обрабатывает возможные исключения.
@router.post("/create")
def create_task(task: CreateTask, user_id: int, db: Annotated[Session, Depends(get_db)]):
    user = db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise HTTPException(status_code=404, detail="User was not found")

    try:
        new_task = insert(Task).values(
            title=task.title,
            content=task.content,
            priority=task.priority,
            user_id=user_id,
            slug=slugify(task.title)
        )
        db.execute(new_task)
        db.commit()
        return {"status_code": status.HTTP_201_CREATED, "transaction": "Successful"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Task creation failed: {str(e)}")

# Обновляет данные задачи по ID, используя данные из модели UpdateTask
@router.put("/update/{task_id}")
def update_task(task_id: int, task: UpdateTask, db: Annotated[Session, Depends(get_db)]):
    stmt = update(Task).where(Task.id == task_id).values(
        title=task.title,
        content=task.content,
        priority=task.priority
    )
    result = db.execute(stmt)
    db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Task was not found")
    return {"status_code": status.HTTP_200_OK, "transaction": "Task update is successful!"}

# Удаляет задачу по ID
@router.delete("/delete/{task_id}")
def delete_task(task_id: int, db: Annotated[Session, Depends(get_db)]):
    stmt = delete(Task).where(Task.id == task_id)
    result = db.execute(stmt)
    db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Task was not found")
    return {"status_code": status.HTTP_200_OK, "transaction": "Task deletion is successful!"}

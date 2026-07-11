from typing import Optional

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from backend.db import get_session
from backend.models import TaskAlert
from backend.schemas import TaskCreateRequest, TaskOut

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskOut])
def list_tasks(status: Optional[str] = None, session: Session = Depends(get_session)):
    query = select(TaskAlert)
    if status:
        query = query.where(TaskAlert.status == status)
    return session.exec(query.order_by(TaskAlert.created_at.desc())).all()


@router.post("", response_model=TaskOut)
def create_task(payload: TaskCreateRequest, session: Session = Depends(get_session)):
    task = TaskAlert(**payload.model_dump())
    session.add(task)
    session.commit()
    session.refresh(task)
    return task

from datetime import timedelta
from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import Task, utcnow

def create_task(db: Session, request) -> Task:
    task = Task(
        task_type=request.task_type,
        payload=request.payload,
        priority=request.priority,
        max_attempts=request.max_attempts,
        sla_due_at=utcnow() + timedelta(seconds=request.sla_seconds),
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

def claim_next(db: Session) -> Task | None:
    task = db.scalar(select(Task).where(Task.status == "PENDING")
        .order_by(Task.priority.desc(), Task.created_at.asc(), Task.id.asc()).limit(1))
    if task is None:
        return None
    task.status = "RUNNING"
    task.attempts += 1
    db.commit()
    db.refresh(task)
    return task

def execute(task: Task) -> dict:
    if task.task_type == "uppercase":
        value = task.payload.get("text")
        if not isinstance(value, str):
            raise ValueError("uppercase tasks require payload.text to be a string")
        return {"text": value.upper()}
    if task.task_type == "echo":
        return {"echo": task.payload}
    if task.task_type == "simulate_failure":
        raise RuntimeError("Intentional simulated failure for retry demonstration")
    raise ValueError("Unsupported task type")

def process_one(db: Session) -> Task | None:
    task = claim_next(db)
    if task is None:
        return None
    try:
        task.result = execute(task)
        task.status = "SUCCEEDED"
        task.last_error = None
    except Exception as exc:
        task.last_error = str(exc)
        task.result = None
        task.status = "PENDING" if task.attempts < task.max_attempts else "FAILED"
    db.commit()
    db.refresh(task)
    return task

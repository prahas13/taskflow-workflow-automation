from datetime import datetime, timezone
from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from .database import Base, engine, get_db
from .models import Task
from .schemas import TaskCreate, TaskRead
from .services import create_task, process_one

Base.metadata.create_all(bind=engine)
app = FastAPI(title="TaskFlow Workflow Automation API", version="1.0.0",
              description="Priority scheduling, retries, and SLA tracking.")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/tasks", response_model=TaskRead, status_code=201)
def submit_task(request: TaskCreate, db: Session = Depends(get_db)):
    return create_task(db, request)

@app.get("/tasks", response_model=list[TaskRead])
def list_tasks(status: str | None = Query(default=None), limit: int = Query(default=50, ge=1, le=200),
               db: Session = Depends(get_db)):
    query = select(Task)
    if status:
        if status not in {"PENDING", "RUNNING", "SUCCEEDED", "FAILED"}:
            raise HTTPException(status_code=400, detail="Invalid status")
        query = query.where(Task.status == status)
    return list(db.scalars(query.order_by(Task.created_at.desc()).limit(limit)).all())

@app.get("/tasks/{task_id}", response_model=TaskRead)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.post("/worker/run-once", response_model=TaskRead | None)
def run_one(db: Session = Depends(get_db)):
    return process_one(db)

@app.get("/metrics/summary")
def summary(db: Session = Depends(get_db)):
    statuses = ("PENDING", "RUNNING", "SUCCEEDED", "FAILED")
    counts = {s: db.scalar(select(func.count()).select_from(Task).where(Task.status == s)) or 0 for s in statuses}
    now = datetime.now(timezone.utc)
    overdue = db.scalar(select(func.count()).select_from(Task).where(
        Task.status.in_(("PENDING", "RUNNING")), Task.sla_due_at < now)) or 0
    return {"total": sum(counts.values()), "pending": counts["PENDING"], "running": counts["RUNNING"],
            "succeeded": counts["SUCCEEDED"], "failed": counts["FAILED"], "overdue": overdue}

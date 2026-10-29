from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field, ConfigDict

TaskType = Literal["uppercase", "echo", "simulate_failure"]

class TaskCreate(BaseModel):
    task_type: TaskType
    payload: dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=0, ge=0, le=10)
    sla_seconds: int = Field(default=300, ge=1, le=86400)
    max_attempts: int = Field(default=3, ge=1, le=10)

class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    task_type: str
    payload: dict[str, Any]
    priority: int
    status: str
    attempts: int
    max_attempts: int
    created_at: datetime
    updated_at: datetime
    sla_due_at: datetime
    result: dict[str, Any] | None
    last_error: str | None

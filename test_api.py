import os
os.environ["DATABASE_URL"] = "sqlite:///./test_taskflow.db"

from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine

client = TestClient(app)

def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

def teardown_function():
    Base.metadata.drop_all(bind=engine)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_uppercase_task_lifecycle():
    created = client.post("/tasks", json={"task_type": "uppercase", "payload": {"text": "hello"}, "priority": 5})
    assert created.status_code == 201
    processed = client.post("/worker/run-once")
    assert processed.status_code == 200
    assert processed.json()["status"] == "SUCCEEDED"
    assert processed.json()["result"] == {"text": "HELLO"}

def test_failure_retries_then_fails():
    client.post("/tasks", json={"task_type": "simulate_failure", "payload": {}, "max_attempts": 2})
    first = client.post("/worker/run-once").json()
    assert first["status"] == "PENDING"
    assert first["attempts"] == 1
    second = client.post("/worker/run-once").json()
    assert second["status"] == "FAILED"
    assert second["attempts"] == 2

def test_priority_validation():
    response = client.post("/tasks", json={"task_type": "echo", "payload": {}, "priority": 99})
    assert response.status_code == 422

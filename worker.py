import time
from .database import Base, SessionLocal, engine
from .services import process_one

def main():
    Base.metadata.create_all(bind=engine)
    print("TaskFlow worker running. Ctrl+C to stop.")
    try:
        while True:
            with SessionLocal() as db:
                task = process_one(db)
                if task:
                    print(f"id={task.id} status={task.status} attempts={task.attempts}")
                    if task.last_error:
                        print(f"error={task.last_error}")
                else:
                    time.sleep(2)
    except KeyboardInterrupt:
        print("Worker stopped.")

if __name__ == "__main__":
    main()

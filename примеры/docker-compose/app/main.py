from celery.result import AsyncResult
from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .celery_conn import app as celery_app
from .db import engine
from .tasks import add, save_video

api = FastAPI(title="Docker: учебный backend")


@api.get("/")
def root():
    return {"message": "Backend работает в Docker"}


@api.get("/health/db")
def check_database():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="База недоступна") from None
    return {"database": "ok"}


@api.post("/tasks/add", status_code=202)
def start_add(a: int, b: int):
    task = add.delay(a, b)
    return {"task_id": task.id}


@api.post("/tasks/video", status_code=202)
def start_video():
    task = save_video.delay()
    return {"task_id": task.id}


@api.get("/tasks/{task_id}")
def get_task(task_id: str):
    task = AsyncResult(task_id, app=celery_app)
    state = task.state
    response = {"task_id": task.id, "state": state}

    if state == "PROGRESS":
        info = task.info
        if isinstance(info, dict):
            response["progress"] = info
    elif state == "SUCCESS":
        response["result"] = task.result
    elif state == "FAILURE":
        response["error"] = "Задача завершилась с ошибкой. Подробности в логах worker-а."

    return response

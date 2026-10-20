import os

from celery import Celery

app = Celery(
    "backend",
    broker=os.environ["CELERY_BROKER_URL"],
    backend=os.environ["CELERY_RESULT_BACKEND"],
    include=["app.tasks"],
)

app.conf.update(
    task_track_started=True,
    result_expires=3600,
)

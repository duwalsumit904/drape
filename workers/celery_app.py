from celery import Celery
from app.core.config import settings

celery_app = Celery("drape",

                    broker=settings.REDIS_URL,
                    backend=settings.REDIS_URL,
                    include=["workers.email_task"]

                            )


celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True
)




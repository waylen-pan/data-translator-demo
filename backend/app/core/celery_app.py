"""Celery 应用实例（Broker/Backend 使用 Redis）。"""

from __future__ import annotations

from celery import Celery

from app.core.config import settings


celery_app = Celery(
    "data_translator_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.translate"],
)

# Celery 基础配置：只使用 JSON 序列化，避免潜在安全风险与兼容问题
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
)


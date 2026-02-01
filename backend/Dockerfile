FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 创建最小权限用户
RUN addgroup --system app && adduser --system --ingroup app app

# 使用 venv，避免污染系统 site-packages
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# 先安装依赖以便构建缓存命中
COPY requirements.txt /app/requirements.txt
RUN pip install -U pip && pip install -r /app/requirements.txt

# 复制应用代码
COPY app /app/app

# 预创建持久化目录（首次挂载命名卷时会把权限一并带过去）
RUN mkdir -p /app/storage/uploads /app/storage/exports \
    && chown -R app:app /app

USER app

EXPOSE 8000

# 默认作为 API 进程启动；worker 在 compose 里覆盖 command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

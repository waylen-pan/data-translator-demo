# 数据翻译器（Demo）

目标：上传 JSON/JSONL/CSV/XLSX 数据，选择要翻译的字段/列与行数，后台调用大模型翻译成简体中文，并导出下载。

## 任务找回机制（无登录）

本项目不做账号体系，但支持“关网页后仍可找回任务结果”：

- 后端会给每个浏览器下发一个匿名会话 Cookie：`dt_client_id`（HttpOnly）
- 上传文件与翻译任务都会绑定该 `client_id`，并在查询/下载时做归属校验
- 因此：**同一浏览器**关闭页面后再打开仍可看到历史任务并下载结果；**换浏览器/无痕**即使拿到 `job_id` 也无法访问

### 升级注意（破坏性变更）

该能力引入了数据库字段 `client_id`，升级需要重建数据库/存储数据：

- Docker 部署：执行 `docker compose down -v` 清空数据卷后再 `docker compose up -d --build`
- 本地 SQLite：删除 `backend/data_translator.db` 后重启后端（会重新建表）

## Docker 一键部署（推荐：服务器部署最省心）

前端会被打包成静态资源，由 Nginx 提供页面并反代 `/api/*` 到后端；后端拆分为 `api`（FastAPI）+ `worker`（Celery），并使用 Redis + Postgres。

### 1) 准备环境变量

在项目根目录执行：

```bash
cp backend/.env.example backend/.env
```

编辑 `backend/.env`，至少配置：

- `ARK_API_KEY=...`（不配置会导致真实翻译失败；本地联调可在 `backend/.env` 里设置 `TRANSLATION_DRY_RUN=true`）

### 2) 启动

在 `data-translator-demo/` 目录执行：

```bash
docker compose up -d --build
```

访问：

- `http://<server-ip>:8080`（默认端口）

### 3) 常用运维命令

查看日志：

```bash
docker compose logs -f web
docker compose logs -f api
docker compose logs -f worker
```

停止：

```bash
docker compose down
```

清理数据（会删除 Postgres 数据卷与上传/导出文件，谨慎执行）：

```bash
docker compose down -v
```

### 4) 可选配置（通过环境变量）

- `WEB_PORT`：对外 Web 端口（默认 `8080`），例如临时改为 80：`WEB_PORT=80 docker compose up -d --build`
- `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB`：Postgres 账号与库名（默认都是 `data_translator`，建议线上改掉）
- `TRANSLATION_DRY_RUN`：是否使用 mock 翻译（默认 `false`；在 `backend/.env` 里设置，用于没有 Key 时跑通全链路）

## 运行前准备（本地开发）

- Node.js（建议 18+ 或 20+）
- Python 3.12
- Redis（用于 Celery broker/backend 与缓存）
  - 方式 A：Docker（可选）
  - 方式 B：本机 `redis-server`（推荐，零依赖）

## 启动（本地开发）

### 1) 启动 Redis

方式 A（Docker，可选）：用单独的 redis 容器（会映射到本机 `6379`，适合“本地跑后端/worker”的开发模式）：

```bash
docker run -d --name data-translator-redis -p 6379:6379 redis:7-alpine \
  redis-server --port 6379 --save "" --appendonly no
```

停止并删除该 redis 容器（可选）：

```bash
docker rm -f data-translator-redis
```

方式 B（本机 redis-server）：任意目录执行：

```bash
redis-server --port 6379 --save "" --appendonly no
```

### 2) 启动后端（FastAPI + Celery）

在 `data-translator-demo/backend/` 目录执行：

```bash
python3.12 -m venv venv
source venv/bin/activate
python -c 'import sys; print(sys.executable)'

pip install -U pip
pip install -r requirements.txt

cp .env.example .env
```

编辑 `.env`，至少配置：

- `ARK_API_KEY=...`

启动 API：

```bash
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

启动 Celery worker（另开一个终端，同目录）：

```bash
source venv/bin/activate
celery -A app.core.celery_app.celery_app worker -l info
```

### 3) 启动前端（React 19）

在 `data-translator-demo/frontend/` 目录执行：

```bash
npm install
npm run dev
```

浏览器打开前端地址（Vite 默认会输出）。

说明：开发期前端已通过 Vite proxy 将 `"/api"` 代理到 `http://localhost:8000`，因此前端请求不需要额外处理 CORS。

## 测试与构建

后端（在 `data-translator-demo/backend/`）：

```bash
source venv/bin/activate
pytest
```

前端（在 `data-translator-demo/frontend/`）：

```bash
npm run lint
npm run build
```


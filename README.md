# 数据翻译器（Demo）

目标：上传 JSON/JSONL/CSV/XLSX 数据，选择要翻译的字段/列与行数，后台调用大模型翻译成简体中文，并导出下载。

## 运行前准备

- Node.js（建议 18+ 或 20+）
- Python 3.12
- Redis（用于 Celery broker/backend 与缓存）
  - 方式 A：Docker（可选）
  - 方式 B：本机 `redis-server`（推荐，零依赖）

## 启动（本地开发）

### 1) 启动 Redis

方式 A（Docker，可选）：在 `data-translator-demo/` 目录执行：

```bash
docker compose up -d
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


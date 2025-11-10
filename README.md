## AI Finance Backend

FastAPI BFF for the AI Finance System, providing unified APIs for ad spend reporting, recharge workflows, and reconciliation.

### ⚠️ Environment Files

生产环境不要提交真实 `.env`；请只提交 `.env.example` 并在部署时复制为 `.env` 后填充敏感配置。

### 本地运行

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 本地测试

```bash
pytest -v --disable-warnings
```

### Docker 启动

```bash
docker build -t ai-finance-backend .
docker run -p 8000:8000 --env-file .env ai-finance-backend
```

### 主要接口

- `GET /healthz`
- `GET /readyz`
- `POST /api/v1/adspend/report`
- `POST /api/v1/topups`
- `POST /api/v1/topups/{id}/approve|pay|confirm`
- `POST /api/v1/reconciliations/auto`
- `GET /api/v1/reconciliations`

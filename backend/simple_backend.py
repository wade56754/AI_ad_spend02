from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

app = FastAPI(title="AI广告代投系统", debug=True)

# 允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 模拟项目数据
MOCK_PROJECTS = {
    1: {
        "id": 1,
        "name": "春季推广活动",
        "client_name": "ABC科技公司",
        "description": "针对新品上市的全方位推广活动",
        "currency": "USD",
        "budget": 50000,
        "current_spend": 32500,
        "status": "active",
        "priority": "high",
        "start_date": "2025-01-01",
        "end_date": "2025-03-31",
        "progress": 65,
        "team_lead_name": "张经理",
        "team_members_count": 5,
        "ad_accounts_count": 8,
        "created_at": "2024-12-15T09:00:00Z",
        "updated_at": "2025-01-12T14:30:00Z",
        "roi": 3.8,
        "conversion_rate": 0.025
    }
}

@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/api/v1/projects/{project_id}")
async def get_project(project_id: int):
    if project_id not in MOCK_PROJECTS:
        raise HTTPException(status_code=404, detail="Project not found")

    return {
        "success": True,
        "data": MOCK_PROJECTS[project_id],
        "message": "获取项目详情成功",
        "code": "SUCCESS",
        "request_id": "test-123",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/projects")
async def list_projects():
    projects = list(MOCK_PROJECTS.values())
    return {
        "success": True,
        "data": {
            "items": projects,
            "meta": {
                "pagination": {
                    "page": 1,
                    "page_size": 20,
                    "total": len(projects),
                    "total_pages": 1
                }
            }
        },
        "message": "获取项目列表成功",
        "code": "SUCCESS",
        "request_id": "test-456",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    print("启动简化版后端服务...")
    print("API文档: http://localhost:8001/docs")
    uvicorn.run(app, host="0.0.0.0", port=8001)
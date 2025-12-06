from fastapi import FastAPI

app = FastAPI()

# 测试路由修复是否生效 - 模拟正确的路由结构
@app.get("/api/v1/projects/{project_id}")
async def get_project(project_id: int):
    return {"success": True, "data": {"id": project_id, "name": "测试项目"}}

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
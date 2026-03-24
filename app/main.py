"""FastAPI 应用入口"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.core.database import engine, Base
from app.api.v1.routes import health_router, chat_router, knowledge_router
from app.utils.logger import logger

# 创建 FastAPI 应用实例
app = FastAPI(
    title="AI Agent RAG Project",
    description="基于 LangGraph 和 RAG 的智能问答系统",
    version="1.0.0"
)


# 注册路由
app.include_router(health_router)
app.include_router(chat_router)
app.include_router(knowledge_router)

# 托管前端静态文件
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
async def serve_frontend():
    return FileResponse("frontend/index.html")


@app.on_event("startup")
async def startup_event():
    """应用启动时自动创建数据库表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("--- MySQL: Tables checked/created successfully ---")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    logger.info("--- Application shutdown ---")

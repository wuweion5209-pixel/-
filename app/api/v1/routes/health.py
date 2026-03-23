"""健康检查和根路由"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "running",
        "database": "connected"
    }


@router.get("/")
async def root():
    """根路由"""
    return {"message": "Welcome to my AI Agent Project"}

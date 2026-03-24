"""健康检查和根路由"""
from fastapi import APIRouter

router = APIRouter()

#如果服务状态正常，则返回running，否则返回error
@router.get("/health")
async def health_check():
    try:
        return {"status": "running"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
#根路由返回欢迎信息
@router.get("/root")
async def root():
    return {"message": "Welcome to my AI Agent Project"}

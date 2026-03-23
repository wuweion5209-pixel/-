"""API 路由模块"""
from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.chat import router as chat_router
from app.api.v1.routes.knowledge import router as knowledge_router

__all__ = ["health_router", "chat_router", "knowledge_router"]

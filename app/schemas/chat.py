"""聊天相关的 Pydantic 模型"""
from pydantic import BaseModel

from app.core.config import settings


class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str
    user_id: str=settings.DEFAULT_USER_ID


class ChatResponse(BaseModel):
    """聊天响应模型"""
    status: str
    answer: str
    conversation_id: str | None = None


class RAGSaveRequest(BaseModel):
    """RAG 保存请求模型"""
    text: str

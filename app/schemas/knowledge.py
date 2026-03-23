"""知识库相关的 Pydantic 模型"""
from pydantic import BaseModel
from typing import Optional


class KnowledgeItem(BaseModel):
    """知识库条目"""
    id: str
    content: str
    metadata: Optional[dict] = None


class KnowledgeListResponse(BaseModel):
    """知识库列表响应"""
    total: int
    items: list[KnowledgeItem]


class KnowledgeClearResponse(BaseModel):
    """知识库清空响应"""
    status: str
    deleted_count: int

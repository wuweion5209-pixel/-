from pydantic import BaseModel
from typing import Optional


class RAGConfig(BaseModel):
    """RAG 模块配置"""
    # 向量检索
    vector_k: int = 10

    # BM25 关键词检索
    bm25_k: int = 10
    bm25_tokenizer: str = "jieba"

    # 融合参数
    fusion_algorithm: str = "rrf"
    rrf_k: float = 60

    # 重排序
    rerank_enabled: bool = True
    rerank_top_k: int = 5
    rerank_model: str = "bge-reranker-base"

    # 过滤阈值
    similarity_threshold: float = 0.4
    keyword_match_weight: float = 0.3


rag_config = RAGConfig()
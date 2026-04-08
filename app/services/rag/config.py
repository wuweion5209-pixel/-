from pydantic import BaseModel
from typing import Optional


class RAGConfig(BaseModel):
    """RAG 模块配置"""
    # 向量检索
    vector_k: int = 20  # 增加检索数量

    # BM25 关键词检索
    bm25_k: int = 20    # 增加检索数量
    bm25_tokenizer: str = "jieba"

    # 融合参数
    fusion_algorithm: str = "rrf"
    rrf_k: float = 60

    # 重排序
    rerank_enabled: bool = False  # 已禁用（模型加载失败）
    rerank_top_k: int = 20  # 重排序后保留数量
    rerank_model: str = "bge-reranker-base"

    # 过滤阈值（已转换为正数分数，越大越相似）
    similarity_threshold: float = 0.1  # 向量检索阈值
    keyword_match_weight: float = 0.3

    # 查询扩展
    query_expansion: bool = True  # 启用查询扩展
    expansion_keywords: list = ["参考文献", "引用", "references", "相关工作"]  # 扩展关键词

    # 分块配置
    chunk_size: int = 500  # 每块最大字符数
    chunk_overlap: int = 50  # 块之间重叠字符数
    min_chunk_size: int = 100  # 最小块字符数


rag_config = RAGConfig()
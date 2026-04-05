"""RAG 模块 - 混合检索 + 重排序"""

from app.services.rag.retriever import hybrid_search, get_hybrid_retriever, HybridRetriever
from app.services.rag.config import rag_config, RAGConfig
from app.services.rag.vector_retriever import VectorRetriever, get_vector_retriever
from app.services.rag.bm25_retriever import BM25Retriever, get_bm25_retriever
from app.services.rag.fusion import FusionRetriever, get_fusion_retriever
from app.services.rag.reranker import Reranker, get_reranker
from app.services.rag.chunker import TextChunker, get_chunker

__all__ = [
    # 主入口
    "hybrid_search",
    "get_hybrid_retriever",
    "HybridRetriever",
    # 配置
    "rag_config",
    "RAGConfig",
    # 子模块
    "get_vector_retriever",
    "VectorRetriever",
    "get_bm25_retriever",
    "BM25Retriever",
    "get_fusion_retriever",
    "FusionRetriever",
    "get_reranker",
    "Reranker",
    "get_chunker",
    "TextChunker",
]
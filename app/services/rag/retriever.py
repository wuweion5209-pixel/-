"""混合检索主入口"""

from typing import List
from langchain_core.documents import Document
from app.services.rag.vector_retriever import get_vector_retriever
from app.services.rag.bm25_retriever import get_bm25_retriever
from app.services.rag.fusion import get_fusion_retriever
from app.services.rag.reranker import get_reranker
from app.services.rag.config import rag_config
from app.utils.logger import logger


class HybridRetriever:
    """混合检索器 - 整合向量检索、BM25 检索、RRF 融合、重排序"""

    def __init__(self):
        self.vector_retriever = get_vector_retriever()
        self.bm25_retriever = get_bm25_retriever()
        self.fusion_retriever = get_fusion_retriever(k=rag_config.rrf_k)
        self.reranker = get_reranker(model_name=rag_config.rerank_model)

    async def search(self, query: str) -> List[Document]:
        """
        混合检索主入口
        1. 向量检索
        2. BM25 检索
        3. RRF 融合
        4. 查询扩展（如结果不足）
        5. 重排序（可选）

        Args:
            query: 用户查询

        Returns:
            List[Document]: 检索结果列表
        """
        # 1. 向量检索
        vector_results = self.vector_retriever.search(
            query=query,
            k=rag_config.vector_k,
            similarity_threshold=rag_config.similarity_threshold
        )
        logger.info(f"[混合检索] 向量检索返回 {len(vector_results)} 条")

        # 2. BM25 检索
        bm25_results = self.bm25_retriever.search(
            query=query,
            k=rag_config.bm25_k
        )
        logger.info(f"[混合检索] BM25 检索返回 {len(bm25_results)} 条")

        # 3. RRF 融合
        if not vector_results and not bm25_results:
            logger.warning("[混合检索] 向量和 BM25 均无结果")
            return []

        fused_results = self.fusion_retriever.fuse([vector_results, bm25_results])
        logger.info(f"[混合检索] RRF 融合后 {len(fused_results)} 条")

        # 4. 如果需要查询扩展（当检索结果少时）
        if rag_config.query_expansion and len(fused_results) < 5:
            logger.info(f"[混合检索] 检索结果较少，进行查询扩展...")
            for kw in rag_config.expansion_keywords:
                # 扩展查询
                expanded_query = f"{query} {kw}"
                # 额外检索
                extra_vector = self.vector_retriever.search(
                    query=expanded_query,
                    k=5,
                    similarity_threshold=0.2  # 更低的阈值
                )
                extra_bm25 = self.bm25_retriever.search(expanded_query, k=5)

                if extra_vector or extra_bm25:
                    extra_fused = self.fusion_retriever.fuse([extra_vector, extra_bm25])
                    # 合并到主结果（去重）
                    existing_texts = {t for t, _, _ in fused_results}
                    added_count = 0
                    for text, score, meta in extra_fused:
                        if text not in existing_texts and len(fused_results) < rag_config.rerank_top_k:
                            fused_results.append((text, score, meta))
                            added_count += 1
                    if added_count > 0:
                        logger.info(f"[混合检索] 扩展关键词'{kw}'新增 {added_count} 条")

            logger.info(f"[混合检索] 扩展后总计 {len(fused_results)} 条")

        # 5. 重排序
        if rag_config.rerank_enabled:
            reranked_results = self.reranker.rerank(
                query=query,
                candidates=fused_results,
                top_k=rag_config.rerank_top_k
            )
            logger.info(f"[混合检索] 重排序后返回 {len(reranked_results)} 条")

            # 转换为 Document 对象
            docs = [
                Document(page_content=text, metadata=metadata)
                for text, _, metadata in reranked_results
            ]
        else:
            # 不重排序，直接取 top-k
            docs = [
                Document(page_content=text, metadata=metadata)
                for text, _, metadata in fused_results[:rag_config.rerank_top_k]
            ]
            logger.info(f"[混合检索] 直接返回 top-{rag_config.rerank_top_k} 条")

        return docs


# 全局单例
_hybrid_retriever = None


def get_hybrid_retriever() -> HybridRetriever:
    """获取混合检索器单例"""
    global _hybrid_retriever
    if _hybrid_retriever is None:
        _hybrid_retriever = HybridRetriever()
    return _hybrid_retriever


# 兼容旧接口
async def hybrid_search(query: str) -> List[Document]:
    """混合检索入口函数（兼容旧接口）"""
    retriever = get_hybrid_retriever()
    return await retriever.search(query)
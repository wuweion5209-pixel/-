from typing import List, Tuple, Dict
from app.core.vectorstore import get_vector_store
from app.utils.logger import logger


class VectorRetriever:
    """向量检索器"""

    def __init__(self, collection_name: str = "knowledge_base"):
        self.collection_name = collection_name

    def search(
        self,
        query: str,
        k: int = 10,
        similarity_threshold: float = 0.4
    ) -> List[Tuple[str, float, Dict]]:
        """
        向量检索

        Args:
            query: 用户查询
            k: 返回结果数量
            similarity_threshold: 相似度阈值，低于此分数的结果将被过滤

        Returns:
            List[(文档文本, 相似度分数, 元数据)]
        """
        vs = get_vector_store(self.collection_name)

        # 检索并返回相似度分数
        results = vs.similarity_search_with_relevance_scores(query, k=k)

        # 转换为 (文本, 分数, 元数据) 格式
        output = []
        for doc, score in results:
            # 过滤低相似度结果
            if score >= similarity_threshold:
                output.append((doc.page_content, float(score), doc.metadata))

        logger.info(f"[向量检索] 返回 {len(output)} 条结果 (阈值={similarity_threshold})")
        return output


# 全局单例
_vector_retriever = None


def get_vector_retriever(collection_name: str = "knowledge_base") -> VectorRetriever:
    """获取向量检索器单例"""
    global _vector_retriever
    if _vector_retriever is None or _vector_retriever.collection_name != collection_name:
        _vector_retriever = VectorRetriever(collection_name)
    return _vector_retriever
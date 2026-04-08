from typing import List, Tuple, Dict
from app.core.vectorstore import get_vector_store
from app.utils.logger import logger


def _cosine_distance_to_similarity(distance: float) -> float:
    """将余弦距离转换为相似度分数（用于比较）
    Chroma 返回余弦距离（负数，越接近0越好）
    转换为正数后越大表示越相似
    """
    # 直接取负值，将负距离转为正分数用于比较
    # 例如: -0.06 -> 0.06, -0.10 -> 0.10
    return -distance


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

        # 转换为 (文本, 分数, 元数据) 格式，并过滤低相似度结果
        output = []
        for doc, distance in results:
            # 将距离转换为相似度 (Chroma 返回的是余弦距离)
            similarity = _cosine_distance_to_similarity(distance)
            # 过滤低相似度结果
            if similarity >= similarity_threshold:
                output.append((doc.page_content, similarity, doc.metadata))

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

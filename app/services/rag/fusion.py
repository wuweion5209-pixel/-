"""RRF 融合模块"""

from typing import List, Tuple, Dict
from app.utils.logger import logger


class FusionRetriever:
    """RRF 融合器"""

    def __init__(self, k: float = 60):
        self.k = k

    def fuse(
        self,
        results_list: List[List[Tuple[str, float, Dict]]]
    ) -> List[Tuple[str, float, Dict]]:
        """
        倒数排名融合（Reciprocal Rank Fusion）

        Args:
            results_list: 多个检索结果列表，每个元素是 [(文本, 分数, metadata), ...]

        Returns:
            融合后的结果列表: [(文本, 融合分数, metadata), ...]
            按融合分数从高到低排序
        """
        if not results_list:
            return []

        # 存储每个文档的融合分数和元数据
        doc_info: Dict[str, dict] = {}

        # 遍历每个检索结果
        for results in results_list:
            # 按排名遍历（排名从 1 开始）
            for rank, (text, _, metadata) in enumerate(results, start=1):
                # RRF 公式: score = 1 / (k + rank)
                rrf_score = 1.0 / (self.k + rank)

                if text not in doc_info:
                    doc_info[text] = {"score": 0.0, "metadata": metadata}

                # 累加各方法的 RRF 分数
                doc_info[text]["score"] += rrf_score

        # 按融合分数降序排序
        sorted_docs = sorted(
            doc_info.items(),
            key=lambda x: x[1]["score"],
            reverse=True
        )

        logger.info(f"[RRF融合] 融合 {len(results_list)} 个结果，共 {len(sorted_docs)} 个唯一文档")

        # 转换为返回格式
        return [(text, info["score"], info["metadata"]) for text, info in sorted_docs]


# 全局单例
_fusion_retriever = None


def get_fusion_retriever(k: float = 60) -> FusionRetriever:
    """获取 RRF 融合器单例"""
    global _fusion_retriever
    if _fusion_retriever is None or _fusion_retriever.k != k:
        _fusion_retriever = FusionRetriever(k)
    return _fusion_retriever
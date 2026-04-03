"""重排序模块"""

from typing import List, Tuple, Dict
from sentence_transformers import CrossEncoder
from app.utils.logger import logger
import torch


class Reranker:
    """Cross-Encoder 重排序器"""

    def __init__(self, model_name: str = "BAAI/bge-reranker-base"):
        self.model_name = model_name
        self._model = None

    def _load_model(self):
        """加载重排序模型"""
        if self._model is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"[重排序] 加载模型: {self.model_name}, 设备: {device}")
            self._model = CrossEncoder(self.model_name, device=device)

    def rerank(
        self,
        query: str,
        candidates: List[Tuple[str, float, Dict]],
        top_k: int = 5
    ) -> List[Tuple[str, float, Dict]]:
        """
        对候选文档进行重排序

        Args:
            query: 用户查询
            candidates: 候选文档列表 [(文本, 融合分数, 元数据), ...]
            top_k: 返回前 k 个结果

        Returns:
            重排序后的结果: [(文本, 重排序分数, 元数据), ...]
        """
        if not candidates:
            return []

        self._load_model()

        # 构建输入对: [(query, doc_text), ...]
        pairs = [(query, text) for text, _, _ in candidates]

        # 获取交叉编码器分数
        scores = self._model.predict(pairs)

        # 组合结果并按分数降序排序
        reranked = []
        for i, (text, _, metadata) in enumerate(candidates):
            reranked.append((text, float(scores[i]), metadata))

        reranked.sort(key=lambda x: x[1], reverse=True)

        # 取 top_k
        result = reranked[:top_k]
        logger.info(f"[重排序] 从 {len(candidates)} 个候选中返回 {len(result)} 个")

        return result


# 全局单例
_reranker = None


def get_reranker(model_name: str = "BAAI/bge-reranker-base") -> Reranker:
    """获取重排序器单例"""
    global _reranker
    if _reranker is None or _reranker.model_name != model_name:
        _reranker = Reranker(model_name)
    return _reranker
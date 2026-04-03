import jieba
from rank_bm25 import BM25Okapi
from typing import List, Tuple, Dict
from app.core.vectorstore import get_vector_store
from app.utils.logger import logger


class BM25Retriever:
      """BM25 关键词检索器"""

      def __init__(self, collection_name: str = "knowledge_base"):
          self.collection_name = collection_name
          self._indexed = False
          self._corpus: List[str] = []
          self._bm25 = None
          self._doc_ids: List[str] = []
          self._metadatas: List[Dict] = []

      def _build_index(self):
          """从 Chroma 加载全部文档，构建 BM25 索引"""
          vs = get_vector_store(self.collection_name)

          # 获取全部文档
          all_docs = vs.get()

          self._corpus = list(all_docs["documents"])
          self._doc_ids = list(all_docs["ids"])
          
          raw_metadatas = all_docs.get("metadatas", [])                           
          self._metadatas = []                                                    
          for i, _ in enumerate(self._corpus):                                    
                 if i < len(raw_metadatas):                                          
                      self._metadatas.append(raw_metadatas[i])                        
                 else:                                                               
                   self._metadatas.append({})     
        

          # 分词
          tokenized_corpus = [list(jieba.cut(doc)) for doc in self._corpus]
          self._bm25 = BM25Okapi(tokenized_corpus)
          self._indexed = True

          logger.info(f"BM25 索引构建完成，共 {len(self._corpus)} 条文档")

      def search(self, query: str, k: int = 10) -> List[Tuple[str, float, Dict]]:
          """
          搜索并返回 top-k 结果

          Returns:
              List[(文本, BM25分数, metadata)]
          """
          if not self._indexed:
              self._build_index()

          # 分词查询
          query_tokens = list(jieba.cut(query))

          # 计算 BM25 分数
          scores = self._bm25.get_scores(query_tokens)

          # 获取 top-k 索引
          top_indices = sorted(range(len(scores)), key=lambda i: scores[i],
  reverse=True)[:k]

          results = []
          for idx in top_indices:
              if scores[idx] > 0:
        
                  results.append((self._corpus[idx], float(scores[idx]), self.metadata))        

          return results

      def reset_index(self):
          """重建索引（当知识库有更新时调用）"""
          self._indexed = False
          self._corpus = []
          self._bm25 = None


  # 全局单例
_bm25_retriever = None


def get_bm25_retriever(collection_name: str = "knowledge_base") -> BM25Retriever:        
      """获取 BM25 检索器单例"""
      global _bm25_retriever
      if _bm25_retriever is None or _bm25_retriever.collection_name != collection_name:    
          _bm25_retriever = BM25Retriever(collection_name)
      return _bm25_retriever


#总结流程：
#







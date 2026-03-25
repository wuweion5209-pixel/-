import os
import chromadb
from langchain_chroma import Chroma
from langchain_community.embeddings import DashScopeEmbeddings
from app.core.config import settings

# 1. 路径配置:为了让所有对向量数据库的操作都强制
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "vector_db_data")
if not os.path.exists(DB_PATH):
    os.makedirs(DB_PATH)

# 2. 【核心修复】创建一个带有 name 属性的 Embedding 子类 (防止 Pydantic 报错)
#因为langchain在内部验证模型是有时候会验证name属性，在这里手动添加一个防止出错
class SafeDashScopeEmbeddings(DashScopeEmbeddings):
    @property
    def name(self) -> str:
        return "dashscope-text-embedding-v2"

# 初始化模型：embeddings模型是用于将数据向量转化的对象，依赖于大模型平台提供的sdk产生，不同的大模型所使用的embeddings的维度也不同，
#embeddings将数据在向量数据库里面存取，在一个服务里，需要使用的embeddings模型也必须相同
#embeddings模型一般运行在平台提供的服务器里，因为矩阵运算太过复杂
embeddings = SafeDashScopeEmbeddings(
    model="text-embedding-v2",
    dashscope_api_key=settings.DASHSCOPE_API_KEY
)

COLLECTION_NAME = "knowledge_base"

# 全局单例 VectorStore 对象
# ⚠️ 直接在这里初始化 LangChain 的 Chroma 对象，确保所有操作都基于同一个实例
#通过这个函数可以得到唯一的chroma对象，通过这个对象可以实现对向量数据库的增删改查
_vector_store = None

def get_vector_store():
    """
    获取全局唯一的 LangChain Chroma 向量库实例
    """
    global _vector_store
    if _vector_store is None:
        _vector_store = Chroma(
            persist_directory=DB_PATH,
            embedding_function=embeddings,
            collection_name=COLLECTION_NAME
        )
    return _vector_store

#此函数返回一个collection，这个collection是对应向量数据库的一个collection对象
#通过这个collection也可以实现对向量数据库的增删改查，但是需要提前将需要操作的数据转化为向量
#client代表与向量数据库建立物理连接，也代表对向量数据库的一个“管理员”
def get_vector_collection():

    client = chromadb.PersistentClient(path=DB_PATH)
    return client.get_or_create_collection(name=COLLECTION_NAME)


    
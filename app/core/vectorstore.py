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

# 多集合单例缓存，key 为 collection_name
_vector_stores: dict = {}

def get_vector_store(collection_name: str = "knowledge_base"):
    """
    获取指定 collection 的 LangChain Chroma 向量库实例（单例复用）
    支持集合：knowledge_base（外部知识库）、episodic（情节记忆）
    """
    global _vector_stores
    if collection_name not in _vector_stores:
        _vector_stores[collection_name] = Chroma(
            persist_directory=DB_PATH,
            embedding_function=embeddings,
            collection_name=collection_name
        )
    return _vector_stores[collection_name]

#此函数返回一个collection，这个collection是对应向量数据库的一个collection对象
#通过这个collection也可以实现对向量数据库的增删改查，但是需要提前将需要操作的数据转化为向量
#client代表与向量数据库建立物理连接，也代表对向量数据库的一个“管理员”
def get_vector_collection():

    client = chromadb.PersistentClient(path=DB_PATH)
    return client.get_or_create_collection(name=COLLECTION_NAME)


    
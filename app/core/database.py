from sqlalchemy.ext.asyncio import create_async_engine       # 导入异步引擎创建函数
from sqlalchemy.ext.asyncio import AsyncSession             # 导入异步会话类型
from sqlalchemy.orm import sessionmaker                      # 导入会话生成器
from sqlalchemy.ext.declarative import declarative_base      # 导入 ORM 基类
from app.core.config import settings                         # 导入刚才配置好的 settings

# 创建所有数据库模型的基类
Base = declarative_base()                                    # 所有的 Model 都要继承它

# 创建异步 MySQL 引擎

engine = create_async_engine(                                
    settings.DATABASE_URL,                                   # 从配置中读取连接字符串
    echo=True,                                               # 开启 SQL 日志，方便调试时查看
    pool_pre_ping=True,                                      # 每次使用连接前先检查是否存活
    pool_recycle=3600                                        # 连接每隔一小时自动回收
)

# 创建异步会话工厂                     
AsyncSessionLocal = sessionmaker(                            
    engine,                                                  # 绑定上面创建的引擎
    class_=AsyncSession,                                     # 指定这是一个异步会话
    expire_on_commit=False                                    # 提交事务后不刷新对象
)                                  
                        
# 定义数据库连接依赖项
async def get_db():
    async with AsyncSessionLocal() as session:               # 使用异步上下文管理
        yield session                                        # 返回会话供 API 使用


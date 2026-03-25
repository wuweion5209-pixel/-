from pydantic_settings import BaseSettings
from langchain_community.chat_models.tongyi import ChatTongyi
from app.utils.logger import logger

class Settings(BaseSettings):
    DATABASE_URL: str                                            # 对应 .env 里的变量
    DASHSCOPE_API_KEY: str
    DEFAULT_USER_ID: str
    AIDER_MODEL: str = "qwen-turbo"

    class Config:
        env_file = ".env"

settings = Settings()
logger.info(f"配置加载成功，使用模型: {settings.AIDER_MODEL}")
llm = ChatTongyi(model=settings.AIDER_MODEL, dashscope_api_key=settings.DASHSCOPE_API_KEY)
logger.info("LLM 初始化完成")
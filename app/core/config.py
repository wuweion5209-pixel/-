from pydantic_settings import BaseSettings                       
from langchain_community.chat_models.tongyi import ChatTongyi

class Settings(BaseSettings):
    DATABASE_URL: str                                            # 对应 .env 里的变量
    DASHSCOPE_API_KEY: str
    DEFAULT_USER_ID: str
    AIDER_MODEL: str = "qwen-turbo"

    class Config:
        env_file = ".env"                                        

settings = Settings()
llm = ChatTongyi(model=settings.AIDER_MODEL, dashscope_api_key=settings.DASHSCOPE_API_KEY)
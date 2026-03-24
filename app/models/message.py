from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from app.core.database import Base
from datetime import datetime
import uuid
class Message(Base):                                         
    __tablename__ = "messages"                               # 表名：消息记录表

    id = Column(Integer, primary_key=True, index=True)
    user_id=Column(String(50),index=True)       
    conversation_id = Column(String(100), index=True,default=lambda:str(uuid.uuid4()))         # 会话 ID，用于区分不同的聊天
    role = Column(String(20))                                # 角色：user 或 assistant
    content = Column(Text)                                   # 聊天内容
    created_at = Column(DateTime, default=datetime.now)  # 发送时间

    
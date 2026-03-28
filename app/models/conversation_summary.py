from sqlalchemy import Column, Integer, String, Text, DateTime
from app.core.database import Base
from datetime import datetime


class ConversationSummary(Base):
    __tablename__ = "conversation_summaries"
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String(100), unique=True, index=True)
    summary = Column(Text)
    message_count = Column(Integer, default=0)  # 生成摘要时的消息总数
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

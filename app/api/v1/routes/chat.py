"""聊天相关路由"""
import uuid
from fastapi import APIRouter, HTTPException
from app.services.agent_chains_db import add_knowledge_to_db
from app.services.agent_service import agent_app
from app.core.config import settings
from app.schemas.chat import ChatRequest, ChatResponse, RAGSaveRequest

router = APIRouter(prefix="/chat", tags=["chat"])

current_conversation_id = None


@router.post("/new_session")
async def create_new_session():
    """创建新的聊天会话"""
    global current_conversation_id
    current_conversation_id = str(uuid.uuid4())
    return current_conversation_id


@router.post("/ragsave")
async def rag_save(request: RAGSaveRequest):
    """保存知识到向量数据库"""
    doc_id = str(uuid.uuid4())
    try:
        await add_knowledge_to_db(text=request.text, doc_id=doc_id)
        return {"status": "success", "message": "数据已存储"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/agent_test", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """聊天接口"""
    global current_conversation_id

    if current_conversation_id is None:
        current_conversation_id = str(uuid.uuid4())

    try:
        initial_state = {
            "input": request.message,
            "user_id": settings.DEFAULT_USER_ID,
            "conversation_id": current_conversation_id,
            "retrieval_count": 0,
            "chat_history": [],
            "messages": [],
            "answer": ""
        }

        final_state = await agent_app.ainvoke(initial_state)

        return {
            "status": "success",
            "answer": final_state["answer"],
            "conversation_id": current_conversation_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


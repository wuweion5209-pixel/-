"""聊天相关路由"""
import uuid
from fastapi import APIRouter, HTTPException, UploadFile, File
from app.services.agent_chains_db import add_knowledge_to_db, add_pdf_to_db, async_delete_conversation, async_get_conversations
from app.services.agent_service import agent_app
from app.core.config import settings
from app.schemas.chat import ChatRequest, ChatResponse, RAGSaveRequest
from app.utils.logger import logger

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/ragsave")
async def rag_save(request: RAGSaveRequest):
    """保存知识到向量数据库"""
    doc_id = str(uuid.uuid4())
    try:
        await add_knowledge_to_db(text=request.text, doc_id=doc_id, source=request.source)
        logger.info(f"知识存储成功: doc_id={doc_id}")
        return {"status": "success", "message": "数据已存储"}
    except Exception as e:
        logger.error(f"知识存储失败: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """上传 PDF 文件到向量数据库"""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="只支持 PDF 文件")
    try:
        file_bytes = await file.read()
        page_count = await add_pdf_to_db(file_bytes=file_bytes, filename=file.filename)
        logger.info(f"PDF 上传成功: {file.filename}，{page_count} 页")
        return {"status": "success", "message": f"PDF 已存储，共 {page_count} 页"}
    except ValueError as e:
        logger.warning(f"PDF 解析无内容: {file.filename} - {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"PDF 上传失败: {file.filename} - {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agent_response", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """聊天接口"""

    logger.info(f"收到聊天请求: session={request.conversation_id}, message={request.message[:50]}")
    try:
        initial_state = {
            "input": request.message,
            "user_id": settings.DEFAULT_USER_ID,
            "conversation_id": request.conversation_id,
            "retrieval_count": 0,
            "tool_used": False,
            "chat_history": [],
            "messages": [],
            "answer": ""
        }

        final_state = await agent_app.ainvoke(initial_state)
        logger.info(f"Agent 响应完成: session={request.conversation_id}")

        return {
            "status": "success",
            "answer": final_state["answer"],
            "conversation_id": request.conversation_id
        }

    except Exception as e:
        logger.error(f"聊天请求处理失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/show_conversatios")
async def show_conversatios():
    conversations = await async_get_conversations(user_id=settings.DEFAULT_USER_ID)
    return {"status": "success", "message": conversations}

@router.delete("/delete_conversation")
async def delete_conversation(conversation_id: str):
    await async_delete_conversation(conversation_id)
    return {"status": "success", "message": "会话已删除"}
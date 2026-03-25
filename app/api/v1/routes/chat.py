"""聊天相关路由"""
import uuid
from fastapi import APIRouter, HTTPException, UploadFile, File
from app.services.agent_chains_db import add_knowledge_to_db, add_pdf_to_db
from app.services.agent_service import agent_app
from app.core.config import settings
from app.schemas.chat import ChatRequest, ChatResponse, RAGSaveRequest
from app.utils.logger import logger

router = APIRouter(prefix="/chat", tags=["chat"])

current_conversation_id = None


@router.post("/new_session")
async def create_new_session():
    """创建新的聊天会话"""
    global current_conversation_id
    current_conversation_id = str(uuid.uuid4())
    logger.info(f"新会话创建: {current_conversation_id}")
    return current_conversation_id


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
    global current_conversation_id

    if current_conversation_id is None:
        current_conversation_id = str(uuid.uuid4())

    logger.info(f"收到聊天请求: session={current_conversation_id}, message={request.message[:50]}")
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
        logger.info(f"Agent 响应完成: session={current_conversation_id}")

        return {
            "status": "success",
            "answer": final_state["answer"],
            "conversation_id": current_conversation_id
        }

    except Exception as e:
        logger.error(f"聊天请求处理失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


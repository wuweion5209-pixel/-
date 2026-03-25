import uuid
from sqlalchemy import select
from datetime import datetime
from app.core.vectorstore import get_vector_store
from app.models.message import Message
from app.core.database import AsyncSessionLocal
from app.core.config import llm
from app.utils.logger import logger
from pypdf import PdfReader
import io


async def add_pdf_to_db(file_bytes: bytes, filename: str):
    """解析 PDF 文件并存入向量数据库"""
    reader = PdfReader(io.BytesIO(file_bytes))
    texts = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and text.strip():
            texts.append((i + 1, text.strip()))

    if not texts:
        raise ValueError("PDF 中未提取到任何文本内容")

    vector_store = get_vector_store()
    for page_num, text in texts:
        doc_id = str(uuid.uuid4())
        vector_store.add_texts(
            texts=[text],
            ids=[doc_id],
            metadatas=[{"source": filename, "page": page_num}]
        )
    logger.info(f"PDF 存储完成: {filename}，共 {len(texts)} 页")
    return len(texts)


# --- 异步数据库操作函数 ---

async def async_get_history(conversation_id: str):

    async with AsyncSessionLocal() as session:
        stmt = (
            select(Message.role, Message.content)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.id.desc())
            .limit(20)
        )
        result = await session.execute(stmt)
        rows = result.all()

        messages = [
            {"role": row.role, "content": row.content}
            for row in reversed(rows)
        ]
        return messages


async def async_save_message(
    user_id: str,
    conversation_id: str,
    user_input: str,
    ai_answer: str
):
    final_conv_id = conversation_id or str(uuid.uuid4())
    Now = datetime.now()

    async with AsyncSessionLocal() as session:
        user_message = Message(
            user_id=user_id,
            conversation_id=final_conv_id,
            role="user",
            content=user_input,
            created_at=Now
        )
        ai_message = Message(
            user_id=user_id,
            conversation_id=final_conv_id,
            role="assistant",
            content=ai_answer,
            created_at=Now
        )
        session.add_all([user_message, ai_message])
        await session.commit()
        return final_conv_id


async def add_knowledge_to_db(text: str, doc_id: str, source: str = "manual"):

    vs = get_vector_store()
    vs.add_texts(
        texts=[text],
        ids=[doc_id],
        metadatas=[{"source": source}]
    )

    check = vs.get(ids=[doc_id])
    if check["ids"] and len(check["ids"]) > 0:
        logger.info(f"知识存储成功，ID: {doc_id}")
    else:
        logger.error(f"知识存储失败，ID: {doc_id}")


def _extract_keywords(text: str) -> list[str]:
    """使用 jieba 分词提取关键词"""
    import jieba
    return [w for w in jieba.cut(text) if len(w) > 1]


async def retrieve_context(query_text: str):

    vs = get_vector_store()
    keywords = _extract_keywords(query_text)

    docs = vs.similarity_search_with_relevance_scores(query_text, k=10)

    final_docs = [
        (doc, score) for doc, score in docs
        if score >= 0.4 or any(k in doc.page_content for k in keywords)
    ]

    logger.info(f"原始检索到 {len(docs)} 条，过滤后剩余 {len(final_docs)} 条")
    for i, (doc, score) in enumerate(docs):
        status = "采用" if any(doc is d for d, _ in final_docs) else "舍弃"
        logger.info(f"[{i+1}] 分数: {score:.4f} | 状态: {status} | 来源: {doc.metadata.get('source', '未知')} | 内容: {doc.page_content[:20]}...")

    if not final_docs:
        return "未找到足够相关的知识库内容。"

    parts = []
    for doc, _ in final_docs:
        source = doc.metadata.get('source', '未知来源')
        page = doc.metadata.get('page', '')
        source_label = f"{source} 第{page}页" if page else source
        parts.append(f"[来源: {source_label}]\n{doc.page_content}")
    return "\n\n".join(parts)

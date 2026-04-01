import uuid
from sqlalchemy import delete, select, func
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
    Now = datetime.now()

    async with AsyncSessionLocal() as session:
        user_message = Message(
            user_id=user_id,
            conversation_id=conversation_id,
            role="user",
            content=user_input,
            created_at=Now
        )
        ai_message = Message(
            user_id=user_id,
            conversation_id=conversation_id,
            role="assistant",
            content=ai_answer,
            created_at=Now
        )
        session.add_all([user_message, ai_message])
        await session.commit()
        return conversation_id
      


async def save_episodic_fragment(conversation_id: str, fragment: str, metadata: dict):
    """将对话片段写入情节记忆向量集合"""
    vs = get_vector_store("episodic")
    doc_id = str(uuid.uuid4())
    full_metadata = {"conversation_id": conversation_id, **metadata}
    vs.add_texts(
        texts=[fragment],
        ids=[doc_id],
        metadatas=[full_metadata]
    )
    logger.info(f"[情节记忆] 已写入片段，conversation_id={conversation_id}")


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


async def async_get_conversations(user_id: str):
    async with AsyncSessionLocal() as session:
        stmt = (
            select(Message.conversation_id, func.min(Message.created_at).label('created_at'))
            .where(Message.user_id == user_id)
            .group_by(Message.conversation_id)
            .order_by(func.min(Message.created_at).desc())
            .limit(20)
        )
        result = await session.execute(stmt)
        rows = result.all()
        return [
            {"conversation_id": row.conversation_id, "created_at": row.created_at}
            for row in rows
        ]
        
        
async def async_delete_conversation(conversation_id: str):
    async with AsyncSessionLocal() as session:
        stmt = (
            delete(Message)
            .where(Message.conversation_id == conversation_id)
        )
        await session.execute(stmt)
        await session.commit()


# --- 滚动摘要 ---

SUMMARY_EVERY_N_ROUNDS = 5   # 每 N 轮（N 条 user+assistant 对）触发一次摘要更新
SUMMARY_MAX_LENGTH = 500     # 摘要字符数超过此阈值时强制更新


async def async_get_summary(conversation_id: str) -> str:
    """返回会话现有摘要，不存在则返回空字符串"""
    from app.models.conversation_summary import ConversationSummary
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ConversationSummary.summary).where(
                ConversationSummary.conversation_id == conversation_id
            )
        )
        return result.scalar_one_or_none() or ""


async def async_maybe_update_summary(conversation_id: str):
    """检查消息总数，若达到触发条件则用 LLM 更新摘要"""
    from app.models.conversation_summary import ConversationSummary
    from langchain_core.messages import HumanMessage

    async with AsyncSessionLocal() as session:
        # 查当前消息总数
        count_result = await session.execute(
            select(func.count()).where(Message.conversation_id == conversation_id)
        )
        total = count_result.scalar()

        # 取现有摘要

        existing_summary = await async_get_summary(conversation_id)

        # 触发条件：每 N 轮 或 摘要过长
        trigger = SUMMARY_EVERY_N_ROUNDS * 2
        round_trigger = total > 0 and total % trigger == 0
        length_trigger = len(existing_summary) > SUMMARY_MAX_LENGTH
        if not (round_trigger or length_trigger):
            return

        # 取最近 trigger 条消息
        recent_result = await session.execute(
            select(Message.role, Message.content)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.id.desc())
            .limit(trigger)
        )
        recent_rows = list(reversed(recent_result.all()))

    # 在 session 外调用 LLM，避免长时间占用连接
    dialogue = "\n".join(
        f"{r.role}: {r.content}" for r in recent_rows
    )
    prefix = f"当前摘要：\n{existing_summary}\n\n" if existing_summary else ""
    prompt = (
        f"{prefix}"
        f"最新对话记录：\n{dialogue}\n\n"
        "请用简洁的中文将以上内容整合，生成一份覆盖全部要点的更新摘要。只输出摘要本身，不要任何额外说明。"
    )
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    new_summary = response.content.strip()

    # 写回数据库（upsert）
    async with AsyncSessionLocal() as session:
        
            # 重新 attach 到新 session
        res = await session.execute(
                select(ConversationSummary).where(
                    ConversationSummary.conversation_id == conversation_id
                )
            )
        existing_row=res.scalar_one_or_none()
            
        if existing_row:  # 基于数据库查询结果判断
             existing_row.summary = new_summary
             existing_row.message_count = total
        else:
        
            session.add(
                ConversationSummary(
                    conversation_id=conversation_id,
                    summary=new_summary,
                    message_count=total,
                )
            )
        await session.commit()
    logger.info(f"[摘要] 会话 {conversation_id} 摘要已更新（共 {total} 条消息）")


async def retrieve_episodic_memory(query: str, conversation_id: str, k: int = 3) -> str:
    """从情节记忆集合中检索与当前会话相关的历史片段"""
    vs = get_vector_store("episodic")
    docs = vs.similarity_search(query, k=k, filter={"conversation_id": conversation_id})
    if not docs:
        return ""
    return "\n\n".join(doc.page_content for doc in docs)
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
# 1. 创建异步引擎 (注意：如果是 MySQL，URL 应为 mysql+aiomysql://...)
                                                      

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
        # 1. 使用 select 对象构造查询，代替手写字符串 SQL
        stmt = (                                             
            select(Message.role, Message.content)            
            .where(Message.conversation_id == conversation_id) 
            .order_by( Message.id.desc()) 
            .limit(20)                                       
        )                                                    
        
        # 2. 执行异步查询
        result = await session.execute(stmt)                 
        
        # 3. 解析结果
        # 由于我们只 select 了 role 和 content，这里直接遍历返回即可
        rows = result.all()                                  
        
        messages = [                                         
            {"role": row.role, "content": row.content}       
            for row in reversed(rows)                                  
        ]

        return messages  # 历史数据读取完成                                   
 
async def async_save_message(conv_id: str,user_id:str, user_input: str, ai_answer: str):
    async with AsyncSessionLocal() as session:
        final_conv_id = conv_id or str(uuid.uuid4())
        Now=datetime.now()
        user_message=Message( 
        user_id=user_id,       
        conversation_id=final_conv_id,
        role="user",
        content=user_input,
        created_at=Now   
         )
        ai_message=Message(
        user_id=user_id,
        conversation_id=final_conv_id,
        role="assistant",
        content=ai_answer,
        created_at=Now   
        )
        session.add_all([user_message, ai_message])
        await session.commit()
        return final_conv_id  # 消息保存完成
        

async def add_knowledge_to_db(text: str, doc_id: str, source: str = "manual"):

    vs = get_vector_store()

    # 调用 LangChain 的存储方法，附带 metadata
    vs.add_texts(
        texts=[text],
        ids=[doc_id],
        metadatas=[{"source": source}]
    )                                                        

    # 3. 校验逻辑：直接通过单例回查
    check = vs.get(ids=[doc_id])                             
    
    if check["ids"] and len(check["ids"]) > 0:               
        print(f"✅ 存储成功：单例对象已确认 ID {doc_id}")      
    else:                                                    
        print(f"❌ 存储失败：请检查文件夹权限或是否被占用")    

async def extract_keywords(query: str):                      
    # 1. 定义一个专门找“重点”的 Prompt
    prompt = f"""                                            
    请从以下用户问题中提取 1-3 个最核心的搜索关键词（如人名、产品名、属性）。
    只输出关键词，用逗号分隔。
    问题：{query}                                            
    """                                                      
    
    # 2. 调用模型（用最快的模型即可）
    response = await llm.ainvoke(prompt)                     
    keywords = [k.strip() for k in response.content.split(",")]
    return keywords  # 关键词提取完成


async def retrieve_context(query_text: str):                 
    
    vs = get_vector_store()                                  
    keywords = await extract_keywords(query_text)
    
    docs = vs.similarity_search_with_relevance_scores(
        query_text, 
        k=5                                                  
    )            
    final_docs = [
                               
    ]
    
    for doc,score in docs:
        has_keyword = any(k in doc.page_content for k in keywords) 
        
        if has_keyword or score >= 0.4:                      
            final_docs.append(doc)

    # 3. 调试日志
    logger.debug(f"原始检索到 {len(docs)} 条，过滤后剩余 {len(final_docs)} 条")
    for i, (doc, score) in enumerate(docs):
        status = "采用" if doc in final_docs else "舍弃"
        logger.debug(f"[{i+1}] 分数: {score:.4f} | 状态: {status} | 内容: {doc.page_content[:20]}...") 

    if not final_docs:                                    
        return "未找到足够相关的知识库内容。"                    

    # 4. 合并返回给 LLM
    return "\n".join([d.page_content for d in final_docs])


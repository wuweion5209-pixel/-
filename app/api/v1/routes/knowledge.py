"""知识库相关路由"""
from fastapi import APIRouter
from app.utils.logger import logger

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/list")
async def list_knowledge():
    """列出知识库内容"""
    from app.core.vectorstore import get_vector_store
    vs = get_vector_store()
    all_data = vs.get()
    total = len(all_data.get("ids", []))
    logger.info(f"查询知识库，共 {total} 条")
    return {
        "total": total,
        "items": [
            {
                "id": all_data["ids"][i],
                "content": all_data["documents"][i],
                "metadata": all_data["metadatas"][i]
            }
            for i in range(total)
        ]
    }


@router.delete("/delete/{doc_id}")
async def delete_knowledge(doc_id: str):
    """删除单条知识"""
    from app.core.vectorstore import get_vector_store
    vector_store = get_vector_store()
    vector_store.delete(ids=[doc_id])
    logger.info(f"删除知识条目: {doc_id}")
    return {"status": "success"}


@router.delete("/clear")
async def clear_knowledge():
    """清空知识库"""
    from app.core.vectorstore import get_vector_store
    vector_store = get_vector_store()
    ids = vector_store.get().get("ids", [])
    if ids:
        vector_store.delete(ids=ids)
        logger.info(f"知识库已清空，删除 {len(ids)} 条")
        return {"status": "success", "deleted_count": len(ids)}
    logger.info("知识库本已为空，无需清空")
    return {"status": "success", "deleted_count": 0}

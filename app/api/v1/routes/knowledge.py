"""知识库相关路由"""
from fastapi import APIRouter

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/list")
async def list_knowledge():
    """列出知识库内容"""
    from app.core.vectorstore import get_vector_store
    vs = get_vector_store()
    all_data = vs.get()
    return {
        "total": len(all_data.get("ids", [])),
        "items": [
            {
                "id": all_data["ids"][i],
                "content": all_data["documents"][i],
                "metadata": all_data["metadatas"][i]
            }
            for i in range(len(all_data.get("ids", [])))
        ]
    }


@router.delete("/clear")
async def clear_knowledge():
    """清空知识库"""
    from app.core.vectorstore import get_vector_store
    vector_store = get_vector_store()
    ids = vector_store.get().get("ids", [])
    if ids:
        vector_store.delete(ids=ids)
        return {"status": "success", "deleted_count": len(ids)}
    return {"status": "success", "deleted_count": 0}

# AI Agent RAG 项目

## 是什么

基于 FastAPI + LangGraph 的智能问答系统，支持知识库管理和网页抓取。

## 技术栈

- **后端**: FastAPI + LangGraph + LangChain
- **LLM**: 通义千问 (DashScope API)
- **数据库**: MySQL + ChromaDB (向量)
- **检索**: 向量检索 + BM25 混合检索

## 核心功能

1. **Agent 对话**: 基于 LangGraph 工作流，支持工具调用（知识库检索、网页抓取）
2. **知识库**: PDF/Word 文档上传，向量存储，混合检索
3. **多层记忆**: 对话历史 → 摘要 → 情节记忆
4. **网页抓取**: 支持 SPA 页面（Jina Reader API）

## 工作流

```
load → generate → router → [tools → generate] → save
     (加载记忆)  (LLM判断)  (有tool调用?)   (执行工具)
```

## 快速开始

```bash
# 配置 .env
DATABASE_URL=mysql+aiomysql://...
DASHSCOPE_API_KEY=sk-xxx

# 启动
uvicorn app.main:app --reload
# 访问 http://localhost:8000
```

## API

- `POST /chat/new_session` - 对话
- `POST /chat/ragsave` - 上传文档
- `GET /knowledge/list` - 知识库列表

---

*2026-04-07*
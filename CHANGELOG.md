# 更新日志

## v1.0.0 - 2026-04-06

### 项目概述
基于 RAG + Agent + FastAPI 的 AI 对话后端服务

### 技术栈
- **LLM**: 通义千问 (Tongyi Qianwen) via DashScope API
- **框架**: FastAPI + LangChain + LangGraph
- **数据库**: MySQL (异步 aiomysql + SQLAlchemy)
- **向量数据库**: ChromaDB (本地持久化)
- **Embedding**: DashScope text-embedding-v2

### 核心功能
- 聊天会话管理（创建会话、消息历史）
- RAG 知识检索（文本分块、混合检索 BM25+向量、重排序）
- Agent 智能问答（LangGraph 工作流、工具调用）
- 知识管理（添加、列表查询、清空）
- 健康检查

### 模块结构
```
app/
├── api/v1/routes/     # API 路由
├── core/              # 核心配置 (LLM, DB, VectorStore)
├── models/            # ORM 模型
├── schemas/           # Pydantic 模型
├── services/          # 业务逻辑 (Agent, RAG, Chains)
└── utils/             # 工具函数
```

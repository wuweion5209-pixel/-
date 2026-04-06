from typing import Annotated, TypedDict, List
from langgraph.graph import StateGraph, END, add_messages
from app.services.agent_chains_db import async_get_history, async_save_message, retrieve_context, async_get_summary, async_maybe_update_summary, retrieve_episodic_memory, save_episodic_fragment
from app.services.web_fetch import extract_main_content
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.core.config import llm
from app.utils.logger import logger


@tool
async def fetch_webpage(url: str):
    """
    这是一个网页抓取工具。当用户提供了具体的URL地址，想了解该网页的内容时，
    调用此工具获取网页的有效文本内容。

    参数:
        url: 用户提供的网页链接，必须是完整的URL格式（如 https://example.com）
    """
    content = extract_main_content(url)
    return content


#定义向量检索工具
@tool
async def retrieve_konwledge(query:str):
    """                                                      
    这是一个知识库检索工具。当用户问及特定文档、专业知识或背景信息时，
    调用此工具并通过关键词 query 获取相关内容。    
    """                                                                                 
    return await retrieve_context(query)

tools=[retrieve_konwledge, fetch_webpage]
llm_with_tools=llm.bind_tools(tools)


# 1. 定义状态结构：这是节点间传递的数据包
class AgentState(TypedDict):
    input: str       # 用户输入内容
    user_id:str
    chat_history: List[dict]                                 # 从数据库捞出的历史
    summary: str                                             # 历史对话的滚动摘要
    retrieval_count: int                                     # 向量检索的次数
    web_fetch_count: int                                     # 网页抓取的次数
    messages: Annotated[list, add_messages]                  # 用于存放对话和toolmessage
    answer: str                                              # 模型生成的答案
    conversation_id: str  # 对话唯一标识
    tool_used: bool  # 是否实际调用过知识检索工具
    episodic_memories: str  # 情节记忆检索结果

_EPISODIC_TRIGGERS = ["之前", "上次", "记得", "说过"]


# --- 定义异步节点 (Nodes) ---

async def load_history_node(state: AgentState):
    # 调用你之前定义的异步 MySQL 查询函数
    history = await async_get_history(state["conversation_id"])
    summary = await async_get_summary(state["conversation_id"])

    episodic = ""
    if any(kw in state["input"] for kw in _EPISODIC_TRIGGERS):
        episodic = await retrieve_episodic_memory(state["input"], state["conversation_id"])
        if episodic:
            logger.info(f"[情节记忆] 检索到相关历史片段，conversation_id={state['conversation_id']}")

    return {"chat_history": history, "summary": summary, "retrieval_count": 0, "web_fetch_count": 0, "tool_used": False, "episodic_memories": episodic}                         

async def generate_node(state: AgentState):
    # 拼接 Prompt：结合历史、背景和当前问题
    system_prompt = SystemMessage(content="""
你是【智能知识库助手】，一个功能强大的知识问答系统。

## 核心能力
1. 拥有知识库访问权限，可以检索文档、论文、资料等内容
2. 拥有长期记忆能力，可以记住之前的对话内容
3. 可以根据用户需求，提供简短或详细的回答
4. 可以抓取网页内容，当用户给出URL时获取网页有效信息

## 行为准则

### 1. 知识库检索（必须遵守）
- 当用户的问题涉及专业知识、文档内容、特定名词解释、论文内容等，**必须先调用** retrieve_konwledge 工具
- 工具返回的内容是绝对真实的事实，必须以此为准
- 即使你的训练知识与检索结果矛盾，也必须以检索结果为准

### 2. 网页抓取
- 当用户提供了具体的URL，想了解该网页的内容时，**必须调用** fetch_webpage 工具
- 根据抓取到的内容回答用户问题
- 如果抓取失败，明确告知用户

### 3. 严格遵循用户指令（最重要）
- 当用户的问题涉及专业知识、文档内容、特定名词解释、论文内容等，**必须先调用** retrieve_konwledge 工具
- 工具返回的内容是绝对真实的事实，必须以此为准
- 即使你的训练知识与检索结果矛盾，也必须以检索结果为准

### 2. 严格遵循用户指令（最重要）
- 用户要求**多少字**，就必须写多少字，允许 10% 浮动
- 用户要求**详细讲解**，就必须充分展开，每个要点都要解释清楚
- 用户要求**简短回答**，才使用简洁语言
- 用户要求**什么格式**，就必须按什么格式输出（如表格、列表、分点等）
- 用户没有明确要求时，根据问题性质决定详细程度

### 3. 回答质量标准
- **准确性**：所有事实性信息必须来自知识库或明确标注来源
- **完整性**：不遗漏用户问题中的任何要点
- **专业性**：使用专业术语，适当解释概念
- **逻辑性**：回答要有条理，层次清晰

### 4. 禁止事项
- 禁止在回答中添加"根据检索结果"、"来源："等来源标注
- 禁止编造知识库中没有的信息
- 禁止忽略用户的具体要求（如字数、详细程度）
- 禁止用"抱歉，我找不到"简单打发用户，如果找不到要说明"在知识库中未找到相关内容"

## 输出格式要求
- 直接给出答案，不需要解释你将调用工具
- 如果调用了工具，直接基于结果回答
- 如果知识库没有相关信息，明确告知用户
""")
    hist_messages = [HumanMessage(content=m['content']) if m['role']=='user' else AIMessage(content=m['content']) for m in state["chat_history"]]

    summary = state.get("summary", "")
    episodic = state.get("episodic_memories", "")

    context_messages = [system_prompt]
    if summary:
        context_messages.append(SystemMessage(content=f"以下是本次对话的历史摘要（供参考）：\n{summary}"))
    if episodic:
        context_messages.append(SystemMessage(content=f"以下是从历史对话中检索到的相关情节记忆（供参考）：\n{episodic}"))
    context_messages += hist_messages

    # 在用户输入后追加强制指令
    user_input_with_instruction = f"""{state['input']}

【回答要求】
- 严格遵循用户的字数要求
- 用户要求详细讲解时，必须充分展开
- 不得添加任何来源标注
- 如需检索知识库，请调用工具"""

    current_input = HumanMessage(content=user_input_with_instruction)

    logger.info(f"[Agent] 用户输入: {state['input']}")
    logger.info(f"[Agent] 向量检索次数: {state.get('retrieval_count', 0)}, 网页抓取次数: {state.get('web_fetch_count', 0)}")

    response = await llm_with_tools.ainvoke(context_messages + [current_input] + state["messages"])

    # 分别统计两种工具的调用次数
    curr_retrieval = state.get("retrieval_count", 0)
    curr_web_fetch = state.get("web_fetch_count", 0)
    tool_used = state.get("tool_used", False)

    if response.tool_calls:
        for tc in response.tool_calls:
            if tc.name == "retrieve_konwledge":
                curr_retrieval += 1
                tool_used = True
                logger.info(f"[Agent] 触发向量检索工具: {tc.name}")
            elif tc.name == "fetch_webpage":
                curr_web_fetch += 1
                logger.info(f"[Agent] 触发网页抓取工具: {tc.name}")

    logger.info(f"[Agent] LLM回复: {response.content[:100]}...")

    return {"messages": [response], "answer": response.content, "retrieval_count": curr_retrieval, "web_fetch_count": curr_web_fetch, "tool_used": tool_used}


async def save_node(state: AgentState):
    answer = state["answer"]

    real_id = await async_save_message(
        state.get("user_id"),
        state.get("conversation_id"),
        state["input"],
        answer
    )
    await async_maybe_update_summary(real_id)

    # 每轮都保存对话片段到情节记忆向量库
    dialogue_fragment = f"user: {state['input']}\nassistant: {answer}"
    await save_episodic_fragment(real_id, dialogue_fragment, {})

    return {"conversation_id": real_id, "answer": answer}  # 记忆持久化完成                                           

def router_node(state:AgentState):
    last_messages = state["messages"][-1]
    retrieval_count = state.get("retrieval_count", 0)

    if last_messages.tool_calls:
        # 只限制向量检索次数，网页抓取不限制
        if retrieval_count >= 3:
            logger.warning("已到达最大向量检索次数，强制结束")
            return "save"
        return "tools"
    return "save"

# --- 组装 LangGraph 工作流

workflow=StateGraph(AgentState)
#为workflow添加功能节点

workflow.add_node("load",load_history_node)
workflow.add_node("generate",generate_node)
workflow.add_node("tools",ToolNode(tools))
workflow.add_node("save",save_node)
#为workflow规划路径，包含agent判断循环

workflow.set_entry_point("load")
workflow.add_edge("load","generate")
workflow.add_conditional_edges("generate",
    router_node,{
        "tools":"tools",
        "save":"save"
    }
    )
workflow.add_edge("tools","generate")
workflow.add_edge("save",END)

# 编译成最终可用的 agent_app
agent_app = workflow.compile()


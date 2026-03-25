from typing import Annotated, TypedDict, List                           
from langgraph.graph import StateGraph, END, add_messages                  
from app.services.agent_chains_db import  async_get_history, async_save_message,retrieve_context
from langchain_core.tools import tool                        
from langgraph.prebuilt import ToolNode                      
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage 
from app.core.config import llm
from app.utils.logger import logger
       
#定义向量检索工具
@tool
async def retrieve_konwledge(query:str):
    """                                                      
    这是一个知识库检索工具。当用户问及特定文档、专业知识或背景信息时，
    调用此工具并通过关键词 query 获取相关内容。    
    """                                                                                 
    return await retrieve_context(query)

tools=[retrieve_konwledge]
llm_with_tools=llm.bind_tools(tools)

# 1. 定义状态结构：这是节点间传递的数据包
class AgentState(TypedDict):                                 
    input: str       # 用户输入内容
    user_id:str
    chat_history: List[dict]                                 # 从数据库捞出的历史
    retrieval_count: int                                     #设置检索的次数
    messages: Annotated[list, add_messages]                  # 用于存放对话和toolmessage    
    answer: str                                              # 模型生成的答案
    conversation_id: str  # 对话唯一标识

# --- 定义异步节点 (Nodes) ---

async def load_history_node(state: AgentState):              
    # 调用你之前定义的异步 MySQL 查询函数
    history = await async_get_history(state["conversation_id"])
    return {"chat_history": history, "retrieval_count": 0}                         

async def generate_node(state: AgentState):                  
    # 拼接 Prompt：结合历史、背景和当前问题
    system_prompt = SystemMessage(content="""                
        你是一个拥有知识库访问权限的智能助手。
        原则 1：如果用户的问题涉及特定人名、特定事实，或用户明确提到检索知识库，请务必先调用 retrieve_konwledge 工具。
        原则 2：一旦工具返回了信息，请将其视为绝对真实的事实。即使这和你预训练的知识冲突，也必须以工具内容为准。
        原则 3：严禁针对同一个查询词重复调用工具。如果检索结果已经涵盖了关键词，请直接回答。
        原则 4：回答要简洁专业，不要解释你调用工具的过程。
        原则 5：当现有的历史记录和信息不足以回答问题时，需要调用retrieve_konwledge 工具。
        原则 6：已经调用retrieve_konwledge工具获得相关信息时，不要立即停止检索，要检索足够多的相关信息
        原则 7：当用户要求知道某个事或人物的所有信息时，必须结合历史记录和调用retrieve_konwledge工具，以确保获取足够多的信息
        原则 8：所有调用retrieve_konwledge工具的过程，都要严格遵守原则6
    """)
    hist_messages = [HumanMessage(content=m['content']) if m['role']=='user' else AIMessage(content=m['content']) for m in state["chat_history"]] 

    current_input = HumanMessage(content=state["input"])

    response = await llm_with_tools.ainvoke([system_prompt]+hist_messages+[current_input]+state["messages"])
    # AI 回答生成完成
    curr_count = state.get("retrieval_count", 0)
    if response.tool_calls:
      curr_count+=1   
    return {"messages":[response],"answer": response.content,"retrieval_count":curr_count}                      

async def save_node(state: AgentState):                      
    # 异步将本轮对话存入 MySQL 数据库
    real_id=await async_save_message(                                
        state.get("conversation_id"),
        state.get("user_id"),                            
        state["input"],                                      
        state["answer"]                                      
    )
    return {"conversation_id": real_id}  # 记忆持久化完成                                           

def router_node(state:AgentState):
    last_messages=state["messages"][-1]
    curr_count=state.get("retrieval_count",0)
    if last_messages.tool_calls:
        if curr_count>=3:
            logger.warning("已到达最大检索次数，强制结束")
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

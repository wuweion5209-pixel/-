"""
AI Agent RAG 项目测试用例
"""
import asyncio
import time
import sys
import os

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.agent_service import agent_app
from app.services.agent_chains_db import retrieve_context
from app.services.web_fetch import extract_main_content
from app.core.config import settings


# ======== 测试配置 ========
TEST_CONVERSATION_ID = "test-auto-001"


async def run_test(name, func):
    """运行单个测试"""
    print(f"\n{'='*50}")
    print(f"测试: {name}")
    print('='*50)
    try:
        start = time.time()
        result = await func()
        elapsed = time.time() - start
        print(f"✓ 耗时: {elapsed:.2f}s")
        return {"success": True, "result": result, "elapsed": elapsed}
    except Exception as e:
        print(f"✗ 失败: {e}")
        return {"success": False, "error": str(e), "elapsed": 0}


# ======== 1. 检索质量测试 ========
async def test_retrieval():
    """测试知识库检索是否返回相关内容"""
    queries = [
        "Python",
        "机器学习",
        "深度学习",
        "什么是神经网络",
    ]

    results = []
    for query in queries:
        print(f"\nQuery: {query}")
        docs = await retrieve_context(query)
        print(f"Result length: {len(docs)} chars")

        # 检查是否有相关内容
        has_content = len(docs) > 20 and "未找到" not in docs
        print(f"Has content: {has_content}")

        if has_content:
            print(f"Preview: {docs[:150]}...")

        results.append({"query": query, "length": len(docs), "has_content": has_content})

    # 统计
    total = len(results)
    has_content = sum(1 for r in results if r["has_content"])
    print(f"\n--- Retrieval Summary ---")
    print(f"Total queries: {total}")
    print(f"Has content: {has_content}/{total}")

    return {"total": total, "has_content": has_content, "details": results}


# ======== 2. 工具调用逻辑测试 ========
async def test_tool_call():
    """测试 LLM 是否正确判断需要调用工具"""

    test_cases = [
        {
            "input": "什么是Python?",
            "expected_tool": "retrieve_konwledge",
            "desc": "专业知识问题，应该调用知识库检索"
        },
        {
            "input": "请帮我查一下 https://www.baidu.com 的内容",
            "expected_tool": "fetch_webpage",
            "desc": "提供URL，应该调用网页抓取"
        },
        {
            "input": "今天天气怎么样?",
            "expected_tool": None,
            "desc": "闲聊问题，不需要工具"
        },
    ]

    results = []
    for case in test_cases:
        print(f"\n输入: {case['input']}")
        print(f"预期: {case['expected_tool']}")

        state = {
            "input": case["input"],
            "user_id": settings.DEFAULT_USER_ID,
            "chat_history": [],
            "summary": "",
            "retrieval_count": 0,
            "web_fetch_count": 0,
            "messages": [],
            "answer": "",
            "conversation_id": TEST_CONVERSATION_ID,
            "tool_used": False,
            "episodic_memories": ""
        }

        result = await agent_app.ainvoke(state)

        # 检查是否调用了工具
        retrieval_count = result.get("retrieval_count", 0)
        web_fetch_count = result.get("web_fetch_count", 0)

        actual_tool = None
        if retrieval_count > 0:
            actual_tool = "retrieve_konwledge"
        elif web_fetch_count > 0:
            actual_tool = "fetch_webpage"

        is_correct = actual_tool == case["expected_tool"]
        print(f"Expected: {case['expected_tool']} | Actual: {actual_tool} | {'OK' if is_correct else 'FAIL'}")

        results.append({
            "input": case["input"],
            "expected": case["expected_tool"],
            "actual": actual_tool,
            "correct": is_correct
        })

    # 统计
    correct = sum(1 for r in results if r["correct"])
    print(f"\n--- Tool Call Summary ---")
    print(f"Correct: {correct}/{len(results)}")

    return {"correct": correct, "total": len(results), "details": results}


# ======== 3. 网页抓取测试 ========
async def test_web_fetch():
    """测试网页抓取功能"""

    test_urls = [
        {
            "url": "https://www.baidu.com",
            "expected_type": "text",
            "desc": "百度首页"
        },
        {
            "url": "https://www.coze.com",
            "expected_type": "text",
            "desc": "Coze (SPA)"
        },
    ]

    results = []
    for test in test_urls:
        print(f"\n抓取: {test['desc']}")
        print(f"URL: {test['url']}")

        start = time.time()
        content = extract_main_content(test["url"])
        elapsed = time.time() - start

        # 判断结果
        is_success = "抓取失败" not in content and "抓取超时" not in content
        length = len(content)

        print(f"长度: {length} 字符")
        print(f"耗时: {elapsed:.2f}s")
        print(f"成功: {is_success}")

        if is_success:
            print(f"内容预览: {content[:100]}...")

        results.append({
            "url": test["url"],
            "desc": test["desc"],
            "success": is_success,
            "length": length,
            "elapsed": elapsed
        })

    # 统计
    success = sum(1 for r in results if r["success"])
    print(f"\n--- Web Fetch Summary ---")
    print(f"Success: {success}/{len(results)}")

    return {"success": success, "total": len(results), "details": results}


# ======== 4. 性能测试 ========
async def test_performance():
    """测试响应时间和资源消耗"""

    # 测试1: 简单对话响应时间
    print("\n--- 测试1: 简单对话 ---")
    start = time.time()
    state = {
        "input": "你好",
        "user_id": settings.DEFAULT_USER_ID,
        "chat_history": [],
        "summary": "",
        "retrieval_count": 0,
        "web_fetch_count": 0,
        "messages": [],
        "answer": "",
        "conversation_id": TEST_CONVERSATION_ID + "-perf1",
        "tool_used": False,
        "episodic_memories": ""
    }
    await agent_app.ainvoke(state)
    simple_time = time.time() - start
    print(f"简单对话耗时: {simple_time:.2f}s")

    # 测试2: 带检索的对话
    print("\n--- 测试2: 带知识库检索 ---")
    start = time.time()
    state = {
        "input": "什么是Python?",
        "user_id": settings.DEFAULT_USER_ID,
        "chat_history": [],
        "summary": "",
        "retrieval_count": 0,
        "web_fetch_count": 0,
        "messages": [],
        "answer": "",
        "conversation_id": TEST_CONVERSATION_ID + "-perf2",
        "tool_used": False,
        "episodic_memories": ""
    }
    result = await agent_app.ainvoke(state)
    retrieval_time = time.time() - start
    retrieval_count = result.get("retrieval_count", 0)
    print(f"检索对话耗时: {retrieval_time:.2f}s")
    print(f"检索次数: {retrieval_count}")

    # 测试3: 检索本身的时间
    print("\n--- Test 3: Retrieval Performance ---")
    start = time.time()
    docs = await retrieve_context("Python")
    retrieval_only_time = time.time() - start
    print(f"Retrieval time: {retrieval_only_time:.3f}s")
    print(f"Result length: {len(docs)}")

    return {
        "simple_conversation": simple_time,
        "retrieval_conversation": retrieval_time,
        "retrieval_count": retrieval_count,
        "retrieval_only": retrieval_only_time
    }


# ======== 主函数 ========
async def main():
    print("="*60)
    print("AI Agent RAG Project Test Suite")
    print("="*60)

    results = {}

    # 1. 检索质量
    results["retrieval"] = await run_test("1. Retrieval Quality Test", test_retrieval)

    # 2. 工具调用逻辑
    results["tool_call"] = await run_test("2. Tool Call Logic Test", test_tool_call)

    # 3. 网页抓取
    results["web_fetch"] = await run_test("3. Web Fetch Test", test_web_fetch)

    # 4. 性能
    results["performance"] = await run_test("4. Performance Test", test_performance)

    # 汇总
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)

    if results.get("retrieval", {}).get("result"):
        r = results["retrieval"]["result"]
        print(f"Retrieval: {r['has_content']}/{r['total']} has content")

    if results.get("tool_call", {}).get("result"):
        t = results["tool_call"]["result"]
        print(f"Tool Call: {t['correct']}/{t['total']} correct")

    if results.get("web_fetch", {}).get("result"):
        w = results["web_fetch"]["result"]
        print(f"Web Fetch: {w['success']}/{w['total']} success")

    if results.get("performance", {}).get("result"):
        perf = results['performance']['result']
        print(f"\nPerformance:")
        print(f"  Simple conversation: {perf['simple_conversation']:.2f}s")
        print(f"  Retrieval conversation: {perf['retrieval_conversation']:.2f}s")
        print(f"  Retrieval only: {perf['retrieval_only']*1000:.0f}ms")


if __name__ == "__main__":
    # 设置 UTF-8 输出
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    asyncio.run(main())
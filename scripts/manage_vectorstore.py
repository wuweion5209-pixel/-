#!/usr/bin/env python3
"""向量数据库管理脚本"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.vectorstore import get_vector_store


def show_all():
    """显示向量库所有内容"""
    vs = get_vector_store()
    all_data = vs.get()

    print("--- 向量库内容扫描报告 ---")
    print(f"总计条数：{len(all_data.get('ids', []))}")

    for i in range(len(all_data.get('ids', []))):
        doc_id = all_data["ids"][i]
        content = all_data["documents"][i]
        metadata = all_data["metadatas"][i]

        print(f"[{i + 1}] ID: {doc_id}")
        print(f"    内容：{content}")
        print(f"    元数据：{metadata}")
        print("-" * 30)


def clear_vector_store():
    """清空向量数据库"""
    vector_store = get_vector_store()
    ids = vector_store.get().get("ids", [])

    if ids:
        vector_store.delete(ids=ids)
        print(f"✅ 已成功清空 {len(ids)} 条数据")
    else:
        print("ℹ️  向量库为空")


def main():
    """主函数"""
    print("=== 向量数据库管理工具 ===")
    print("1. 查看所有数据")
    print("2. 清空数据")

    key = input("请输入需要进行的操作：")

    if key == "1":
        show_all()
    elif key == "2":
        confirm = input("⚠️  确认清空所有数据？(y/n): ")
        if confirm.lower() == "y":
            clear_vector_store()
        else:
            print("已取消操作")
    else:
        print("输入无效")


if __name__ == "__main__":
    main()

"""
测试语义搜索功能
"""
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from vector_search import search

# 测试查询
test_queries = [
    "什么是多 Agent 协同？",
    "Protégé 工具的使用方法",
    "如何构建知识图谱？",
    "OpenClaw 的团队角色有哪些？",
]

print("="*60)
print("语义搜索测试")
print("="*60)

for query in test_queries:
    print(f"\n查询: {query}")
    print("-"*60)

    results = search(query, n_results=3)

    for i, (doc, dist, meta) in enumerate(zip(
        results['documents'][0],
        results['distances'][0],
        results['metadatas'][0]
    )):
        print(f"\n【结果 {i+1}】(距离: {dist:.4f})")
        print(f"来源: {meta['source']}")
        # 显示部分内容（前200字）
        print(f"内容: {doc[:200]}...")
        print()

print("="*60)
print("测试完成!")
print("="*60)
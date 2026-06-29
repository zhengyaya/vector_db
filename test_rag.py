"""
测试 RAG 问答
"""
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from rag_chat import rag_query

# 测试问题
test_queries = [
    "什么是多 Agent 协同？",
    "Protégé 工具如何使用？",
]

print("="*60)
print("RAG 问答测试")
print("="*60)

for query in test_queries:
    print(f"\n问题: {query}")
    print("-"*60)

    result = rag_query(query)

    print("回答:")
    print(result['answer'])
    print()
    print(f"参考文档数: {len(result['sources'])}")
    print(f"相似度距离: {result['distances']}")
    print("="*60)

print("\n测试完成!")
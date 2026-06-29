"""
测试多集合 vs 单集合效果对比
"""
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from rag_multi import search_in_collection, COLLECTIONS

# 测试问题
test_queries = [
    ("什么是多 Agent 协同？", "multi_agent"),
    ("Protégé 工具如何使用？", "knowledge_tools"),
    ("什么是本体建模？", "knowledge_tools"),
]

print("="*60)
print("多集合检索效果对比测试")
print("="*60)

for query, expected_coll in test_queries:
    print(f"\n问题: {query}")
    print(f"预期集合: {expected_coll}")
    print("-"*60)

    # 在所有集合中搜索
    best_dist = float('inf')
    best_coll = None

    for coll_id in COLLECTIONS.keys():
        results = search_in_collection(query, coll_id, n_results=2)
        if results['distances'] and results['distances'][0]:
            min_dist = min(results['distances'][0])
            print(f"  {coll_id}: 最小距离 {min_dist:.4f}")

            if min_dist < best_dist:
                best_dist = min_dist
                best_coll = coll_id

    print(f"\n最佳匹配: {best_coll} (距离: {best_dist:.4f})")

    if best_coll == expected_coll:
        print("  ✅ 正确匹配到预期集合")
    else:
        print(f"  ⚠️ 实际匹配到 {best_coll}，预期 {expected_coll}")

print("\n" + "="*60)
print("测试完成!")
print("="*60)
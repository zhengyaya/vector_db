# test_compare_v3.py - 多集合效果对比测试
import sys
import io
import requests
import chromadb

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import rag_config as config

COLLECTIONS = {
    "multi_agent": {"name": "多Agent协同"},
    "knowledge_tools": {"name": "知识工程工具"}
}

CHROMA_PATH = r"D:\Python\vector_db\chroma_data"

def search_auto(query):
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    best_dist = float('inf')
    best_coll = None
    best_results = None

    for coll_id in COLLECTIONS.keys():
        collection = client.get_collection(name=coll_id)
        results = collection.query(
            query_texts=[query],
            n_results=2,
            include=['documents', 'metadatas', 'distances']
        )
        if results['distances'][0]:
            min_dist = min(results['distances'][0])
            print("  {}: {}".format(coll_id, min_dist))
            if min_dist < best_dist:
                best_dist = min_dist
                best_coll = coll_id
                best_results = results

    return best_results, best_coll, best_dist

def call_llm(prompt):
    url = config.MINIMAX_BASE_URL + "/text/chatcompletion_v2"
    headers = {"Authorization": "Bearer " + config.MINIMAX_API_KEY, "Content-Type": "application/json"}
    payload = {"model": config.MINIMAX_MODEL, "messages": [{"role": "system", "content": "你是专业助手"}, {"role": "user", "content": prompt}]}
    response = requests.post(url, headers=headers, json=payload, timeout=60)
    result = response.json()
    if result.get('choices'):
        return result['choices'][0]['message']['content']
    return str(result)

# 测试问题（之前效果不好的）
test_queries = [
    ("什么是知识工程", "knowledge_tools"),
    ("什么是本体建模", "knowledge_tools"),
    ("什么是知识抽取", "knowledge_tools"),
]

print("="*60)
print("多集合效果对比测试")
print("="*60)

for query, expected in test_queries:
    print("\n问题: {}".format(query))
    print("-"*60)

    results, coll, dist = search_auto(query)

    print("\n最佳集合: {} (距离: {:.4f})".format(coll, dist))

    # 对比旧数据
    old_dist = {"什么是知识工程": 1.29, "什么是本体建模": 1.08, "什么是知识抽取": 1.29}
    improvement = old_dist.get(query, 0) - dist
    if improvement > 0:
        print("提升: {:.4f} ({:.1f}%)".format(improvement, improvement/old_dist.get(query,1)*100))
    else:
        print("下降: {:.4f}".format(-improvement))

print("\n" + "="*60)
print("测试完成")
print("="*60)
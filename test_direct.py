# test_direct.py
import sys
import io
import requests
import chromadb
import json
import rag_config as config

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 定义集合
COLLECTIONS = {
    "multi_agent": {"name": "多Agent协同"},
    "knowledge_tools": {"name": "知识工程工具"}
}

CHROMA_PATH = r"D:\Python\vector_db\chroma_data"

def search_auto(query):
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    best_dist = float('inf')
    best_coll = None

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

    return best_results, best_coll

def call_llm(prompt):
    url = config.MINIMAX_BASE_URL + "/text/chatcompletion_v2"
    headers = {"Authorization": "Bearer " + config.MINIMAX_API_KEY, "Content-Type": "application/json"}
    payload = {"model": config.MINIMAX_MODEL, "messages": [{"role": "system", "content": "你是专业助手"}, {"role": "user", "content": prompt}]}
    response = requests.post(url, headers=headers, json=payload, timeout=60)
    result = response.json()
    if result.get('choices'):
        return result['choices'][0]['message']['content']
    return str(result)

query = "什么是多 Agent 协同？"
print("问题: " + query)
print("-" * 60)

results, collection = search_auto(query)
docs = results['documents'][0]
dists = results['distances'][0]

print("\n集合:", collection)
print("距离:", dists[0])

context = "\n\n".join([d[:200] for d in docs])
prompt = "问题：{}\n参考文档：{}\n回答：".format(query, context)
answer = call_llm(prompt)

print("\n回答:", answer[:300])
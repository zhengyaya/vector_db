"""
OpenGauss 向量搜索测试 - 显示详细中间数据
测试题目：多Agent协同的作用
"""

import psycopg2
import requests
import og_config as config


def get_connection():
    return psycopg2.connect(**config.OG_CONFIG)


def get_embedding(text):
    """调用 MiniMax API 获取文本 embedding"""
    url = f"{config.MINIMAX_BASE_URL}/embeddings"
    headers = {
        "Authorization": f"Bearer {config.MINIMAX_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": config.EMBEDDING_MODEL,
        "type": "query",
        "texts": [text]
    }

    response = requests.post(url, headers=headers, json=payload, timeout=30)
    result = response.json()

    if 'vectors' in result and result['vectors'] and len(result['vectors']) > 0:
        return result['vectors'][0]
    else:
        print(f"Embedding API 返回错误: {result}")
        return None


def cosine_similarity(vec1, vec2):
    """计算余弦相似度"""
    if not vec1 or not vec2:
        return 0.0

    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = sum(a * a for a in vec1) ** 0.5
    norm2 = sum(b * b for b in vec2) ** 0.5

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return dot / (norm1 * norm2)


def search_with_details(query_text, n_results=10):
    """向量语义搜索 - 详细版"""
    print("=" * 60)
    print("步骤1: 获取查询的Embedding")
    print("=" * 60)
    print(f"查询内容: {query_text}")
    print()

    query_embedding = get_embedding(query_text)

    if not query_embedding:
        print("获取Embedding失败!")
        return []

    print(f"Embedding维度: {len(query_embedding)}")
    print(f"Embedding前10个值: {query_embedding[:10]}")
    print()

    # 获取所有向量
    print("=" * 60)
    print("步骤2: 获取数据库中的所有向量")
    print("=" * 60)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, content, source, vector FROM vector_docs")
    all_docs = cur.fetchall()
    conn.close()

    print(f"数据库中共有 {len(all_docs)} 个文档")
    print()

    # 计算每个文档的相似度
    print("=" * 60)
    print("步骤3: 计算每个文档与查询的余弦相似度")
    print("=" * 60)

    similarities = []
    for doc_id, content, source, vector in all_docs:
        if vector:
            sim = cosine_similarity(query_embedding, vector)
            similarities.append({
                'id': doc_id,
                'content': content[:100] + '...',
                'source': source,
                'similarity': sim,
                'vector': vector
            })

    # 按相似度排序
    print("=" * 60)
    print("步骤4: 按相似度排序")
    print("=" * 60)

    similarities.sort(key=lambda x: x['similarity'], reverse=True)

    print(f"\n{'排名':<4} {'相似度':<10} {'文档ID':<30} {'来源':<20}")
    print("-" * 70)
    for i, doc in enumerate(similarities[:n_results], 1):
        print(f"{i:<4} {doc['similarity']:.4f}    {doc['id']:<30} {doc['source']:<20}")

    print()

    # 返回 top n
    return similarities[:n_results]


if __name__ == "__main__":
    # 测试题目：多Agent协同的作用
    query = "多Agent协同的作用"

    print("\n" + "=" * 60)
    print("向量搜索测试 - 详细中间数据")
    print("=" * 60)
    print(f"测试题目: {query}")
    print()

    results = search_with_details(query, n_results=10)

    print("=" * 60)
    print("最终结果 (Top 3)")
    print("=" * 60)
    for i, doc in enumerate(results[:3], 1):
        print(f"\n--- Top {i} ---")
        print(f"相似度: {doc['similarity']:.4f}")
        print(f"来源: {doc['source']}")
        print(f"内容预览: {doc['content'][:200]}")
"""
OpenGauss 向量搜索测试 - 搜索功能
"""

import psycopg2

OG_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'postgres',
    'user': 'gaussdb',
    'password': 'GaussDB@123'
}

def get_connection():
    return psycopg2.connect(**OG_CONFIG)


def search(query_text, n_results=3):
    """搜索（文本匹配）"""
    conn = get_connection()
    cur = conn.cursor()

    # 使用 LIKE 进行搜索
    cur.execute("""
        SELECT id, content, source
        FROM vector_docs
        WHERE content LIKE %s
        LIMIT %s
    """, (f'%{query_text}%', n_results))

    results = cur.fetchall()

    cur.close()
    conn.close()

    return results


if __name__ == "__main__":
    # 测试搜索
    query = "Agent"

    print(f"\n搜索关键词: {query}")
    print("="*50)

    results = search(query, n_results=3)

    print(f"找到 {len(results)} 个结果:\n")
    for i, (id, content, source) in enumerate(results, 1):
        print(f"--- 结果 {i} ---")
        print(f"来源: {source}")
        print(f"内容: {content[:200]}...")
        print()
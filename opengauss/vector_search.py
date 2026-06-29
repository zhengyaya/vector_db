"""
阶段1：个人文档语义搜索工具 (OpenGauss版本)
功能：读取文档、向量化入库、语义搜索
"""

import psycopg2
import requests
import json
from pathlib import Path
import og_config as config


def get_connection():
    """获取数据库连接"""
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


def init_database():
    """初始化 OpenGauss 数据库表"""
    conn = get_connection()
    cur = conn.cursor()

    # 创建向量表 (使用 float4 数组)
    cur.execute("""
        DROP TABLE IF EXISTS vector_docs;
    """)

    cur.execute("""
        CREATE TABLE vector_docs (
            id VARCHAR(255) PRIMARY KEY,
            content TEXT NOT NULL,
            source VARCHAR(255),
            vector FLOAT4[],
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 创建 GIN 索引用于全文搜索
    cur.execute("""
        CREATE INDEX idx_vector_docs_content ON vector_docs USING gin(to_tsvector('simple', content));
    """)

    conn.commit()
    print("表创建成功: vector_docs")
    cur.close()
    conn.close()


def read_documents():
    """读取文档目录下的所有文件"""
    docs = []
    doc_path = Path(config.DOCS_PATH)

    for file in doc_path.iterdir():
        if file.suffix in ['.md', '.txt', '.docx']:
            try:
                if file.suffix == '.md' or file.suffix == '.txt':
                    content = file.read_text(encoding='utf-8')
                elif file.suffix == '.docx':
                    try:
                        import docx
                        doc = docx.Document(file)
                        content = '\n'.join([para.text for para in doc.paragraphs])
                    except:
                        print(f"跳过 docx 文件: {file.name}")
                        continue

                docs.append({
                    'id': file.stem,
                    'content': content,
                    'source': file.name,
                    'type': file.suffix
                })
                print(f"读取: {file.name} ({len(content)} 字符)")
            except Exception as e:
                print(f"读取失败 {file.name}: {e}")

    return docs


def chunk_text(text, chunk_size=500):
    """将文本切分成小块"""
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = []
    current_size = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if current_size + len(para) > chunk_size and current_chunk:
            chunks.append('\n\n'.join(current_chunk))
            current_chunk = []
            current_size = 0

        current_chunk.append(para)
        current_size += len(para)

    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))

    return chunks


def import_documents():
    """导入文档到 OpenGauss 向量数据库"""
    print("\n" + "="*50)
    print("步骤1: 读取文档")
    print("="*50)
    docs = read_documents()

    print("\n" + "="*50)
    print("步骤2: 文档切分")
    print("="*50)
    all_chunks = []
    for doc in docs:
        chunks = chunk_text(doc['content'], chunk_size=500)
        for i, chunk in enumerate(chunks):
            all_chunks.append({
                'id': f"{doc['id']}_{i}",
                'content': chunk,
                'source': doc['source']
            })
        print(f"{doc['source']}: 切分成 {len(chunks)} 个块")

    print(f"\n总计: {len(all_chunks)} 个文本块")

    print("\n" + "="*50)
    print("步骤3: 向量化入库 OpenGauss")
    print("="*50)

    # 初始化表
    init_database()

    conn = get_connection()
    cur = conn.cursor()

    # 批量处理
    for i, chunk in enumerate(all_chunks):
        # 获取 embedding
        print(f"处理 {i+1}/{len(all_chunks)}: {chunk['id']}")
        embedding = get_embedding(chunk['content'])

        if embedding:
            # 存储到数据库 (使用 float4 数组)
            cur.execute(
                "INSERT INTO vector_docs (id, content, source, vector) VALUES (%s, %s, %s, %s)",
                (chunk['id'], chunk['content'], chunk['source'], embedding)
            )

    conn.commit()
    print(f"已导入 {len(all_chunks)} 个文档块")

    cur.close()
    conn.close()

    return len(all_chunks)


def search(query_text, n_results=3):
    """向量语义搜索"""
    # 获取查询的 embedding
    query_embedding = get_embedding(query_text)

    if not query_embedding:
        return []

    conn = get_connection()
    cur = conn.cursor()

    # 使用 Python 计算余弦相似度
    # 获取所有向量，计算相似度并排序
    cur.execute("SELECT id, content, source, vector FROM vector_docs")
    all_docs = cur.fetchall()

    if not all_docs:
        return []

    # 计算相似度
    similarities = []
    for doc_id, content, source, vector in all_docs:
        if vector:
            # 余弦相似度
            sim = cosine_similarity(query_embedding, vector)
            similarities.append((doc_id, content, source, sim))

    # 排序
    similarities.sort(key=lambda x: x[3], reverse=True)

    cur.close()
    conn.close()

    # 返回 top n
    return similarities[:n_results]


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


if __name__ == "__main__":
    # 导入文档
    count = import_documents()

    print("\n" + "="*50)
    print("文档导入完成!")
    print("="*50)
    print(f"文档数量: {count}")
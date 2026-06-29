"""
OpenGauss 向量搜索测试
功能：使用 OpenGauss 数据库进行向量搜索
"""

import psycopg2
import numpy as np
from pathlib import Path

# OpenGauss 连接配置
OG_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'postgres',
    'user': 'gaussdb',
    'password': 'GaussDB@123'
}

# 文档目录
DOCS_PATH = r"\\wsl.localhost\Ubuntu\home\eros\.openclaw\workspace-content-ma\docs"

# 集合名称
COLLECTION_NAME = "my_docs"


def get_connection():
    """获取数据库连接"""
    return psycopg2.connect(**OG_CONFIG)


def init_table():
    """初始化向量表"""
    conn = get_connection()
    cur = conn.cursor()

    # 创建向量表（使用 text 类型存储文本，jsonb 存储向量）
    cur.execute("""
        DROP TABLE IF EXISTS vector_docs;
    """)

    cur.execute("""
        CREATE TABLE vector_docs (
            id VARCHAR(255) PRIMARY KEY,
            content TEXT NOT NULL,
            source VARCHAR(255),
            vector BLOB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 创建向量索引（如果需要）
    # 注意：OpenGauss 需要启用向量搜索插件

    conn.commit()
    print("表创建成功: vector_docs")
    cur.close()
    conn.close()


def read_documents():
    """读取文档目录下的所有文件"""
    docs = []
    doc_path = Path(DOCS_PATH)

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
    """导入文档到 OpenGauss"""
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
    print("步骤3: 数据入库 OpenGauss")
    print("="*50)

    conn = get_connection()
    cur = conn.cursor()

    # 清空表
    cur.execute("DELETE FROM vector_docs;")

    # 批量插入
    for chunk in all_chunks:
        cur.execute(
            "INSERT INTO vector_docs (id, content, source) VALUES (%s, %s, %s)",
            (chunk['id'], chunk['content'], chunk['source'])
        )

    conn.commit()
    print(f"已导入 {len(all_chunks)} 个文档块")

    cur.close()
    conn.close()

    return len(all_chunks)


def search(query_text, n_results=3):
    """搜索（文本匹配）"""
    conn = get_connection()
    cur = conn.cursor()

    # 使用 LIKE 进行简单搜索
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
    # 初始化表
    init_table()

    # 导入文档
    count = import_documents()

    print("\n" + "="*50)
    print("文档导入完成!")
    print("="*50)
    print(f"文档数量: {count}")
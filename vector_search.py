"""
阶段1：个人文档语义搜索工具
功能：读取文档、向量化入库、语义搜索
"""

import chromadb
import os
from pathlib import Path

# 文档目录
DOCS_PATH = r"\\wsl.localhost\Ubuntu\home\eros\.openclaw\workspace-content-ma\docs"

# Chroma 持久化路径
CHROMA_PATH = r"D:\Python\vector_db\chroma_data"

# 集合名称
COLLECTION_NAME = "my_docs"


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
                    # 简单处理 docx - 读取失败则跳过
                    try:
                        import docx
                        doc = docx.Document(file)
                        content = '\n'.join([para.text for para in doc.paragraphs])
                    except:
                        print(f"跳过 docx 文件: {file.name}")
                        continue

                docs.append({
                    'id': file.stem,  # 文件名作为 ID
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
    # 按段落分割
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


def init_database():
    """初始化 Chroma 数据库"""
    # 创建持久化客户端
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    # 删除已存在的集合（重新构建）
    try:
        client.delete_collection(name=COLLECTION_NAME)
        print(f"删除已存在的集合: {COLLECTION_NAME}")
    except:
        pass

    # 创建新集合
    collection = client.create_collection(name=COLLECTION_NAME)
    print(f"创建集合: {COLLECTION_NAME}")

    return client, collection


def import_documents():
    """导入文档到向量数据库"""
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
    print("步骤3: 向量化入库")
    print("="*50)
    client, collection = init_database()

    # 批量添加到向量数据库
    ids = [chunk['id'] for chunk in all_chunks]
    documents = [chunk['content'] for chunk in all_chunks]
    metadatas = [{'source': chunk['source']} for chunk in all_chunks]

    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )

    print(f"已导入 {len(ids)} 个文档块")
    return collection


def search(query_text, n_results=3):
    """语义搜索"""
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_collection(name=COLLECTION_NAME)

    results = collection.query(
        query_texts=[query_text],
        n_results=n_results,
        include=['documents', 'metadatas', 'distances']
    )

    return results


if __name__ == "__main__":
    # 导入文档
    collection = import_documents()

    print("\n" + "="*50)
    print("文档导入完成!")
    print("="*50)
    print(f"集合名称: {COLLECTION_NAME}")
    print(f"文档数量: {collection.count()}")
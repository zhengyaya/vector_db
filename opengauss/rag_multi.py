"""
阶段3：RAG 知识问答系统 - 多集合版本
功能：支持多集合管理、元数据过滤、对话历史
"""

import requests
import json
import chromadb
from datetime import datetime, timedelta
import rag_config as config

# 文档目录
DOCS_PATH = r"\\wsl.localhost\Ubuntu\home\eros\.openclaw\workspace-content-ma\docs"
CHROMA_PATH = config.CHROMA_PATH

# 主题集合配置
COLLECTIONS = {
    "multi_agent": {
        "name": "多Agent协同",
        "files": ["OpenClaw多Agent协同实战.md", "OpenClaw多Agent协同工作实战.md"]
    },
    "knowledge_tools": {
        "name": "知识工程工具",
        "files": ["知识工程实战平台-工具链说明书与操作指南.md"]
    }
}


def init_collections():
    """初始化多个集合"""
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    # 删除旧集合
    try:
        client.delete_collection(name="my_docs")
        print("删除旧集合: my_docs")
    except:
        pass

    # 创建新集合
    for coll_id, coll_info in COLLECTIONS.items():
        try:
            client.delete_collection(name=coll_id)
            print(f"删除旧集合: {coll_id}")
        except:
            pass

        collection = client.create_collection(name=coll_id)
        print(f"创建集合: {coll_id} - {coll_info['name']}")

    return client


def read_documents():
    """读取文档目录下的所有文件"""
    import os
    from pathlib import Path

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
    """按主题导入文档到不同集合"""
    print("\n" + "="*50)
    print("读取文档")
    print("="*50)
    docs = read_documents()

    client = init_collections()

    # 按主题分配文档
    for coll_id, coll_info in COLLECTIONS.items():
        collection = client.get_collection(name=coll_id)

        matching_docs = [d for d in docs if d['source'] in coll_info['files']]
        all_chunks = []

        for doc in matching_docs:
            chunks = chunk_text(doc['content'], chunk_size=500)
            for i, chunk in enumerate(chunks):
                all_chunks.append({
                    'id': f"{doc['id']}_{i}",
                    'content': chunk,
                    'source': doc['source']
                })
            print(f"{doc['source']}: 切分成 {len(chunks)} 个块")

        # 添加到集合
        if all_chunks:
            collection.add(
                ids=[c['id'] for c in all_chunks],
                documents=[c['content'] for c in all_chunks],
                metadatas=[{'source': c['source']} for c in all_chunks]
            )
            print(f"集合 {coll_id}: 已导入 {len(all_chunks)} 个文档块")

    print("\n文档导入完成!")

    # 显示集合统计
    print("\n" + "="*50)
    print("集合统计")
    print("="*50)
    for coll_id, coll_info in COLLECTIONS.items():
        collection = client.get_collection(name=coll_id)
        print(f"- {coll_id}: {collection.count()} 个文档块")


# 对话历史管理
class ChatHistory:
    """对话历史管理器"""

    def __init__(self, max_days=7):
        self.max_days = max_days
        self.history = []
        self.client = chromadb.PersistentClient(path=CHROMA_PATH)

    def add(self, query: str, answer: str, sources: list):
        """添加对话记录"""
        self.history.append({
            'query': query,
            'answer': answer,
            'sources': sources,
            'timestamp': datetime.now()
        })

    def get_context(self, max_turns=3):
        """获取对话历史上下文"""
        # 清理过期记录
        cutoff = datetime.now() - timedelta(days=self.max_days)
        self.history = [h for h in self.history if h['timestamp'] > cutoff]

        # 返回最近N轮对话
        recent = self.history[-max_turns:] if self.history else []
        return recent

    def clear(self):
        """清空历史"""
        self.history = []


def call_llm(prompt: str) -> str:
    """调用 LLM"""
    url = f"{config.MINIMAX_BASE_URL}/text/chatcompletion_v2"
    headers = {
        "Authorization": f"Bearer {config.MINIMAX_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": config.MINIMAX_MODEL,
        "messages": [
            {"role": "system", "content": "你是一个专业的知识助手，请根据提供的上下文回答用户的问题。"},
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.post(url, headers=headers, json=payload, timeout=60)
    result = response.json()

    if 'choices' in result and len(result['choices']) > 0:
        return result['choices'][0]['message']['content']
    elif 'error' in result:
        return f"API错误: {result['error']}"
    else:
        return f"调用失败: {result}"


def search_in_collection(query: str, collection_name: str, n_results: int = 3):
    """在指定集合中搜索"""
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_collection(name=collection_name)

    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        include=['documents', 'metadatas', 'distances']
    )

    return results


def rag_query_with_collection(query: str, collection_name: str = None, use_history: bool = True) -> dict:
    """
    RAG 问答 - 支持多集合

    Args:
        query: 用户问题
        collection_name: 指定集合名，不指定则自动选择
        use_history: 是否使用对话历史

    Returns:
        dict: 问答结果
    """
    # 自动选择最佳集合
    if collection_name is None:
        # 简单策略：遍历所有集合，找最佳匹配
        best_results = None
        best_distance = float('inf')
        best_collection = None

        for coll_id in COLLECTIONS.keys():
            results = search_in_collection(query, coll_id, n_results=2)
            if results['distances'] and results['distances'][0]:
                min_dist = min(results['distances'][0])
                if min_dist < best_distance:
                    best_distance = min_dist
                    best_collection = coll_id
                    best_results = results

        collection_name = best_collection
        results = best_results
    else:
        results = search_in_collection(query, collection_name, n_results=3)

    # 提取结果
    context_docs = results['documents'][0]
    distances = results['distances'][0]
    metadatas = results['metadatas'][0]

    print(f"\n检索集合: {collection_name}")
    print(f"召回文档数: {len(context_docs)}")
    print(f"最佳距离: {min(distances):.4f}")

    # 构建 Prompt
    context = "\n\n".join([
        f"【文档 {i+1}】{doc[:200]}..."
        for i, doc in enumerate(context_docs)
    ])

    prompt = f"""请根据以下上下文信息回答用户的问题。

用户问题：{query}

参考文档：
{context}

要求：
1. 只根据提供的文档内容回答
2. 如果没有相关信息，请明确告知

回答："""

    # 调用 LLM
    answer = call_llm(prompt)

    return {
        'query': query,
        'answer': answer,
        'sources': context_docs,
        'distances': distances,
        'collection': collection_name
    }


if __name__ == "__main__":
    # 导入文档到新集合
    import_documents()
"""
阶段3：RAG 客服系统完整版
功能：多集合 + 元数据过滤 + 对话历史 + 多轮对话
"""
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import json
import chromadb
from datetime import datetime, timedelta
from rag_multi import COLLECTIONS, call_llm as llm_call


# Chroma 配置
CHROMA_PATH = r"D:\Python\vector_db\chroma_data"


class ChatHistory:
    """对话历史管理器"""

    def __init__(self, max_days=7):
        self.max_days = max_days
        self.history = []
        self.client = chromadb.PersistentClient(path=CHROMA_PATH)

    def add(self, query: str, answer: str, sources: list, collection: str):
        """添加对话记录"""
        self.history.append({
            'query': query,
            'answer': answer,
            'sources': sources,
            'collection': collection,
            'timestamp': datetime.now()
        })
        print(f"已保存对话到历史 (共 {len(self.history)} 条)")

    def get_context(self, max_turns=3):
        """获取对话历史上下文"""
        # 清理过期记录
        cutoff = datetime.now() - timedelta(days=self.max_days)
        self.history = [h for h in self.history if h['timestamp'] > cutoff]

        # 返回最近N轮对话
        recent = self.history[-max_turns:] if self.history else []

        if recent:
            print(f"\n对话历史 ({len(recent)} 条):")
            for i, h in enumerate(recent):
                print(f"  {i+1}. Q: {h['query'][:30]}...")

        return recent

    def clear(self):
        """清空历史"""
        self.history = []
        print("对话历史已清空")


def search_with_filter(query: str, collection_name: str, n_results: int = 3, metadata_filter: dict = None):
    """在指定集合中搜索，支持元数据过滤"""
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_collection(name=collection_name)

    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        where=metadata_filter,  # 元数据过滤
        include=['documents', 'metadatas', 'distances']
    )

    return results


def search_auto(query: str, n_results: int = 3):
    """自动选择最佳集合搜索"""
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    best_results = None
    best_distance = float('inf')
    best_collection = None

    for coll_id in COLLECTIONS.keys():
        collection = client.get_collection(name=coll_id)
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            include=['documents', 'metadatas', 'distances']
        )

        if results['distances'] and results['distances'][0]:
            min_dist = min(results['distances'][0])
            print(f"  {coll_id}: 距离 {min_dist:.4f}")

            if min_dist < best_distance:
                best_distance = min_dist
                best_collection = coll_id
                best_results = results

    return best_results, best_collection


def build_rag_prompt(query: str, context_docs: list, chat_history: list = None) -> str:
    """构建 RAG Prompt，支持对话历史"""
    # 拼接历史上下文
    history_text = ""
    if chat_history:
        history_text = "\n\n之前的对话：\n"
        for h in chat_history:
            history_text += f"- 用户问：{h['query']}\n  回答：{h['answer'][:100]}...\n"

    # 拼接当前文档
    context = "\n\n".join([
        f"【文档 {i+1}】{doc[:200]}..."
        for i, doc in enumerate(context_docs)
    ])

    prompt = f"""请根据以下上下文信息回答用户的问题。
{history_text}
用户问题：{query}

参考文档：
{context}

要求：
1. 只根据提供的文档内容回答
2. 如果文档中没有相关信息，请明确告知
3. 如果用户追问，结合之前的对话历史回答

回答："""

    return prompt


def rag_query(query: str, use_history: bool = True) -> dict:
    """
    RAG 问答题

    Args:
        query: 用户问题
        use_history: 是否使用对话历史

    Returns:
        dict: 问答结果
    """
    print(f"\n{'='*60}")
    print(f"问题: {query}")
    print(f"{'='*60}")

    # 获取对话历史
    chat_history = None
    if use_history:
        chat_history = chat_manager.get_context(max_turns=2)

    # 自动搜索最佳集合
    print(f"\n🔍 自动检索...")
    results, collection = search_auto(query, n_results=3)

    # 提取结果
    context_docs = results['documents'][0]
    distances = results['distances'][0]
    metadatas = results['metadatas'][0]

    print(f"\n📄 检索结果:")
    print(f"  集合: {collection}")
    print(f"  文档数: {len(context_docs)}")
    print(f"  最佳距离: {min(distances):.4f}")

    # 显示每个文档
    for i, (doc, dist, meta) in enumerate(zip(context_docs, distances, metadatas)):
        print(f"  文档{i+1}: 距离 {dist:.4f}, 来源: {meta.get('source', '未知')[:30]}...")

    # 构建 Prompt
    prompt = build_rag_prompt(query, context_docs, chat_history)

    # 调用 LLM
    print(f"\n🤖 调用 LLM...")
    answer = llm_call(prompt)

    # 保存到历史
    if use_history:
        chat_manager.add(query, answer, context_docs, collection)

    return {
        'query': query,
        'answer': answer,
        'sources': context_docs,
        'distances': distances,
        'collection': collection
    }


# 全局对话管理器
chat_manager = ChatHistory(max_days=7)


def chat_loop():
    """对话循环"""
    print("="*60)
    print("RAG 智能客服系统 v3.0")
    print("="*60)
    print("命令:")
    print("  /history - 查看对话历史")
    print("  /clear - 清空历史")
    print("  /quit - 退出")
    print("="*60)

    while True:
        query = input("\n你: ").strip()

        if not query:
            continue

        if query.lower() == '/quit':
            print("👋 再见！")
            break
        elif query.lower() == '/history':
            chat_manager.get_context()
        elif query.lower() == '/clear':
            chat_manager.clear()
        else:
            try:
                result = rag_query(query)
                print(f"\n{'='*60}")
                print("回答:")
                print(f"{'='*60}")
                print(result['answer'])
            except Exception as e:
                print(f"❌ 错误: {e}")


if __name__ == "__main__":
    chat_loop()
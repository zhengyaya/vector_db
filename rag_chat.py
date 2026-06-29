"""
阶段2：RAG 知识问答系统
功能：结合向量检索 + LLM 实现智能问答
"""

import requests
import json
from vector_search import search
import rag_config as config


def call_llm(prompt: str) -> str:
    """调用 MiniMax LLM API"""
    url = f"{config.MINIMAX_BASE_URL}/text/chatcompletion_v2"
    headers = {
        "Authorization": f"Bearer {config.MINIMAX_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": config.MINIMAX_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "你是一个专业的知识助手，请根据提供的上下文回答用户的问题。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    response = requests.post(url, headers=headers, json=payload, timeout=60)
    result = response.json()

    # 调试用
    if response.status_code != 200:
        return f"HTTP错误: {response.status_code}, {response.text}"

    if 'choices' in result and len(result['choices']) > 0:
        return result['choices'][0]['message']['content']
    elif 'error' in result:
        return f"API错误: {result['error']}"
    else:
        return f"调用失败: {result}"


def build_rag_prompt(query: str, context_docs: list) -> str:
    """构建 RAG Prompt"""
    # 构建上下文
    context = "\n\n".join([
        f"【文档 {i+1}】{doc}"
        for i, doc in enumerate(context_docs)
    ])

    prompt = f"""请根据以下上下文信息回答用户的问题。

用户问题：{query}

参考文档：
{context}

要求：
1. 只根据提供的文档内容回答，不要编造信息
2. 如果文档中没有相关信息，请明确告知用户
3. 回答要简洁、准确

回答："""
    return prompt


def rag_query(query: str, top_k: int = None) -> dict:
    """
    RAG 问答主函数

    Args:
        query: 用户问题
        top_k: 召回的文档数量

    Returns:
        dict: 包含 answer, sources 等信息
    """
    if top_k is None:
        top_k = config.TOP_K

    # 1. 向量检索
    print(f"🔍 检索相关文档...")
    results = search(query, n_results=top_k)

    # 2. 提取文档内容
    context_docs = results['documents'][0]
    distances = results['distances'][0]

    print(f"📄 召回 {len(context_docs)} 条相关文档")

    # 3. 构建 Prompt
    rag_prompt = build_rag_prompt(query, context_docs)

    # 4. 调用 LLM
    print(f"🤖 调用 LLM 生成答案...")
    answer = call_llm(rag_prompt)

    # 5. 返回结果
    return {
        'query': query,
        'answer': answer,
        'sources': context_docs,
        'distances': distances
    }


def chat_loop():
    """对话循环"""
    print("=" * 60)
    print("RAG 知识问答系统")
    print("=" * 60)
    print("输入问题进行问答，输入 'quit' 退出")
    print()

    while True:
        query = input("❓ 你: ").strip()

        if not query:
            continue

        if query.lower() in ['quit', 'q', '退出']:
            print("👋 再见！")
            break

        try:
            result = rag_query(query)
            print("\n" + "=" * 60)
            print("🤖 回答:")
            print("-" * 60)
            print(result['answer'])
            print("=" * 60)
            print()
        except Exception as e:
            print(f"❌ 错误: {e}")


if __name__ == "__main__":
    chat_loop()
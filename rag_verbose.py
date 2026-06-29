"""
RAG 问答系统 - 详细步骤展示版
"""
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

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

    print(f"\n{'='*60}")
    print("📡 步骤3: 调用 LLM API")
    print("-"*60)
    print(f"模型: {config.MINIMAX_MODEL}")
    print(f"API URL: {url}")

    response = requests.post(url, headers=headers, json=payload, timeout=60)
    result = response.json()

    print(f"HTTP 状态码: {response.status_code}")

    if 'choices' in result and len(result['choices']) > 0:
        content = result['choices'][0]['message']['content']
        print(f"Token 使用: {result.get('usage', {})}")
        return content
    elif 'error' in result:
        return f"API错误: {result['error']}"
    else:
        return f"调用失败: {result}"


def build_rag_prompt(query: str, context_docs: list, distances: list) -> str:
    """构建 RAG Prompt"""
    print(f"\n{'='*60}")
    print("📝 步骤2: 构建 Prompt")
    print("-"*60)

    # 构建上下文
    context_parts = []
    for i, (doc, dist) in enumerate(zip(context_docs, distances)):
        # 取前200字作为摘要
        doc_preview = doc[:200].replace('\n', ' ')
        context_parts.append(f"【文档 {i+1}】(相似度距离: {dist:.4f})\n{doc_preview}...")

    context = "\n\n".join(context_parts)

    prompt = f"""请根据以下上下文信息回答用户的问题。

用户问题：{query}

参考文档：
{context}

要求：
1. 只根据提供的文档内容回答，不要编造信息
2. 如果文档中没有相关信息，请明确告知用户
3. 回答要简洁、准确
4. 在回答中标注参考了哪些文档

回答："""

    print(f"用户问题: {query}")
    print(f"召回文档数: {len(context_docs)}")
    print(f"Prompt 长度: {len(prompt)} 字符")

    return prompt


def rag_query_verbose(query: str, top_k: int = None) -> dict:
    """
    RAG 问答题细展示版

    Args:
        query: 用户问题
        top_k: 召回的文档数量

    Returns:
        dict: 包含所有步骤的详细信息
    """
    if top_k is None:
        top_k = config.TOP_K

    print(f"\n{'#'*60}")
    print(f"# RAG 问答详细流程")
    print(f"{'#'*60}")
    print(f"用户问题: {query}")
    print(f"Top K: {top_k}")

    # ========================================
    # 步骤1: 向量检索
    # ========================================
    print(f"\n{'='*60}")
    print("🔍 步骤1: 向量检索")
    print("-"*60)
    print(f"查询文本: {query}")
    print(f"目标召回数: {top_k}")

    results = search(query, n_results=top_k)

    # 提取结果
    context_docs = results['documents'][0]
    distances = results['distances'][0]
    metadatas = results['metadatas'][0]

    print(f"\n✅ 检索完成!")
    print(f"召回文档数: {len(context_docs)}")

    # 显示每条文档的详细信息
    print(f"\n{'─'*60}")
    print("📄 召回文档详情:")
    print(f"{'─'*60}")
    for i, (doc, dist, meta) in enumerate(zip(context_docs, distances, metadatas)):
        print(f"\n--- 文档 {i+1} ---")
        print(f"来源: {meta.get('source', '未知')}")
        print(f"相似度距离: {dist:.4f} {'✅ 高度相似' if dist < 1.0 else '⚠️ 中等相似' if dist < 1.5 else '❌ 低相似度'}")
        print(f"内容预览: {doc[:150].replace(chr(10), ' ')}...")

    # ========================================
    # 步骤2: 构建 Prompt
    # ========================================
    rag_prompt = build_rag_prompt(query, context_docs, distances)

    # ========================================
    # 步骤3: 调用 LLM
    # ========================================
    answer = call_llm(rag_prompt)

    # ========================================
    # 步骤4: 返回结果
    # ========================================
    print(f"\n{'='*60}")
    print("✅ 步骤4: 完成")
    print("-"*60)
    print(f"回答长度: {len(answer)} 字符")

    return {
        'query': query,
        'answer': answer,
        'sources': context_docs,
        'distances': distances,
        'metadatas': metadatas
    }


if __name__ == "__main__":
    # 测试问题
    test_query = "知识工程实战平台应该如何使用"
    print(f"\n{'#'*60}")
    print(f"# 测试问题: {test_query}")
    print(f"{'#'*60}")

    result = rag_query_verbose(test_query)

    print(f"\n{'='*60}")
    print("📝 最终回答:")
    print(f"{'='*60}")
    print(result['answer'])
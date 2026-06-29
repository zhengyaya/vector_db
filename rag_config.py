"""
RAG 知识问答系统 - 配置文件
"""

# MiniMax API 配置
MINIMAX_API_KEY = "sk-cp--zlHZf5TD4kaieFIsaJyJQvoBLFOoolbxKiRosMB7mNmdj9wD2pHh7uf7iUfHTKG9LAF2_cgMFpw0X_LVUlbOD616s2yWQDIFH5bFDgOlhEIWpSX5cMfS20"  # 替换为你的 API Key
MINIMAX_BASE_URL = "https://api.minimax.chat/v1"
MINIMAX_MODEL = "MiniMax-M3"

# Chroma 配置
CHROMA_PATH = r"D:\Python\vector_db\chroma_data"
COLLECTION_NAME = "my_docs"

# RAG 配置
TOP_K = 3  # 召回最相似的 Top K 条文档
MAX_CONTEXT_LENGTH = 2000  # 上下文最大字符数
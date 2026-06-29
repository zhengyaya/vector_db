# test_v3.py
import sys
import io

# 重新配置 stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from rag_chatbot import rag_query

result = rag_query("什么是多 Agent 协同？")
print("\n回答:", result['answer'][:300])
print("\n集合:", result['collection'])
print("最佳距离:", result['distances'][0])
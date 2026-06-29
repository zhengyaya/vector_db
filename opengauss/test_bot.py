# -*- coding: utf-8 -*-
import sys
import io

class UTF8Output:
    def __init__(self, original):
        self.original = original
    def write(self, text):
        self.original.write(text.encode('utf-8').decode('utf-8'))
    def flush(self):
        self.original.flush()

sys.stdout = UTF8Output(sys.__stdout__)
sys.stderr = UTF8Output(sys.__stderr__)

from rag_chatbot import rag_query

query = "什么是多 Agent 协同？"
print("问题: " + query)
print("-" * 60)

result = rag_query(query)
print()
print("回答: " + result['answer'][:300])
print()
print("集合: " + result['collection'])
print("最佳距离: " + str(result['distances'][0]))
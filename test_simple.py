# test_simple.py
# -*- coding: utf-8 -*-
import subprocess
import sys

# 设置 UTF-8 输出
subprocess.run([sys.executable, "-c", '''
# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

from rag_chatbot import rag_query

result = rag_query("什么是多 Agent 协同？")
print("ANSWER:", result["answer"][:300])
print("COLLECTION:", result["collection"])
print("DISTANCE:", result["distances"][0])
'''], cwd="D:/Python/vector_db")
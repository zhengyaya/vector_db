# 向量数据库学习项目

> 基于 Chroma/OpenGauss + MiniMax LLM 的向量数据库学习项目

---

## 项目简介

本项目是一个完整的向量数据库学习路径，从基础到进阶逐步掌握向量数据库的核心概念和应用。支持两种向量数据库：
- **Chroma**：轻量级向量数据库
- **OpenGauss**：企业级关系型数据库（支持向量存储）

---

## 目录结构

```
vector_db/
├── README.md                    # 项目说明文件
├── learning.md                 # 学习笔记
│
├── 核心代码 (Chroma版本)
│   ├── chroma_test.py         # Chroma 入门测试
│   ├── vector_search.py      # 向量入库和搜索（阶段1）
│   ├── rag_chat.py         # RAG 问答（阶段2）
│   ├── rag_chatbot.py      # AI 客服系统（阶段3）
│   ├── rag_multi.py        # 多集合管理
│   └── rag_config.py      # 配置文件（本地，不上传）
│
├── 核心代码 (OpenGauss版本)
│   ├── opengauss/
│   │   ├── vector_search.py  # 向量入库和搜索
│   │   ├── test_og_search.py  # 向量搜索测试
│   │   └── og_config.py  # 配置文件（本地，不上传）
│
├── 工具脚本
│   ├── view_chroma_data.py # 查看持久化数据
│   ├── test_search.py     # 搜索测试
│   ├── test_rag.py       # RAG 测试
│   ├── test_compare.py   # 效果对比测试
│   ├── test_direct.py   # 直接测试
│   └── test_compare_v3.py # 多集合效果对比
│
├── 数据存储
│   ├── chroma_data/      # Chroma 持久化数据
│   │   ├── chroma.sqlite3
│   │   │   └── */
│   │
│   └── __pycache__/      # Python 缓存
│
└── .claude/            # Claude 配置
```

---

## 数据库支持

| 数据库 | 类型 | 向量存储 | 适用场景 |
|--------|------|---------|----------|
| Chroma | 嵌入式 | 原生 | 轻量级应用、原型开发 |
| OpenGauss | 企业级 | float4[]数组 | 企业级应用、需要SQL查询 |

---

## 学习路径

### 阶段1：语义搜索系统
- **文件**: `vector_search.py`
- **功能**: 文档向量化、入库、语义搜索
- **掌握**: 向量、embedding、相似度检索

### 阶段2：RAG 知识问答系统
- **文件**: `rag_chat.py`
- **功能**: 结合 LLM 实现问答
- **掌握**: RAG、Prompt 工程、上下文召回

### 阶段3：AI 客服系统
- **文件**: `rag_chatbot.py`
- **功能**: 多集合管理、对话历史、多轮对话
- **掌握**: 多集合、元数据过滤、记忆管理

---

## 快速开始

### 1. 安装依赖
```bash
pip install chromadb requests psycopg2-binary
```

### 2. 配置 API
编辑对应目录下的配置文件，填入 MiniMax API Key：
- Chroma版本: `rag_config.py`
- OpenGauss版本: `opengauss/og_config.py`

```python
MINIMAX_API_KEY = "your-api-key"
```

### 3. 运行测试
```bash
# Chroma版本 - 向量搜索
python vector_search.py

# OpenGauss版本 - 向量搜索
cd opengauss
python vector_search.py

# RAG 问答
python rag_chat.py
```

---

## 配置文件说明

### rag_config.py (Chroma版本)
```python
# MiniMax API 配置
MINIMAX_API_KEY = "your-api-key"
MINIMAX_BASE_URL = "https://api.minimax.chat/v1"
MINIMAX_MODEL = "MiniMax-M3"

# Chroma 配置
CHROMA_PATH = r"D:\Python\vector_db\chroma_data"
COLLECTION_NAME = "my_docs"

# RAG 配置
TOP_K = 3
MAX_CONTEXT_LENGTH = 2000
```

### opengauss/og_config.py (OpenGauss版本)
```python
# OpenGauss 连接配置
OG_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'postgres',
    'user': 'gaussdb',
    'password': 'your-password'
}

# MiniMax API 配置
MINIMAX_API_KEY = "your-api-key"
MINIMAX_BASE_URL = "https://api.minimax.chat/v1"
MINIMAX_MODEL = "MiniMax-M3"
EMBEDDING_MODEL = "embo-01"

# 文档目录
DOCS_PATH = r"your-docs-path"

# RAG 配置
TOP_K = 3
MAX_CONTEXT_LENGTH = 2000
```

---

## 核心功能说明

### 向量检索 (Chroma)
```python
from vector_search import search

results = search("什么是多 Agent 协同？", n_results=3)
# 返回：documents, distances, metadatas
```

### 向量检索 (OpenGauss)
```python
from opengauss.vector_search import search

results = search("什么是多 Agent 协同？", n_results=3)
# 返回：[(id, content, source, similarity), ...]
```

### RAG 问答
```python
from rag_chat import rag_query

result = rag_query("什么是知识工程？")
print(result['answer'])  # LLM 生成的答案
print(result['sources']) # 参考文档
```

---

## 数据说明

### Chroma 持久化结构
```
chroma_data/
├── chroma.sqlite3              # 元数据（SQLite）
└── [collection_id]/
    ├── data_level0.bin         # 向量数据（二进制）
    ├── header.bin
    ├── length.bin
    └── link_lists.bin
```

### OpenGauss 表结构
```sql
CREATE TABLE vector_docs (
    id VARCHAR(255) PRIMARY KEY,
    content TEXT NOT NULL,
    source VARCHAR(255),
    vector FLOAT4[],  -- 1536维向量
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 向量维度
- Chroma: 384维向量
- OpenGauss: 1536维向量 (embo-01模型)

---

## 知识库

默认使用 WSL 路径的文档：
- `\\wsl.localhost\Ubuntu\home\eros\.openclaw\workspace-content-ma\docs`

已导入文档：
| 集合 | 文档数 | 主题 |
|------|--------|------|
| multi_agent | 27 | 多Agent协同 |
| knowledge_tools | 18 | 知识工程工具 |

---

## 技术栈

| 技术 | 说明 |
|------|------|
| Chroma | 向量数据库 |
| OpenGauss | 企业级数据库（支持向量） |
| MiniMax M3 | LLM 模型 |
| MiniMax embo-01 | Embedding 模型 |
| SQLite | Chroma元数据存储 |
| HNSW | Chroma向量索引算法 |

---

## 学习笔记

详细的学习问答记录在 [learning.md](learning.md) 中，包括：
- 阶段1完成后的问答（4轮）
- 阶段2的测试记录（4个问题）
- 阶段3的效果对比

---

## 注意事项

1. 配置文件包含敏感信息，不上传到GitHub
   - `rag_config.py`
   - `opengauss/og_config.py`
2. 需要有效的 MiniMax API Key
3. OpenGauss版本需要先启动Docker容器
4. 知识库内容有限，检索效果取决于文档质量

---

## License

MIT
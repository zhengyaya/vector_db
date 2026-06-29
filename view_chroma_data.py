import chromadb

chroma_client = chromadb.PersistentClient(path="D:/path/to/save/to")

# 获取集合
collection = chroma_client.get_collection(name="my_collection")

print("=" * 50)
print("集合信息")
print("=" * 50)
print("文档数量:", collection.count())

print("\n" + "=" * 50)
print("所有数据")
print("=" * 50)
print(collection.get())

print("\n" + "=" * 50)
print("按ID查询 id1")
print("=" * 50)
print(collection.get(ids=["id1"]))

print("\n" + "=" * 50)
print("搜索测试: 查询 'hawaii' 相关文档")
print("=" * 50)
results = collection.query(
    query_texts=["This is a query document about hawaii"],
    n_results=2
)
print(results)
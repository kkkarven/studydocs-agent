from doc_tools import list_docs, read_doc,search_docs

query = input("输入你要查询的关键词：")
while (query != "q"):
    language = input("是否指定语言：")
    if language == "q":
        break
    result = search_docs(query,language)
    print("搜索结果：",result)
    query = input("输入你要查询的关键词：")
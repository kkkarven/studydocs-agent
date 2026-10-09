from doc_tools import list_docs, read_doc


# 第一部分：检查资料列表
doc_names = list_docs()
print("资料列表：", doc_names)
for doc_name in doc_names:
    documents = read_doc(doc_name)
    source = documents["source"]
    line = documents["lines"]
    print("资料名称：",source)
    print("资料内容：",line)
# 在这里补充对列表内容、顺序的观察。


# 第二部分：检查正常读取
# 在这里分别显示 source 和原文行列表。
# 再检查其他两份资料。
#上面已完成

# 第三部分：检查读取是否跟随文件变化
# 修改资料中的一句话，保存后重新运行。
# 对照输出，确认读到的是修改后的内容。


# 第四部分：检查非法输入
read_doc("不存在的文件.md")
# 核心函数完成后，再加入非法文件名的读取检查。
# 放在正常检查之后，或单独运行，观察预期报错。
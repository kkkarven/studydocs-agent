from pathlib import Path


# 两个工具共用的资料目录
DOCS_DIR = Path("data/reference").resolve()


def list_docs():
    filenames = []

    for file_path in DOCS_DIR.glob("*.md"):
        real_path = file_path.resolve()

        if real_path.is_file() and real_path.is_relative_to(DOCS_DIR):
            filenames.append(file_path.name)

    return sorted(filenames)


def read_doc(filename):
    # filename 是资料文件名字符串。
    # 对不符合资料范围的输入明确报错。
    # 返回包含 source 和 lines 的字典。
    # 在这里补充实现。
    if filename not in list_docs():
        raise ValueError("文件名不在允许读取的资料列表中")

    file_path = (DOCS_DIR / filename).resolve()

    if not file_path.is_relative_to(DOCS_DIR):
        raise ValueError("文件路径超出资料目录")

    text = file_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    return {
        "source": filename,
        "lines": lines,
    }
def search_docs(key_word,language = ""):
    search_result =[]
    if key_word.strip() == "":
        raise ValueError("关键词无效")
    lower_word = key_word.strip().lower()
    target_language = language.strip().lower()
    doc_names = list_docs()
    for doc_name in doc_names:
        documents = read_doc(doc_name)
        source = documents["source"]
        lines = documents["lines"]
        document_language = ""
        for metadata_line in lines:
            language_text = metadata_line.strip()
            if language_text.startswith("- 语言："):
                parts = language_text.split("：", 1)
                document_language = parts[1].strip().lower()
                break
        for line_number,line in enumerate(lines,start = 1):
            if lower_word in line.lower():
                result_item = {
                        "source" : source,
                        "line_number" : line_number,
                        "text": line}
                search_result.append(result_item)
                if target_language and not(target_language == document_language.lower()):
                    search_result.remove(result_item)
    return  search_result
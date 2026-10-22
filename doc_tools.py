from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
DOCS_DIR = (PROJECT_DIR / "data" / "reference").resolve()


def list_docs():#取文件名
    filenames = []
    for file_path in DOCS_DIR.glob("*.md"):
        real_path = file_path.resolve()
        if real_path.is_file() and real_path.is_relative_to(DOCS_DIR):
            filenames.append(file_path.name)
    return sorted(filenames)
def read_doc(filename):#取文件{名，内容}
    if filename not in list_docs():
        raise ValueError("文件名不在允许读取的资料列表中")
    file_path = (DOCS_DIR / filename).resolve()
    if not file_path.is_relative_to(DOCS_DIR):
        raise ValueError("文件路径超出资料目录")
    text = file_path.read_text(encoding =  "utf-8")
    return{
        "source":filename,
        "lines":text.splitlines(),
    }
def search_docs(key_word,language = ""):#搜索文件，关键词匹配，语言匹配
    if not isinstance(key_word,str) or not isinstance(language,str):
        raise ValueError("关键词和语言必须是字符串")
    keyword =  key_word.strip().lower()
    target_language = language.strip().lower()
    if not keyword:
        raise ValueError("关键词不能为空")
    results = []
    for filename in list_docs():
        document = read_doc(filename)
        lines = document["lines"]

        document_langugae = ""
        for line in lines:#语言匹配
            metadata = line.strip()
            if metadata.startswith("- 语言："):
                document_langugae = metadata.split("：",1)[1].strip().lower()
                break
        if target_language and (target_language != document_langugae):
            continue
        for line_number,line in enumerate(lines,start=1):
            if keyword in line.lower():
                results.append({
                    "source":document["source"],
                    "line_number":line_number,
                    "text":line,
                })
    return results
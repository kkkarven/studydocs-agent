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
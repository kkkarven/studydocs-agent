import json
from pathlib import Path

from doc_tools import list_docs


PROJECT_DIR = Path(__file__).resolve().parent
STATE_FILE = PROJECT_DIR / "data" / "private" / "familiar.json"


def load_state():
    if not STATE_FILE.exists():
        return {"familiar": []}

    text = STATE_FILE.read_text(encoding="utf-8")
    state = json.loads(text)

    if not isinstance(state, dict):
        raise ValueError("熟悉状态必须是字典。")

    familiar = state.get("familiar")

    if not isinstance(familiar, list):
        raise ValueError("familiar 字段必须是列表。")

    for filename in familiar:
        if not isinstance(filename, str):
            raise ValueError("熟悉条目必须是文件名字符串。")

    return state


def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

    text = json.dumps(
        state,
        ensure_ascii=False,
        indent=2,
    )

    STATE_FILE.write_text(text, encoding="utf-8")

def register_familiar(filename):
    if not isinstance(filename, str):
        raise ValueError("熟悉条目必须是文件名字符串。")
    if filename not in list_docs():
        raise ValueError("条目不在docs中")
    state = load_state()
    familiar = state["familiar"]
    if filename in familiar:
        return False
    else:
        familiar.append(filename)
        save_state(state)
        return True
    # 检查 filename 是字符串，且在 list_docs() 中。
    # 读取状态，取得 familiar 列表。
    # 已登记：返回 False。
    # 未登记：加入列表，保存状态，返回 True。


def unregister_familiar(filename):
    if not isinstance(filename, str):
        raise ValueError("熟悉条目必须是文件名字符串。")
    if filename not in list_docs():
        raise ValueError("条目不在docs中")
    state = load_state()
    familiar = state["familiar"]
    if filename not in familiar:
        return False
    else:
        familiar.remove(filename)
        save_state(state)
        return True
    # 检查 filename 是字符串，且在 list_docs() 中。
    # 读取状态，取得 familiar 列表。
    # 未登记：返回 False。
    # 已登记：移除条目，保存状态，返回 True。


def list_familiar():
    state = load_state()
    familiar = state["familiar"]
    # 读取状态，返回其中的 familiar 列表。
    return familiar


def is_familiar(filename):
    if not isinstance(filename, str):
        raise ValueError("熟悉条目必须是文件名字符串。")
    if filename not in list_docs():
        raise ValueError("条目不在docs中")
    state = load_state()
    familiar = state["familiar"]
    if filename in familiar:
        return True
    else:

        return False
    # 检查 filename 是字符串，且在 list_docs() 中。
    # 读取状态，返回该文件名是否在 familiar 列表中。
    
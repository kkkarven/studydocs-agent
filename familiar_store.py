import json
from pathlib import Path

from doc_tools import list_docs


PROJECT_DIR = Path(__file__).resolve().parent
STATE_FILE = PROJECT_DIR/"data"/"private"/"familiar.json"

def vaildate_filename(filename):
    if not isinstance(filename,str):
        raise ValueError("熟悉条目必须是文件名字符串。")
    if filename not in list_docs():
        raise ValueError("条目不在资料列表中。")

def load_state():
    if not STATE_FILE.exists():
        return{"familiar":[]}
    
    state = json.loads(STATE_FILE.read_text(encoding="utf-8"))

    if not isinstance(state,dict):
        raise ValueError("熟悉状态必须是字典。")
    familiar = state.get("familiar")
    if not isinstance(familiar,list):
        raise("familiar字段必须是列表。")
    for filename in familiar:
        if not isinstance(filename,str):
            raise ValueError("熟悉条目必须是文件名字符串。")
    return state

def save_state(state):
    STATE_FILE.parent.mkdir(parents=True,exist_ok=True)

    text = json.dumps(state,ensure_ascii=False,indent=2)
    STATE_FILE.write_text(text,encoding="utf-8")

def register_familiar(filename):
    vaildate_filename(filename)
    state = load_state()
    familiar = state["familiar"]
    if filename in familiar:
        return False
    familiar.append(filename)
    save_state(state)
    return True

def unregister_familiar(filename):
    vaildate_filename(filename)
    state = load_state()
    familiar = state["familiar"]
    if filename not in familiar:
        return False
    familiar.remove(filename)
    save_state(state)
    return True

def list_familiar():
    return load_state()["familiar"]

def is_familiar(filename):
    vaildate_filename(filename)
    return filename in list_familiar()
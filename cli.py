import readline

import requests

from agent import new_conversation
from run_store import run_and_record as ask_agent,export_markdown
from doc_tools import read_doc
from familiar_store import (
    is_familiar,
    list_familiar,
    register_familiar,
    unregister_familiar,
)
from review_store import get_daily_review


ITEM_ALIASES = {
    "pythonprint": "python_print.md",
    "python打印": "python_print.md",
    "python字典按键取值": "python_dict_lookup.md",
    "c指针数组": "c_pointer_array.md",
}
ITME_LABELS = {
    "python_print.md": "Python print",
    "python_dict_lookup.md": "Python 字典按键取值",
    "c_pointer_array.md": "C 指针数组",
}
NO_ARGUMENT_COMMANDS = {
    "/退出",
    "/新会话",
    "/熟悉库",
    "/复习",
    "/导出",
}
ITEM_COMMANDS = {
    "/登记",
    "/取消登记",
    "/查看",
}

def reslove_item(text):
    normalized = "".join(text.split()).lower()
    return ITEM_ALIASES.get(normalized)

def main():
    print(
        "命令：/登记 条目、/取消登记 条目、/熟悉库、"
        "/复习、/查看 条目、/新会话、/导出、/退出"
    )
    history = new_conversation()
    completed_turns = 0
    max_session_turn = 2
    last_answer_record = None
    while True:
        try:
            user_text = input("> ").strip()
        except (EOFError,KeyboardInterrupt):
            print("\n已退出")
            break
        if not user_text:
            continue
        part = user_text.split(maxsplit=1)
        command = part[0]
        argument = part[1] if len(part) == 2 else ""

        try:
            if command in NO_ARGUMENT_COMMANDS and argument:
                print(f"{command} 不接受参数。")
                continue
            if command == "/退出":
                break
            elif command == "/新会话":
                history = new_conversation()
                completed_turns = 0
                print("已开启新对话")
            elif command == "/导出":
                if last_answer_record is None:
                    print("当前没有可导出的成功回答。")
                    continue
                path = export_markdown(last_answer_record)
                print("已导出",path)
            elif command == "/熟悉库":
                items = list_familiar()
                if not items:
                    print("熟悉库为空")
                for filename in items:
                    print(ITME_LABELS.get(filename,filename))
            elif command == "/复习":
                record = get_daily_review()
                print("今日复习日期：",record["date"])
                if record["items"]:
                    for filename in record["items"]:
                        print(ITME_LABELS.get(filename,filename))
                    print("使用 /查看 条目 可以查看资料原文。")
                elif not list_familiar():
                    print("熟悉库为空，尚无可复习条目")
                else:
                    print("今日复习组为空，新增条目将在下一天参与抽取。")
            elif command in ITEM_COMMANDS:
                if not argument:
                    print(f"请提供条目，例如：{command} Python print")
                    continue
                filename = reslove_item(argument)
                if filename is None:
                    print("未找到条目，请检查名称。")
                    continue
                if command == "/登记":
                    changed = register_familiar(filename)
                    print("已登记"if changed else"该条目已登记")
                elif command == "/取消登记":
                    changed = unregister_familiar(filename)
                    print ("已取消登记"if changed else"该条目尚未登记")
                else:#/查看
                    document = read_doc(filename)
                    print("\n".join(document["lines"]))
            else:
                if user_text.startswith("/"):
                    print("未知命令：",command)
                    continue
                if completed_turns >= max_session_turn:
                    history = new_conversation()
                    completed_turns = 0
                    print("已自动开启新会话")
                result = ask_agent(user_text,history)
                if result["answer"] is None:
                    print("达到模型请求上限，本次未获得最终回答。")
                    continue

                history = result["history"]
                completed_turns +=1
                last_answer_record = result["record"]
                print("\n模型回答：")
                print(result["answer"])

                sources = result["sources"]
                print("本轮实际读取资料：","、".join(sources) or "无")

                familar_sources = []#由用户输入匹配转为ai检索匹配
                for source in sources:
                    if is_familiar(source):
                        familar_sources.append(source)
                if familar_sources:
                    labels = [ITME_LABELS.get(source,source) for source in familar_sources]
                    print(
                        "本轮读取的资料中，已登记熟悉的条目：",
                        "、".join(labels),
                    )
                

        except (
            requests.exceptions.RequestException,
            ValueError,
            OSError,
        ) as error:
            print(f"本次操作失败：{type(error).__name__}:{error}")

if __name__ == "__main__":
    main()
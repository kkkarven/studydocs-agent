from familiar_store import (
    register_familiar,
    unregister_familiar,
    list_familiar,
)
import readline
from agent import ask_agent, new_conversation
from familiar_store import is_familiar
from review_store import get_daily_review
from doc_tools import read_doc
import requests

ITEM_ALIASES = {
    "python print": "python_print.md",
    "python 打印": "python_print.md",
    "python 字典按键取值": "python_dict_lookup.md",
    "c 指针数组": "c_pointer_array.md",
}
ITEM_LABELS = {
    "python_print.md": "Python print",
    "python_dict_lookup.md": "Python 字典按键取值",
    "c_pointer_array.md": "C 指针数组",
}

def resolve_item(text):
    processed_text = " ".join(text.split()).lower()
    if processed_text in ITEM_ALIASES:
        return ITEM_ALIASES[processed_text]
    else:
        return None
    # text：用户输入的条目名称字符串。
    # 去除首尾空白、转为小写。
    # 从 ITEM_ALIASES 查找，返回文件名或 None。


def main():
    print("可用命令：/登记 条目、/熟悉库、/取消登记 条目、/新会话、/复习、/查看 条目、/退出")

    history = new_conversation()
    completed_turns = 0
    max_session_turns = 2
    while True:
        user_text = input("> ").strip()

        if user_text == "":
            continue

        parts = user_text.split(maxsplit=1)
        command = parts[0]
        argument = ""

        if len(parts) == 2:
            argument = parts[1]
        try:
            if command == "/退出":
                if argument != "":
                    print("退出不接受参数")
                    continue
                # 不接受参数；无参数时退出循环。
                break
            elif command == "/新会话":
                if argument != "":
                    print("新会话不接受参数")
                    continue
                history = new_conversation()
                completed_turns =  0
                print("新会话已开启")
                # 拒绝额外参数。
                # 无参数时重新创建 history，将 completed_turns 设为 0。
                # 显示“已开始新会话”

            elif command == "/熟悉库":
                # 不接受参数。
                # 读取熟悉列表；空库提示，否则逐项显示。
                if argument != "":
                    print("熟悉库不接受参数")
                    continue
                familiar_items = list_familiar()
                if familiar_items:
                    for filename in familiar_items:
                        print(filename)
                else:
                    print("熟悉库为空")


            elif command == "/登记":
                # 参数不能为空，名称必须能解析。
                # 调用登记函数，根据返回值显示结果。
                if argument == "":
                    print("请提供条目，例如：/登记 Python print")
                    continue
                filename = resolve_item(argument)
                if filename is None:
                    print("未找到条目，请检查名称")
                    continue
                if register_familiar(filename):
                    print("已登记：",filename)
                else :
                    print("该条目已经登记：",filename)


            elif command == "/取消登记":
                # 参数不能为空，名称必须能解析。
                # 调用撤销函数，根据返回值显示结果。
                if argument == "":
                    print("请提供条目，例如：/取消登记 Python print")
                    continue
                filename =  resolve_item(argument)
                if filename is None:
                    print("未找到条目，请检查名称")
                    continue
                if unregister_familiar(filename):
                    print("已撤销登记：",filename)
                else:
                    print("该条目尚未登记",filename)
            elif command == "/复习":
                if argument != "":
                    print("复习不接受参数")
                    continue
                daily = get_daily_review()
                items = daily["items"]
                print("今日复习日期：",daily["date"])
                if items:
                    for filename in items:
                        label = ITEM_LABELS.get(filename, filename)
                        print(label)
                    print("请先回忆条目内容，再使用 /查看 <条目> 查看资料。")
                elif not list_familiar():
                    print("熟悉库为空，尚无可复习条目。")
                else:
                    print("今日复习组为空，新增登记条目将在下一天参与抽取。")
                # 拒绝额外参数。
                # 调用 get_daily_review()，显示日期和条目。
                # 不调用模型，不改变 history 和 completed_turns。
                pass

            elif command == "/查看":
                if argument == "":
                    print("请提供条目")
                    continue
                filename = resolve_item(argument)
                if filename is None:
                    print("未找到条目，请检查名称")
                    continue
                document = read_doc(filename)
                print("\n".join(document["lines"]))
                # 参数不能为空，使用 resolve_item(argument) 找到文件名。
                # 无法确定时提示并继续。
                # 读取资料，显示原文。

            else:
                if user_text.startswith("/"):
                    print("未知命令，请检查命令名称。")
                    print("未识别的命令：", repr(command))
                    continue

                # 普通文本进入问答。
                # 如果已完成两次问答，先重置历史和计数，并显示新会话提示。
                # 普通文本进入问答。
                if completed_turns >= max_session_turns:
                    history = new_conversation()
                    completed_turns = 0
                    print("已自动开始新会话")


                try:
                    result = ask_agent(user_text, history)

                except requests.exceptions.JSONDecodeError as error:
                    # 显示：模型响应不是有效 JSON，并显示 error。
                    # 然后回到下一次输入。
                    print("模型响应不是有效 JSON:",error)
                    continue

                except requests.exceptions.RequestException as error:
                    # 显示：模型请求失败，并显示 error。
                    # 然后回到下一次输入。
                    print("模型请求失败:",error)
                    continue

                except ValueError as error:
                    # 显示：模型响应或工具数据不符合要求，并显示 error。
                    # 然后回到下一次输入。
                    print("模型响应或工具数据不符合要求:",error)
                    continue

                if result["answer"] is None:
                    print("达到模型请求上限，本次未获得最终回答。")
                    continue
                history = result["history"]
                completed_turns += 1

                print(result["answer"])
                sources = result["sources"]
                if sources:
                    print("本轮实际读取资料：","、".join(sources))
                else:
                    print("本轮未读取新资料，请核对回答依据")
                filename = resolve_item(user_text)
                if filename is not None and is_familiar(filename):
                    print("该条目已在你的熟悉库中。")
            # 保存成功返回的历史，增加问答计数。
    # 显示回答、本轮来源，以及符合条件的熟悉提示。
        except (OSError, ValueError) as error:
            print("本次操作未全部完成，文件读写或数据异常：", error)
            continue

if __name__ == "__main__":
    main()

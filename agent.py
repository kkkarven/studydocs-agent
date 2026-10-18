import os
import requests
import json
from doc_tools import search_docs, read_doc

# 第一部分：准备本次调用使用的基本信息
url = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/chat")
model = os.environ.get("OLLAMA_MODEL", "qwen3.5:2b-q4_K_M")
system_prompt = """
工具调用规则：
- 回答前，先调用 search_docs 查找相关本地资料。同一轮可以请求多个 search_docs，每个调用只搜索一个简短主题。
- 每次调用的 key_word 填一个简短、具体的语法主题；language 填用户明确指定的语言，没有指定时填空字符串。
- 收到搜索结果后，先判断资料是否与问题相关、是否足以回答。资料足够时直接回答，不要重复搜索。
- 搜索结果为空或与问题无关时，可以调整关键词继续搜索。最多进行三轮工具处理；收到足够资料后直接回答。
- 搜索后仍没有相关资料时，明确说明“缺少本地资料依据，以下说明尚未核对”。可以提供简短说明，但不得编造资料、出处或版本。

回答要求：
- 简要说明语法或接口的用途和基本写法；涉及参数或返回值时，说明它们的作用。
- 给出一个变量和前提完整的短示例，并说明预期运行结果。
- 只有本地资料明确写出适用版本时，才说明该版本；资料没有写时，不要猜测或补造版本。
- 必要时指出一个与当前问题相关的易错点。回答保持简短，不扩展成完整教程。
- 本地资料的文件名由程序显示。不要自行编造文件名、行号或声称查阅了未返回的资料。
"""

tool_spec = {
    "type": "function",
    "function": {
        "name": "search_docs",
        "description": "在本地 Markdown 语法资料中搜索关键词，并按指定语言筛选。返回匹配行的来源文件名、行号和原文。搜索结果是匹配行列表，不是完整文件正文。",
        "parameters": {
            "type": "object",
            "properties": {
                "key_word": {
                    "type": "string",
                    "description": "一个适合原文匹配的短语法主题，例如 print、字典按键取值、int *a[]。不要把语言名称和完整问题拼成关键词。",
                },
                "language": {
                    "type": "string",
                    "description": "用户明确指定的语言名称：Python、C 或 C++。没有指定语言时传入空字符串，表示不限制语言。",
                },
            },
            "required": ["key_word", "language"],
        },
    },
}

# 第二部分：组织发给 Ollama 的请求体


def new_conversation():
    return [{"role": "system", "content": system_prompt}]

def request_model(request_body):
    max_attempts = 2

    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.post(
                url=url,
                json=request_body,
                timeout=(5, 60),
            )
        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
        ):
            if attempt == max_attempts:
                raise

            print("连接失败或超时，准备重试一次。")
            continue

        print("HTTP状态码：", response.status_code)
        response.raise_for_status()
        result = response.json()

        if not isinstance(result, dict):
            raise ValueError("模型响应必须是字典。")

        if not isinstance(result.get("message"), dict):
            raise ValueError("模型响应缺少 message 字典。")

        return result

def ask_agent(question, history):
    messages = history.copy()
    messages.append({
        "role": "user",
        "content": question,
    })

    request_body = {
        "model": model,
        "messages": messages,
        "tools": [tool_spec],
        "stream": False,
        "think": False,
        "options": {
            "num_ctx": 4096,
            "temperature": 0,
        },
    }

    max_rounds = 4
    all_source_names = []

    # 把原来的 for round_number ... 及工具处理代码放在这里。

    for round_number in range(1, max_rounds + 1):
        print("模型请求轮次：", round_number)
        result = request_model(request_body)
        message = result["message"]
        print("第%d轮模型消息："% round_number,message)
        tool_calls =  message.get("tool_calls",[])

        # A：发送请求，检查 HTTP 状态，解析响应。
        # 得到 message 字典，再取得 tool_calls 列表。

        request_body["messages"].append(message)

        if not tool_calls:
            # B：显示最终回答，以及 all_source_names 中的实际来源。
            answer = message.get("content", "")
            if not isinstance(answer, str) or not answer.strip():
                raise ValueError("模型结束响应，但没有回答内容。")
            if not all_source_names:
                answer = "未找到相关本地资料，本次不提供未经核对的语法解释。"
                message["content"] = answer
            return {
                "answer": answer,
                "sources": all_source_names,
                "history": messages,
            }

        if round_number == max_rounds:
            return {
                "answer": None,
                "sources": all_source_names,
                "history": history,
            }
        # C：沿用昨天的调用数量、工具名称、参数类型和空关键词检查。
        # 验证通过后执行 search_docs，得到 search_result。
        for call in tool_calls:
            function = call["function"]
            tool_name = function["name"]
            arguments = function["arguments"]

            # 填条件：工具名称不是允许执行的 search_docs 时，条件应为 True。
            if call["function"]["name"] != "search_docs":
                raise ValueError("模型请求了本轮不允许执行的工具。")

            # 填条件：arguments 不是字典时，条件应为 True。
            if not isinstance(call["function"]["arguments"],dict):
                raise ValueError("工具参数必须是字典。")

            key_word = arguments.get("key_word")
            language = arguments.get("language")

            # 填条件：key_word 或 language 不是字符串时，条件应为 True。
            if not isinstance(key_word,str) or not isinstance(language,str):
                raise ValueError("关键词和语言参数必须是字符串。")

            # 填条件：关键词去掉首尾空白后为空字符串时，条件应为 True。
            if key_word.strip() == "":
                raise ValueError("模型给出的搜索关键词为空。")

            search_result = search_docs(key_word, language)
            print("搜索结果：", search_result)


            source_names = []
            reference_documents = []

            # D：沿用昨天逐个收集文件、读取正文和去重的代码。
            # 把本轮 source_names 中的新文件名补充到 all_source_names。
            for item in search_result:
                # 从 item 中取得 "source"，保存到 source。
                source = item["source"]
                if source in source_names:
                    continue
                # 在这里判断：这个文件是否已经在 source_names 中。
                # 已经收集过，就跳过本次循环后面的读取工作。
                document = read_doc(source)
                # 调用 read_doc，传入 source，把返回字典保存到 document。
                document_text = "\n".join(document["lines"])
                # 从 document 中取得 "lines"。
                # 把这个字符串列表连接成正文字符串，保存到 document_text。
                reference_documents.append({
                    "source":source,
                    "text":document_text
                })
                # 向 reference_documents 添加一个字典：
                # "source" 保存文件名字符串。
                # "text" 保存完整正文字符串。
                source_names.append(source)
                # 向 source_names 添加本次收集的文件名。
            for  source in source_names:
                if source not in all_source_names:
                    all_source_names.append(source)
            print("当前调用读取的资料：", source_names)
            tool_content = json.dumps(
                reference_documents,
                ensure_ascii=False,
            )
            tool_message = {
                "role": "tool",
                "tool_name": tool_name,
                "content": tool_content,
            }
                    # 模型提供调用编号时，把结果关联到对应调用。
            if call.get("id"):
                tool_message["tool_call_id"] = call["id"]

            request_body["messages"].append(tool_message)

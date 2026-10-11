import requests
import json
from doc_tools import search_docs, read_doc

# 第一部分：准备本次调用使用的基本信息
url = "http://localhost:11434/api/chat"
model = "qwen3.5:2b-q4_K_M"
question = "请先搜索本地资料，再说明 Python 字典如何按键取值，并给出一个短示例和运行结果。"

system_prompt = """
你是本地语法学习助手。
回答语法问题前，先请求调用 search_docs 搜索本地资料。
key_word 只填写一个短的语法主题，不要填写完整问题。
language 填写用户明确指定的语言，例如 Python、C、C++；没有指定时填写空字符串。
尚未收到工具结果时，不要直接解释语法，也不要声称已经查阅资料。
收到资料后，针对当前问题简短回答：说明用途和基本写法，给一个完整的短示例及其运行结果，必要时补充一条易错点。
不要展开成教程，不要重复整篇资料。
资料不足时明确说明，不编造内容。
本次检索资料的文件名由程序显示，不需要你生成。
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
request_body = {
    "model":model,
    "messages":[{"role":"user","content":question}],
    "stream":False,"think":False,"options":{"num_ctx":4096}
    # 在这里组织 model、messages、stream、think 和 options
}
request_body["tools"] = [tool_spec]

request_body["messages"] = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": question},
]

request_body["options"]["temperature"] = 0

# 第三部分：发送请求
response = requests.post(url=url,json=request_body,timeout=60)
# 调用 requests.post，传入地址、请求体和超时设置。
# 用变量 response 保存它返回的 Response 对象。

print("HTTP状态码：",response.status_code)
print("原始响应文本：",response.text)
response.raise_for_status()
# 第四部分：检查 HTTP 响应
# 显示 HTTP 状态码和原始响应文本。
# 调用响应对象的方法，检查是否存在 HTTP 错误。

result  = response.json()
# 第五部分：解析响应数据
# 将响应中的 JSON 解析为 Python 数据。
# 用变量 result 保存解析结果。
message = result["message"]
print("第一轮模型消息：", message)

tool_calls = message.get("tool_calls", [])

# 填条件：tool_calls 中的调用数量不是 1 时，条件应为 True。
if len(tool_calls) != 1:
    raise ValueError("本轮练习需要恰好一个工具调用；请先检查第一轮模型消息。")

function = tool_calls[0]["function"]
tool_name = function["name"]
arguments = function["arguments"]

# 填条件：工具名称不是允许执行的 search_docs 时，条件应为 True。
if tool_calls[0]["function"]["name"] != "search_docs":
    raise ValueError("模型请求了本轮不允许执行的工具。")

# 填条件：arguments 不是字典时，条件应为 True。
if not isinstance(arguments, dict):
    raise ValueError("工具参数必须是字典。")

key_word = arguments.get("key_word")
language = arguments.get("language")

# 填条件：key_word 或 language 不是字符串时，条件应为 True。
if not isinstance(key_word, str) or not isinstance(language, str):
    raise ValueError("关键词和语言参数必须是字符串。")

# 填条件：关键词去掉首尾空白后为空字符串时，条件应为 True。
if key_word.strip() == "":
    raise ValueError("模型给出的搜索关键词为空。")

search_result = search_docs(key_word, language)
print("搜索结果：", search_result)

source_names = []       # 保存已经收集的文件名字符串。
reference_documents = []  # 保存准备交给模型的资料记录。

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

print("实际读取的资料：", source_names)
if len(reference_documents) == 0:
    raise ValueError("本地没有找到匹配资料，本轮不继续生成回答。")
print("收集的资料份数：", len(reference_documents))

tool_content = json.dumps(
    reference_documents,
    ensure_ascii=False,
)

request_body["messages"].append(message)

request_body["messages"].append({
    "role": "tool",
    "tool_name": tool_name,
    "content": tool_content,
})

second_request_body = {
    "model": model,
    "messages": request_body["messages"],
    "stream": False,
    "think": False,
    "options": request_body["options"],
}

second_response = requests.post(
    url=url,
    json=second_request_body,
    timeout=60,
)

second_response.raise_for_status()
second_result = second_response.json()
second_message = second_result["message"]
print("第二轮模型消息：", second_message)
if second_message.get("tool_calls", []):
    raise ValueError("第二轮仍请求调用工具；本轮练习到此停止，请检查模型消息。")

print("模型回答：", second_message["content"])
print("本次读取资料：", "、".join(source_names))

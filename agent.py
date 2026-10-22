import json
import requests 
from doc_tools import read_doc,search_docs
from model_client import model,request_model

MAX_ROUNDS = 4

system_prompt = """
你是本地编程学习资料助手。

工具使用规则：
- 回答前先调用 search_docs 搜索本地资料。
- 同一轮可以请求多个搜索，每个调用只搜索一个简短主题。
- key_word 使用适合原文匹配的短关键词，例如 print、字典按键取值。
- language 使用用户明确指定的语言；未指定时使用空字符串。
- 工具会返回匹配资料的完整正文。
- 资料足够时直接回答，不要重复搜索。
- 搜索结果为空时，可以调整关键词继续搜索。
- 最多进行三轮工具处理，随后给出最终回答。
- 没有相关本地资料时，说明未找到资料，不编造依据。

回答要求：
- 简要解释用途和基本写法。
- 给出一个变量、前提完整的短示例，并说明预期结果。
- 版本信息只能来自返回的资料。
- 必要时指出一个相关易错点。
- 文件来源由程序显示，不自行编造文件名或行号。
"""

tool_spec = {
    "type": "function",
    "function": {
        "name": "search_docs",
        "description": (
            "在本地 Markdown 资料中按关键词和语言搜索。"
            "程序会根据匹配结果读取并返回相关资料全文。"
        ),
        "parameters": {
            "type":"object",
            "properties": {
                "key_word":{
                    "type":"string",
                    "description":(
                        "简短语法主题，例如 print、字典按键取值、指针数组。"
                        "不要使用完整问题作为关键词。"
                    ),
                },
                "language":{
                    "type":"string",
                    "description":(
                        "用户明确指定的语言，例如 Python、C、C++。"
                        "未指定时使用空字符串。"
                    ),
                },
            },
            "required":["key_word","language"],
        },
    },
}

def new_conversation():
    return[{"role":"system","content":system_prompt}]

def execute_search(call):#模型请求形式检查
    if not isinstance(call,dict):
        raise ValueError("工具调用必须是字典。")
    function = call.get("function")
    if not isinstance(function,dict):
        raise ValueError("工具调用缺少 function 字典。")
    tool_name = function.get("name")
    arguments = function.get("arguments")
    if tool_name != "search_docs":
        raise ValueError("模型请求了不允许执行的工具。")
    if not isinstance(arguments,dict):
        raise ValueError("工具参数必须是字典")
    key_word = arguments.get("key_word")
    language = arguments.get("language")
    if not isinstance(key_word,str) or not isinstance(language,str):
        raise ValueError("关键词和语言必须是字符串。")
    if not key_word.strip():
        raise ValueError("模型给出的搜索关键词为空。")
    print(f"执行搜索：{key_word!r}，语言：{language!r}")
    matches = search_docs(key_word,language)

    terms = key_word.split()#严格提示词导致模型难以搜索到内容，需要拆分提示词进行部分匹配
    if not matches and len(terms) >1:
        print("完整关键词未匹配，分别搜索：", terms)

        seen = set()
        for term in terms:
            term_matches = search_docs(term,language)
            for item  in term_matches:
                identity = (item["source"],item["line_number"])
                if identity in seen:
                    continue
                seen.add(identity)
                matches.append(item)
    source_names = []
    refrence_documents = []
    for item in matches:
        source = item["source"]
        if source in source_names:
            continue
        document =  read_doc(source)
        refrence_documents.append({
            "source":source,
            "text":"\n".join(document["lines"]),#完整文章交还给模型
        })
        source_names.append(source)
    print("本次工具读取资料：",source_names)

    tool_message = {#工具交还模型结果
        "role":"tool",
        "tool_name":tool_name,
        "content":json.dumps(
            refrence_documents,
            ensure_ascii=False,
        ),
    }
    if call.get("id"):
        tool_message["tool_call_id"] = call["id"]
    return tool_message,source_names
def ask_agent(question,history):#处理一次问答，不等于响应一次，而是工具调用+回答
    messages = history.copy()
    messages.append({
        "role":"user",
        "content":question,
    })
    request_body = {
        "model":model,
        "messages":messages,
        "tools":[tool_spec],
        "stream":False,
        "think":False,
        "options":{
            "num_ctx":4096,
            "temperature":0,
        },
    }

    all_source_name = []

    for round_number in range(1,MAX_ROUNDS+1):#请求工具
        print(f"\n模型请求轮次：{round_number}")
        result = request_model(request_body)
        message = result["message"]
        print("响应字段：", list(message))
        print("工具调用：", repr(message.get("tool_calls")))
        print("回答内容：", repr(message.get("content")))
        tool_calls = message.get("tool_calls",[])
        if not isinstance(tool_calls,list):
            raise ValueError("tool_calls 必须是列表。")
        messages.append(message)
        if not tool_calls:
            answer = message.get("content","")
            if not isinstance(answer,str) or not answer.strip():
                raise ValueError("模型结束响应，但没有回答内容。")
            if not all_source_name:
                answer = "未找到相关本地资料，本次不提供未经核对的语法解释。"
                message["content"] = answer
            return {
                "answer":answer,
                "sources":all_source_name,
                "history": messages,
            }
        if round_number == MAX_ROUNDS:
             return{
                 "answer":None,
                 "sources":all_source_name,
                 "history":history,
             }
        for call in tool_calls:
            tool_message, source_names = execute_search(call)
            messages.append(tool_message)
            for source in source_names:
                if source in source_names:
                    if source not in all_source_name:
                        all_source_name.append(source)

def main():
    question = input("问题：").strip()
    if not question:
        return 0
    try:
        result = ask_agent(question,new_conversation())
    except(requests.exceptions.RequestException,ValueError,OSError) as error:
        print(f"本次回答失败：{type(error).__name__}:{error}")
        return 1
    if result["answer"] is None:
        print("达到模型请求上限，本次未获得最终回答。")
        return 1
    
    print("\n回答：")
    print(result["answer"])
    print("\n本轮实际读取资料：", "、".join(result["sources"]) or "无")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
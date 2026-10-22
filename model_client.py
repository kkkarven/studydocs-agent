import json
import os

import requests

url = os.environ.get(
    "OLLAMA_URL",
    "http://localhost:11434/api/chat"
)
model = os.environ.get(
    "OLLAMA_MODEL",
    "qwen3.5:2b-q4_K_M",
)

def request_model(request_body):#一次完整请求
    max_attempts = 2
    for attempt in range(1,max_attempts + 1):
        try:
            response = requests.post(
                url = url,
                json=request_body,
                timeout=(5,60)
            )
        except(
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
        ):
            if attempt == max_attempts:
                raise
            print("连接失败或超时，准备重试一次。")
            continue
        print("HTTP:",response.status_code)
        response.raise_for_status()
        result = response.json()
        if not isinstance(result,dict):
            raise ValueError("模型响应必须是字典。")
        if not isinstance(result.get("message"),dict):
            raise ValueError("模型响应缺少 message 字典。")
        return result

def main():
    question = "请用一句话解释 Python print() 的作用。"
    request_body = {
        "model":model,
        "messages":[
            {
                "role":"user",
                "content":question,
            }
        ],
        "stream":False,
        "think":False,
        "options":{
            "num_ctx":4096,
            "temperature":0,
        },
    }
    print("请求模型：",model)
    print("用户问题：",question)
    try:
        result = request_model(request_body)

        answer = result["message"].get("content")   
        if not isinstance(answer,str) or not answer.strip():
            raise ValueError("模型没有返回非空回答。")
    except requests.exceptions.JSONDecodeError as error:
        print("模型响应不是有效json：",error)
        return 1
    except requests.exceptions.RequestException as error:
        print("模型请求失败：",error)
        return 1
    except ValueError as error:
        print("模型响应结构不符合要求：",error)
        return 1
    print("原始响应:\n",json.dumps(result,ensure_ascii=False,indent=2))
    print("\n模型回答:\n",answer)
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
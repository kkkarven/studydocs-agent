import requests


# 第一部分：准备本次调用使用的基本信息
url = "http://localhost:11434/api/chat"
model = "qwen3.5:2b-q4_K_M"
question = "请解释pyhton中 printf 的作用。"


# 第二部分：组织发给 Ollama 的请求体
request_body = {
    "model":model,
    "messages":[{"role":"user","content":question}],
    "stream":False,"think":False,"options":{"num_ctx":4096}
    # 在这里组织 model、messages、stream、think 和 options
}


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

model_name = result["model"]
answer = result["message"]["content"]
is_done = result["done"]
print(model_name)
print(answer)
print(is_done)
# 第六部分：读取并显示结果
# 从 result 中读取模型名称、回答内容和完成标记。
"""运行记录支架：记录协议和调用包装由助手准备；两个存储函数由学习者完成。"""
import json
from datetime import datetime
from pathlib import Path
from time import perf_counter
from uuid import uuid4
from zoneinfo import ZoneInfo

import requests
import agent

PROJECT_DIR = Path(__file__).resolve().parent
LOG_FILE = PROJECT_DIR / "data" / "private" / "runs.jsonl"
EXPORT_DIR = PROJECT_DIR / "data" / "private" / "exports"


def make_record(question, result, elapsed_seconds, error=""):
    answer = result.get("answer") if result else None
    return {
        "id": uuid4().hex,
        "timestamp": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(),
        "model": agent.model,
        "question": question,
        "status": "error" if error else ("ok" if answer is not None else "limit"),
        "answer": answer,
        "sources": list(result.get("sources", [])) if result else [],
        "elapsed_seconds": round(elapsed_seconds, 4),
        "error": error,
    }


def append_run(record):
    """核心练习1：创建LOG_FILE.parent，以UTF-8追加一行JSON，末尾加换行。
    record为make_record返回的字典；不覆盖旧行，不把缩进JSON写成多行。
    """
    LOG_FILE.parent.mkdir(parents=True,exist_ok=True)
    text = json.dumps(record,ensure_ascii=False)
    with LOG_FILE.open("a",encoding="utf-8") as file:
        file.write(text + "\n")


def export_markdown(record):
    """核心练习2：只导出status=ok且有非空回答的记录。
    写入EXPORT_DIR / (record["id"] + ".md")，返回Path。
    正文包含问题、回答、来源、时间、模型和耗时；无来源要明确说明。
    """
    sources = record["sources"]
    if sources:
        source_text = "\n".join(f"- {source}" for source in sources)
    else:
        source_text = "本轮未读取新资料，回答依据需核对"

    timestamp = record["timestamp"]
    model = record["model"]
    elapsed = record["elapsed_seconds"]
    question = record["question"]
    answer = record["answer"]

    markdown = f"""# 学习记录

    - 时间：{timestamp}
    - 模型：{model}
    - 耗时：{elapsed} 秒

    ## 问题

    {question}

    ## 回答

    {answer}

    ## 来源

    {source_text}
    """
    if record["status"] != "ok" or not isinstance(record["answer"],str) or not record["answer"].strip():
        raise ValueError("无回答或回答有问题")
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = EXPORT_DIR / (record["id"] + ".md")
    path.write_text(markdown, encoding="utf-8")
    return path

def _append_without_hiding_answer(record):
    try:
        append_run(record)
    except OSError as error:
        print("运行记录保存失败，问答结果仍保留：", error)


def run_and_record(question, history):
    """复用原ask_agent；记录失败后继续向CLI抛原异常，不吞掉错误。"""
    started = perf_counter()
    try:
        result = agent.ask_agent(question, history)
    except (requests.exceptions.RequestException, ValueError, OSError) as error:
        record = make_record(
            question, None, perf_counter() - started,
            error=f"{type(error).__name__}: {error}",
        )
        _append_without_hiding_answer(record)
        raise
    record = make_record(question, result, perf_counter() - started)
    _append_without_hiding_answer(record)
    return {**result, "record": record}

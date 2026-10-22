import json
from datetime import datetime
from pathlib import Path
from time import perf_counter
from uuid import uuid4
from zoneinfo import ZoneInfo

import requests

import agent

PROJECT_DIR = Path(__file__).resolve().parent
LOG_FILE = PROJECT_DIR/"data"/"private"/"runs.jsonl"
EXPORT_DIR = PROJECT_DIR /"data"/"private"/"exports"

def make_record(question,result,elapsed_seconds,error = ""):
    answer = result.get("answer") if result else None

    if error:
        status = "error"
    elif answer is None:
        status = "limit"
    else:
        status = "ok"
    return {
        "id": uuid4().hex,
        "timestamp": datetime.now(
            ZoneInfo("Asia/Shanghai")
        ).isoformat(),
        "model": agent.model,
        "question": question,
        "status": status,
        "answer": answer,
        "sources": list(result.get("sources", [])) if result else [],
        "elapsed_seconds": round(elapsed_seconds, 4),
        "error": error,
    }
def append_run(record):
    LOG_FILE.parent.mkdir(parents=True,exist_ok=True)
    text = json.dumps(record,ensure_ascii=False)
    with LOG_FILE.open("a",encoding="utf-8") as file:
        file.write(text + "\n")

def export_markdown(record):
    answer = record.get("answer")
    if(
        record.get("status") != "ok"
        or not isinstance(answer,str)
        or not answer.strip()
    ):
        raise ValueError("只能导出具有非空回答的成功记录")
    if record["sources"]:
        source_text = "\n".join(
            f"-{source}" for source in record["sources"]
        )
    else:
        source_text = "本轮未读取新资料，回答依据需核对。"

    markdown = f"""# 学习记录

- 时间：{record["timestamp"]}
- 模型：{record["model"]}
- 耗时：{record["elapsed_seconds"]} 秒

## 问题

{record["question"]}

## 回答

{answer}

## 来源

{source_text}
"""
    EXPORT_DIR.mkdir(parents=True,exist_ok=True)
    path = EXPORT_DIR / (record["id"] + ".md")
    path.write_text(markdown,encoding = "utf-8")

    return path

def _append_without_hiding_answer(record):
    try:
        append_run(record)
    except OSError as error:
        print("运行记录保存失败，问答结果仍保留：", error)


def run_and_record(question,history):
    started = perf_counter()
    try:#即使出错也会保留记录
        result = agent.ask_agent(question,history)
    except(
        requests.exceptions.RequestException,
        ValueError,
        OSError,
    )as error:
        record = make_record(
            question,
            None,
            perf_counter() - started,
            error=f"{type(error).__name__}:{error}",
        )
        _append_without_hiding_answer(record)
        raise

    record = make_record(
        question,
        result,
        perf_counter() - started,
    )
    _append_without_hiding_answer(record)
    return {**result,"record":record}
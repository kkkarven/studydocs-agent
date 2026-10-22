import argparse
import contextlib
import io
import json
from datetime import datetime
from pathlib import Path
from string import ascii_letters, digits
from time import perf_counter
from zoneinfo import ZoneInfo

import agent
from doc_tools import read_doc, search_docs

PROJECT_DIR = Path(__file__).resolve().parent
CASES_FLIE = PROJECT_DIR / "eval_cases.json"
OUTPUT_DIR = PROJECT_DIR / "data" / "private" / "evaluation"

def build_baseline(case):
    started = perf_counter()
    matches = search_docs(case["keyword"],case["language"])

    names = []
    documents = []

    for item in matches:
        source = item["source"]
        if source in names:
            continue
        names.append(source)
        document = read_doc(source)
        documents.append("\n".join(document["lines"]))

    return{
        "method": "人工预设关键词检索并直接展示全文，无模型生成",
        "sources": names,
        "answer": "\n\n".join(documents) if documents else "缺少本地资料依据。",
        "elapsed_seconds": round(perf_counter() - started, 4),

    }
def evaluate_case(case,baseline_only=False):
    row = {
        "case": case,
        "timestamp": datetime.now(
            ZoneInfo("Asia/Shanghai")
        ).isoformat(),
        "model": agent.model,
        "baseline": build_baseline(case),
    }

    if baseline_only:
        return row
    debug = io.StringIO()
    started = perf_counter()
    try:
        with contextlib.redirect_stdout(debug):
            result = agent.ask_agent(
                case["question"],
                agent.new_conversation(),
            )
        row["agent"] = {
            "status":"ok" if result["answer"]is not None else "limit",
            "answer":result["answer"],
            "sources":result["sources"],
        }
    except Exception as error:
        row["agent"] ={
            "status": "error",
            "answer": None,
            "sources": [],
            "error": f"{type(error).__name__}: {error}",
        }
    row["agent"]["elapsed_seconds"] = round(
        perf_counter() - started,4
    )
    
    row["debug"] = debug.getvalue()

    return row

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True)
    parser.add_argument("--case", default="")
    parser.add_argument("--baseline-only", action="store_true")
    args = parser.parse_args()

    allowed = ascii_letters + digits +"_-"

    if not args.label or any(char not in allowed for char in args.label):
        parser.error("label 只能使用英文字母、数字、下划线或连字符。")

    cases = json.loads(CASES_FLIE.read_text(encoding="utf-8"))

    if args.case:
        cases = [case for case in cases if case["id"] == args.case]
        if not cases:
            parser.error("未知case id")
    output_dir = OUTPUT_DIR /args.label
    output_dir.mkdir(parents = True , exist_ok = True)

    for case in cases:
        path = output_dir / (case["id"] + ".json")
        if path.exists():
            print("已有结果，保留不覆盖：", path)
            continue
        row =  evaluate_case(case,args.baseline_only)

        path.write_text(
            json.dumps(row,ensure_ascii=False,indent=2),
            encoding = "utf-8"
        )
        print("已保存：",path,flush=True)
    print("请按 checks 人工核对；请求成功不代表回答正确。")

if __name__ == "__main__":
    main()
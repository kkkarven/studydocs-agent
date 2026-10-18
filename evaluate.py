"""公开开发回归集；保存原始输出供人工评价，不执行生成代码或自动认定语义正确。"""
import argparse
import contextlib
import io
import json
from datetime import datetime
from pathlib import Path
from time import perf_counter
import agent
from doc_tools import search_docs, read_doc

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True)
    parser.add_argument("--case", default="", help="只运行一个case id；空值运行全部")
    parser.add_argument("--baseline-only", action="store_true")
    args = parser.parse_args()
    if not args.label or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in args.label):
        parser.error("label只能使用字母数字下划线或连字符")
    output_dir = ROOT / "data/private/evaluation" / args.label
    output_dir.mkdir(parents=True, exist_ok=True)
    cases = json.loads((ROOT / "eval_cases.json").read_text(encoding="utf-8"))
    if args.case:
        cases = [case for case in cases if case["id"] == args.case]
        if not cases:
            parser.error("未知case id")
    for case in cases:
        path = output_dir / (case["id"] + ".json")
        if path.exists():
            print("已有结果，保留不覆盖：", path)
            continue
        started = perf_counter()
        matches = search_docs(case["keyword"], case["language"])
        names = list(dict.fromkeys(item["source"] for item in matches))
        baseline = {
            "method": "人工预设关键词检索并直接展示全文，无模型生成",
            "sources": names,
            "answer": "\n\n".join("\n".join(read_doc(name)["lines"]) for name in names)
                      if names else "缺少本地资料依据。",
            "elapsed_seconds": round(perf_counter() - started, 4),
        }
        row = {"case": case, "timestamp": datetime.now().astimezone().isoformat(),
               "model": agent.model, "baseline": baseline}
        if not args.baseline_only:
            debug = io.StringIO()
            started = perf_counter()
            try:
                with contextlib.redirect_stdout(debug):
                    result = agent.ask_agent(case["question"], agent.new_conversation())
                row["agent"] = {
                    "answer": result["answer"], "sources": result["sources"],
                    "status": "ok" if result["answer"] is not None else "limit",
                }
            except Exception as error:
                row["agent"] = {"status": "error", "error": f"{type(error).__name__}: {error}"}
            row["agent"]["elapsed_seconds"] = round(perf_counter() - started, 4)
            row["debug"] = debug.getvalue()
        path.write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding="utf-8")
        print("已保存：", path, flush=True)
    print("逐条核对checks；填写docs/evaluation-review.md，不能把请求成功当成答案正确。")


if __name__ == "__main__":
    main()

"""D9验收约定；核心函数及CLI接好前应失败，不能当作已完成功能。"""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import requests
import agent
import cli
import run_store as store


class Delivery(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.addCleanup(self.temporary.cleanup)
        for name, value in (
            ("LOG_FILE", self.root / "runs.jsonl"),
            ("EXPORT_DIR", self.root / "exports"),
        ):
            p = patch.object(store, name, value)
            p.start()
            self.addCleanup(p.stop)

    def record(self, sources=None):
        return store.make_record("问题：中文", {
            "answer": "回答内容", "sources": sources or []
        }, 0.125)

    def test_append_preserves_lines_and_chinese(self):
        first, second = self.record(), self.record()
        store.append_run(first)
        store.append_run(second)
        lines = store.LOG_FILE.read_text(encoding="utf-8").splitlines()
        self.assertEqual([json.loads(x) for x in lines], [first, second])
        self.assertIn("中文", lines[0])

    def test_export_contains_content_and_metadata(self):
        record = self.record(["python_print.md"])
        path = store.export_markdown(record)
        self.assertIsInstance(path, Path)
        self.assertEqual(path.parent, store.EXPORT_DIR)
        text = path.read_text(encoding="utf-8")
        for value in ("问题：中文", "回答内容", "python_print.md",
                      record["timestamp"], record["model"], "0.125"):
            self.assertIn(value, text)

    def test_export_no_sources_and_refuse_failure(self):
        record = self.record()
        text = store.export_markdown(record).read_text(encoding="utf-8")
        self.assertIn("本轮未读取", text)
        record.update(status="error", answer=None)
        with self.assertRaises(ValueError):
            store.export_markdown(record)

    def test_wrapper_logs_success_and_error(self):
        history = agent.new_conversation()
        with patch("run_store.agent.ask_agent", return_value={
            "answer": "回答内容", "sources": [], "history": history.copy()
        }):
            result = store.run_and_record("成功", history)
        self.assertEqual(result["record"]["status"], "ok")
        with patch("run_store.agent.ask_agent", side_effect=requests.exceptions.Timeout("模拟")):
            with self.assertRaises(requests.exceptions.Timeout):
                store.run_and_record("失败", history)
        records = [json.loads(x) for x in store.LOG_FILE.read_text().splitlines()]
        self.assertEqual([x["status"] for x in records], ["ok", "error"])
        self.assertIsNone(records[1]["answer"])

    def test_limit_is_logged_without_answer(self):
        history = agent.new_conversation()
        with patch("run_store.agent.ask_agent", return_value={"answer": None, "sources": [], "history": history}):
            result = store.run_and_record("达到上限", history)
        self.assertEqual(result["record"]["status"], "limit")
        self.assertIsNone(result["record"]["answer"])
        self.assertEqual(result["history"], history)
        logged = json.loads(store.LOG_FILE.read_text(encoding="utf-8"))
        self.assertEqual(logged["status"], "limit")

    def test_log_failure_preserves_answer(self):
        with patch("run_store.append_run", side_effect=PermissionError("模拟")), \
             patch("run_store.agent.ask_agent", return_value={
                 "answer": "保留回答", "sources": [], "history": []
             }), contextlib.redirect_stdout(io.StringIO()):
            result = store.run_and_record("问题", [])
        self.assertEqual(result["answer"], "保留回答")

    def test_no_evidence_answer_matches_saved_history(self):
        unsafe = "不应显示的无资料解释"
        with patch("agent.request_model", return_value={"message": {"role": "assistant", "content": unsafe}}), contextlib.redirect_stdout(io.StringIO()):
            result = agent.ask_agent("无资料问题", agent.new_conversation())
        self.assertIn("未找到相关本地资料", result["answer"])
        self.assertEqual(result["history"][-1]["content"], result["answer"])
        self.assertNotIn(unsafe, result["answer"])

    def test_cli_export_connection(self):
        record = self.record()
        output = io.StringIO()
        fake = {"answer": "回答内容", "sources": [], "history": [], "record": record}
        with patch("builtins.input", side_effect=["问题", "/导出", "/退出"]), \
             patch("cli.ask_agent", return_value=fake), \
             contextlib.redirect_stdout(output):
            cli.main()
        self.assertTrue(list(store.EXPORT_DIR.glob("*.md")), output.getvalue())


if __name__ == "__main__":
    unittest.main()

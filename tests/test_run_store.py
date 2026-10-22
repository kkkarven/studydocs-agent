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


class RunStoreTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)

        for name, value in [
            ("LOG_FILE", root / "runs.jsonl"),
            ("EXPORT_DIR", root / "exports"),
        ]:
            patcher = patch.object(store, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def make_record(self, sources=None):
        return store.make_record(
            "中文问题",
            {"answer": "模拟回答", "sources": sources or []},
            0.125,
        )

    def test_append_preserves_records(self):
        first = self.make_record()
        second = self.make_record()

        store.append_run(first)
        store.append_run(second)

        text = store.LOG_FILE.read_text(encoding="utf-8")
        records = [json.loads(line) for line in text.splitlines()]

        self.assertEqual(records, [first, second])
        self.assertIn("中文问题", text)

    def test_export_content_and_validation(self):
        record = self.make_record(["python_print.md"])
        path = store.export_markdown(record)
        text = path.read_text(encoding="utf-8")

        for value in [
            "中文问题",
            "模拟回答",
            "python_print.md",
            record["timestamp"],
            record["model"],
            "0.125",
        ]:
            self.assertIn(value, text)

        no_sources = self.make_record()
        path = store.export_markdown(no_sources)
        self.assertIn(
            "本轮未读取",
            path.read_text(encoding="utf-8"),
        )

        for status, answer in [
            ("limit", None),
            ("error", None),
            ("ok", "   "),
        ]:
            with self.subTest(status=status, answer=answer):
                with self.assertRaises(ValueError):
                    store.export_markdown({
                        **record,
                        "status": status,
                        "answer": answer,
                    })

    def test_success_and_limit_are_recorded(self):
        history = agent.new_conversation()

        with patch(
            "run_store.agent.ask_agent",
            side_effect=[
                {"answer": "完成", "sources": [], "history": history},
                {"answer": None, "sources": [], "history": history},
            ],
        ):
            success = store.run_and_record("成功问题", history)
            limit = store.run_and_record("上限问题", history)

        self.assertEqual(success["record"]["status"], "ok")
        self.assertEqual(limit["record"]["status"], "limit")

        records = [
            json.loads(line)
            for line in store.LOG_FILE.read_text(
                encoding="utf-8"
            ).splitlines()
        ]
        self.assertEqual(
            [record["status"] for record in records],
            ["ok", "limit"],
        )

    def test_error_is_recorded_and_raised(self):
        with patch(
            "run_store.agent.ask_agent",
            side_effect=requests.exceptions.Timeout("模拟超时"),
        ):
            with self.assertRaises(requests.exceptions.Timeout):
                store.run_and_record("失败问题", [])

        record = json.loads(
            store.LOG_FILE.read_text(encoding="utf-8")
        )

        self.assertEqual(record["status"], "error")
        self.assertIsNone(record["answer"])
        self.assertIn("模拟超时", record["error"])

    def test_log_failure_keeps_answer(self):
        with patch(
            "run_store.agent.ask_agent",
            return_value={
                "answer": "保留回答",
                "sources": [],
                "history": [],
            },
        ), patch(
            "run_store.append_run",
            side_effect=PermissionError("模拟日志写入失败"),
        ), contextlib.redirect_stdout(io.StringIO()):
            result = store.run_and_record("问题", [])

        self.assertEqual(result["answer"], "保留回答")

    def test_cli_export_connection(self):
        output = io.StringIO()

        with patch(
            "run_store.agent.ask_agent",
            return_value={
                "answer": "模拟回答",
                "sources": [],
                "history": [],
            },
        ), patch(
            "builtins.input",
            side_effect=["/导出", "测试问题", "/导出", "/退出"],
        ), contextlib.redirect_stdout(output):
            cli.main()

        self.assertIn("当前没有可导出", output.getvalue())
        self.assertEqual(
            len(list(store.EXPORT_DIR.glob("*.md"))), 1
        )
        self.assertTrue(store.LOG_FILE.exists())

    def test_cli_failure_keeps_last_success(self):
        with patch(
            "run_store.agent.ask_agent",
            side_effect=[
                {"answer": "成功回答", "sources": [], "history": []},
                requests.exceptions.Timeout("模拟失败"),
            ],
        ), patch(
            "builtins.input",
            side_effect=["成功问题", "失败问题", "/导出", "/退出"],
        ), contextlib.redirect_stdout(io.StringIO()):
            cli.main()

        exports = list(store.EXPORT_DIR.glob("*.md"))
        self.assertEqual(len(exports), 1)
        self.assertIn(
            "成功问题",
            exports[0].read_text(encoding="utf-8"),
        )


if __name__ == "__main__":
    unittest.main()
"""助手准备的隔离回归；不会连接模型或写入真实个人状态。"""
import contextlib
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import requests
import agent
import cli
import doc_tools
import familiar_store as familiar
import review_store as review
import check_review
import run_store


def response(payload=None, status=200, text=None):
    value = requests.Response()
    value.status_code = status
    value._content = (text if text is not None else json.dumps(payload)).encode()
    return value


def final_message(text="模拟回答"):
    return {"message": {"role": "assistant", "content": text}}


def tools(*keywords):
    return {"message": {"role": "assistant", "content": "", "tool_calls": [
        {"id": f"call_{i}", "function": {"name": "search_docs",
         "arguments": {"key_word": word, "language": "Python"}}}
        for i, word in enumerate(keywords)
    ]}}


class Documents(unittest.TestCase):
    def test_list(self):
        self.assertEqual(len(doc_tools.list_docs()), 3)

    def test_read(self):
        self.assertIn("print", "\n".join(doc_tools.read_doc("python_print.md")["lines"]))

    def test_reject_escape(self):
        with self.assertRaises(ValueError):
            doc_tools.read_doc("../private/familiar.json")

    def test_blank_keyword(self):
        with self.assertRaises(ValueError):
            doc_tools.search_docs(" ")

    def test_language(self):
        self.assertEqual(doc_tools.search_docs("print", "C++"), [])
        self.assertTrue(doc_tools.search_docs("print", "Python"))


class Familiar(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.state = Path(self.temporary.name) / "familiar.json"
        self.patcher = patch.object(familiar, "STATE_FILE", self.state)
        self.patcher.start()
        self.addCleanup(self.temporary.cleanup)
        self.addCleanup(self.patcher.stop)

    def test_empty(self):
        self.assertEqual(familiar.list_familiar(), [])

    def test_register_duplicate_and_remove(self):
        self.assertTrue(familiar.register_familiar("python_print.md"))
        self.assertFalse(familiar.register_familiar("python_print.md"))
        self.assertTrue(familiar.is_familiar("python_print.md"))
        self.assertTrue(familiar.unregister_familiar("python_print.md"))
        self.assertFalse(familiar.unregister_familiar("python_print.md"))
        self.assertEqual(familiar.list_familiar(), [])

    def test_unknown_rejected(self):
        with self.assertRaises(ValueError):
            familiar.register_familiar("unknown.md")

    def test_corrupt_not_replaced(self):
        self.state.write_text("{")
        with self.assertRaises(ValueError):
            familiar.list_familiar()
        self.assertEqual(self.state.read_text(), "{")

    def test_write_failure(self):
        with patch.object(Path, "write_text", side_effect=PermissionError("模拟")):
            with self.assertRaises(OSError):
                familiar.register_familiar("python_print.md")


class Review(unittest.TestCase):
    def test_existing_isolated_checker(self):
        with contextlib.redirect_stdout(io.StringIO()):
            check_review.main()


class Request(unittest.TestCase):
    def setUp(self):
        self.output = contextlib.redirect_stdout(io.StringIO())
        self.output.__enter__()
        self.addCleanup(self.output.__exit__, None, None, None)

    def test_success(self):
        with patch("agent.requests.post", return_value=response(final_message())) as post:
            self.assertEqual(agent.request_model({}), final_message())
            self.assertEqual(post.call_count, 1)

    def test_retry_then_success(self):
        with patch("agent.requests.post", side_effect=[
            requests.exceptions.Timeout("模拟"), response(final_message())
        ]) as post:
            agent.request_model({})
            self.assertEqual(post.call_count, 2)

    def test_timeout_and_connection_limit(self):
        for error_class in (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            with self.subTest(error_class=error_class), patch(
                "agent.requests.post", side_effect=error_class("模拟")
            ) as post:
                with self.assertRaises(error_class):
                    agent.request_model({})
                self.assertEqual(post.call_count, 2)

    def test_http_not_retried(self):
        with patch("agent.requests.post", return_value=response({}, status=503)) as post:
            with self.assertRaises(requests.exceptions.HTTPError):
                agent.request_model({})
            self.assertEqual(post.call_count, 1)

    def test_invalid_json(self):
        with patch("agent.requests.post", return_value=response(text="bad")):
            with self.assertRaises(requests.exceptions.JSONDecodeError):
                agent.request_model({})

    def test_missing_message(self):
        for payload in ({}, [], {"message": []}):
            with self.subTest(payload=payload), patch(
                "agent.requests.post", return_value=response(payload)
            ):
                with self.assertRaises(ValueError):
                    agent.request_model({})


class Loop(unittest.TestCase):
    def setUp(self):
        self.history = agent.new_conversation()
        self.original = copy.deepcopy(self.history)

    def test_multiple_tools_and_history(self):
        with patch("agent.request_model", side_effect=[
            tools("字典按键取值", "print"), final_message("完成")
        ]), contextlib.redirect_stdout(io.StringIO()):
            result = agent.ask_agent("测试", self.history)
        self.assertEqual(result["answer"], "完成")
        self.assertIn("python_print.md", result["sources"])
        self.assertEqual(sum(x["role"] == "tool" for x in result["history"]), 2)
        self.assertEqual(self.history, self.original)

    def test_limit_keeps_original_history(self):
        with patch("agent.request_model", return_value=tools("不存在主题")), \
             contextlib.redirect_stdout(io.StringIO()):
            result = agent.ask_agent("测试", self.history)
        self.assertIsNone(result["answer"])
        self.assertEqual(result["history"], self.original)
        self.assertEqual(self.history, self.original)

    def test_failure_keeps_history(self):
        with patch("agent.request_model", side_effect=ValueError("模拟")), \
             contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(ValueError):
                agent.ask_agent("测试", self.history)
        self.assertEqual(self.history, self.original)


class CLI(unittest.TestCase):
    def test_file_errors_do_not_exit(self):
        output = io.StringIO()
        with patch("builtins.input", side_effect=["/熟悉库", "/退出"]), \
             patch("cli.list_familiar", side_effect=OSError("模拟读取失败")), \
             contextlib.redirect_stdout(output):
            cli.main()
        self.assertIn("模拟读取失败", output.getvalue())

    def test_no_false_registration_success(self):
        output = io.StringIO()
        with patch("builtins.input", side_effect=["/登记 Python print", "/退出"]), \
             patch("cli.register_familiar", side_effect=PermissionError("模拟写入失败")), \
             contextlib.redirect_stdout(output):
            cli.main()
        self.assertNotIn("已登记：", output.getvalue())
        self.assertIn("模拟写入失败", output.getvalue())

    def test_failure_does_not_count(self):
        def ask(question, history):
            if question == "失败":
                raise requests.exceptions.Timeout("模拟")
            result = {"answer": "完成", "sources": [], "history": history.copy()}
            result["record"] = run_store.make_record(question, result, 0.0)
            return result
        with patch("builtins.input", side_effect=["失败", "一", "二", "/退出"]), \
             patch("cli.ask_agent", side_effect=ask), \
             patch("cli.new_conversation", wraps=agent.new_conversation) as new, \
             contextlib.redirect_stdout(io.StringIO()):
            cli.main()
        self.assertEqual(new.call_count, 1)


if __name__ == "__main__":
    unittest.main()

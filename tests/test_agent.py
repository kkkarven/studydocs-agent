import copy
import unittest
from unittest.mock import patch

import agent

def tool_reply(*keywords):
    return {
        "message": {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": f"call_{index}",
                    "function": {
                        "name": "search_docs",
                        "arguments": {
                            "key_word": keyword,
                            "language": "Python",
                        },
                    },
                }
                for index, keyword in enumerate(keywords)
            ],
        }
    }

def final_reply(text):
    return {
        "message": {
            "role": "assistant",
            "content": text,
        }
    }


class AgentTests(unittest.TestCase):
    def test_multiple_calls_and_history(self):
        history = agent.new_conversation()
        original = copy.deepcopy(history)

        with patch(
            "agent.request_model",
            side_effect=[
                tool_reply("字典按键取值", "print"),
                final_reply("模拟最终回答"),
            ],
        ):
            result = agent.ask_agent("测试问题", history)

        self.assertEqual(result["answer"], "模拟最终回答")
        self.assertEqual(history, original)
        self.assertIn("python_dict_lookup.md", result["sources"])
        self.assertIn("python_print.md", result["sources"])

        self.assertEqual(
            [message["role"] for message in result["history"]],
            ["system", "user", "assistant", "tool", "tool", "assistant"],
        )

        tool_messages = [
            message
            for message in result["history"]
            if message["role"] == "tool"
        ]
        self.assertEqual(
            [message["tool_call_id"] for message in tool_messages],
            ["call_0", "call_1"],
        )
    def test_limit_stops_before_last_tools(self):
        history = agent.new_conversation()
        original = copy.deepcopy(history)

        with patch(
            "agent.request_model",
            side_effect=[
                tool_reply("print")
                for _ in range(agent.MAX_ROUNDS)
            ],
        ) as request, patch(
            "agent.execute_search",
            wraps=agent.execute_search,
        ) as execute:
            result = agent.ask_agent("测试问题", history)

        self.assertIsNone(result["answer"])
        self.assertEqual(request.call_count, agent.MAX_ROUNDS)
        self.assertEqual(execute.call_count, agent.MAX_ROUNDS - 1)
        self.assertEqual(result["history"], original)
        self.assertEqual(history, original)

    def test_empty_search_returns_no_source_message(self):
        with patch(
            "agent.request_model",
            side_effect=[
                tool_reply("不存在的关键词_xyz"),
                final_reply("模拟模型自行给出的解释"),
            ],
        ):
            result = agent.ask_agent("测试问题", agent.new_conversation())

        self.assertEqual(result["sources"], [])
        self.assertEqual(
            result["answer"],
            "未找到相关本地资料，本次不提供未经核对的语法解释。",
        )

    def test_failure_keeps_original_history(self):
        history = agent.new_conversation()
        original = copy.deepcopy(history)

        with patch(
            "agent.request_model",
            side_effect=ValueError("模拟响应错误"),
        ):
            with self.assertRaises(ValueError):
                agent.ask_agent("测试问题", history)

        self.assertEqual(history, original)

    def test_unknown_tool_is_rejected(self):
        call = {
            "function": {
                "name": "delete_file",
                "arguments": {},
            }
        }

        with self.assertRaises(ValueError):
            agent.execute_search(call)


if __name__ == "__main__":
    unittest.main()
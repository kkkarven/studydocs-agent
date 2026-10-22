import unittest

from doc_tools import list_docs, read_doc, search_docs

class DocumentToolsTests(unittest.TestCase):
    def test_list_docs(self):#listdocs列表检查
        self.assertEqual(
            list_docs(),
            [
                "c_pointer_array.md",
                "python_dict_lookup.md",
                "python_print.md",
            ],
        )
    def test_read_doc(self):#readdoc返回形式检查
        document = read_doc("python_print.md")

        self.assertEqual(document["source"], "python_print.md")
        self.assertIsInstance(document["lines"], list)
        self.assertIn("print", "\n".join(document["lines"]))
    def test_search_ignores_case(self):#返回搜索，检查遗漏
        results = search_docs(" PRINT ", " PYTHON ")

        self.assertTrue(results)
        self.assertIn(
            "python_print.md",
            [item["source"] for item in results],
        )

        for item in results:
            self.assertGreaterEqual(item["line_number"], 1)
            self.assertIn("print", item["text"].lower())

    def test_language_filter(self):
        self.assertEqual(search_docs("print", "C++"), [])

        results = search_docs("指针数组", "C")

        self.assertTrue(results)
        self.assertEqual(
            {item["source"] for item in results},
            {"c_pointer_array.md"},
        )
    def test_unknown_keyword(self):
        self.assertEqual(search_docs("不存在的关键词_xyz"), [])

    def test_reject_blank_keyword(self):
        with self.assertRaises(ValueError):
            search_docs("   ")

    def test_reject_invalid_types(self):
        with self.assertRaises(ValueError):
            search_docs(None)

        with self.assertRaises(ValueError):
            search_docs("print", None)

    def test_reject_path_escape(self):
        with self.assertRaises(ValueError):
            read_doc("../private/familiar.json")


if __name__ == "__main__":
    unittest.main()
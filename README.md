# studydocs-agent

面向个人编程学习的语法解答与复习 Agent。规划支持 C、C++、Python 及常用 Python 库的用法与示例、个人 Markdown 资料检索、显式熟悉登记、熟悉条目提示和每日随机复习。

当前处于开发阶段，上述首版功能尚待实现。

- [首版需求与范围](docs/project-scope.md)

继续采用 Ollama 本地模型，DeepSeek API 保留为后备。计划包含测试、评价、文档与独立复现说明。

## 资料搜索检查

在项目根目录运行：

```bash
python check_search.py
```

先输入关键词，再输入语言（如 `Python` 或 `C`）；语言留空表示不限。输入 `q` 退出。空关键词会主动抛出 `ValueError`，请不要直接回车。

搜索结果包含资料文件名、原文行号和原文内容。检索词用于定位候选资料，便于查看与核对相关内容。

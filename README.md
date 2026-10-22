# StudyDocs Agent

面向个人编程学习的本地资料问答与复习助手。模型通过工具检索 Markdown 资料，程序读取正文并回传，随后显示回答和实际读取的来源。

当前版本是重新搭建的学习实验实现，覆盖资料问答、熟悉库、每日复习、运行日志、Markdown 导出和固定题集评测。已接入的资料只有 Python print、Python 字典按键取值和 C 指针数组。

**读取到正确资料仍可能生成错误解释。当前项目用于学习与实验，模型回答需要核对。**

## 快速开始

目标平台为 Linux / WSL Ubuntu；CLI 使用 readline。当前开发与检查环境为 Python 3.14.4，依赖为 requests 2.34.2。原生 Windows 未验证。

先准备 Git、Python 和已安装的 Ollama，然后执行：

```bash
git clone https://github.com/kkkarven/studydocs-agent.git
cd studydocs-agent

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

确认 Ollama 服务可用并准备默认模型：

```bash
ollama list
ollama pull qwen3.5:2b-q4_K_M
```

如果服务尚未启动，在另一个终端执行并保持运行：

```bash
ollama serve
```

回到项目终端启动：

```bash
python cli.py
```

如果已经位于本地重建目录，直接在该目录激活虚拟环境并运行，无需再次克隆。

## 使用

普通文本进入问答，例如：

```text
> Python 字典如何按键取值？键不存在时怎么办？
> C 指针数组 int *a[] 是什么意思？
```

程序会显示工具执行过程、最终回答和本轮实际读取的文件。若读取的资料已登记熟悉，会提示对应条目。

| 命令 | 作用 |
| --- | --- |
| `/登记 Python print` | 登记熟悉；重复登记不增加重复条目 |
| `/熟悉库` | 查看已登记条目 |
| `/取消登记 Python print` | 撤销登记，保留资料文件 |
| `/复习` | 获取或恢复当天最多三条复习内容 |
| `/查看 Python print` | 直接显示资料原文，不调用模型 |
| `/新会话` | 清空模型会话历史 |
| `/导出` | 导出本次程序运行中最近一次成功回答 |
| `/退出` | 退出程序 |

可识别的条目名称：

- Python print / Python 打印
- Python 字典按键取值
- C 指针数组

条目名称匹配忽略大小写和空白，例如 `C指针数组` 与 `C 指针数组` 均可识别。命令与参数之间仍需要空格，例如 `/登记 C指针数组`。名称表不负责理解任意自然语言同义表达。

### 会话与复习规则

- 每个会话最多累计两次获得最终回答的问答，下一次普通提问前自动开启新会话；本地命令不计数。
- `/新会话` 不删除熟悉库、复习记录或最近可导出的成功记录。
- 每日复习按 Asia/Shanghai 日期，首次有候选时随机抽取最多三条；同日恢复原顺序。
- 撤销条目后，下次 `/复习` 会移除该条目，不补抽；当日复习组生成后的新增条目下一天参与抽取。
- 首次空库不保存抽取记录，因此当天登记条目后仍可生成复习组。

## 配置

通过环境变量覆盖模型地址和名称：

```bash
export OLLAMA_URL=http://localhost:11434/api/chat
export OLLAMA_MODEL=qwen3.5:2b-q4_K_M
python cli.py
```

以上也是默认值。程序不自动读取 .env 文件。

每次问答最多进行四轮模型交互；单轮连接失败或超时最多尝试两次。HTTP 错误、JSON 解析失败和响应结构错误会向上抛出，由 CLI 提示后继续接收输入。

请求使用 `timeout=(5, 60)`，分别限制连接与读取等待，不是整次问答的总时限。达到四轮上限和网络超时是不同的失败原因。

## 架构

```text
用户输入
  ↓
cli.py：命令分流、会话管理
  ↓
run_store.py：计时和运行记录
  ↓
agent.py：模型请求、工具执行、停止判断
  ├── model_client.py：向 Ollama 发送 HTTP 请求
  └── doc_tools.py：搜索并读取本地资料
  ↓
回答、实际来源、更新后的历史
  ↓
CLI 显示结果；按需导出 Markdown
```

模型生成工具调用请求，实际函数由 Python 检查参数后执行。同一轮可以处理多个工具调用，并逐个回传工具结果。

检索先按完整关键词做忽略大小写的文本包含匹配。完整搜索无结果，且查询包含多个空白分隔的词时，再分别搜索这些词、合并匹配行并去重。程序随后按来源文件去重，读取全文供模型使用。它目前不是向量检索。

```text
studydocs-agent/
├── cli.py                  # 交互入口与命令分流
├── agent.py                # 工具调用循环
├── model_client.py         # HTTP 请求、超时与连接重试
├── doc_tools.py            # 资料列表、读取与文字检索
├── familiar_store.py       # 熟悉库持久化
├── review_store.py         # 当日复习组
├── run_store.py            # 运行日志与 Markdown 导出
├── evaluate.py             # 固定题集执行与结果保存
├── eval_cases.json         # 六道开发回归题
├── data/reference/         # 随项目提供的 Markdown 资料
├── data/private/           # 运行后产生，Git 忽略
├── tests/                  # 离线检查
├── docs/                   # 排查与修改记录
├── requirements.txt
└── LICENSE
```

## 运行记录与导出

CLI 问答会记录问题、时间、模型、最终回答、实际来源、耗时和错误。日志格式为 JSONL，每行一条 JSON，不覆盖之前的记录。

| 状态 | 含义 |
| --- | --- |
| `ok` | 获得最终回答，包括程序生成的无来源拒答；不代表内容正确 |
| `limit` | 达到模型交互轮次上限，没有最终回答 |
| `error` | 发生已处理的请求、数据或文件错误 |

日志保存失败时会提示，已经获得的回答仍然保留。问答失败或达到上限后，之前最近一次成功回答仍可导出。程序重启后，暂不支持选择历史日志中的记录导出。

| 本地路径 | 内容 |
| --- | --- |
| `data/private/familiar.json` | 熟悉条目 |
| `data/private/daily_review.json` | 当日复习组 |
| `data/private/runs.jsonl` | CLI 问答运行记录 |
| `data/private/exports/` | 导出的 Markdown |
| `data/private/evaluation/<label>/` | 固定题集的原始结果与调试输出 |

这些个人数据默认被 Git 忽略；本地日志仍会保存完整问题和回答。

## 检查与评测

### 离线检查

在项目根目录执行：

```bash
python -m unittest discover -s tests -v
```

当前包含资料工具、Agent 循环、熟悉库、复习、日志和 CLI 导出连接的检查，使用模拟模型响应及临时状态目录。2026-10-22 已运行的 26 项检查通过；这不等于所有模型回答正确。

### 真实模型评测

先生成人工预设关键词的检索参照，不调用模型：

```bash
python evaluate.py --label baseline --baseline-only
```

再执行 Agent，可先跑单题，再补齐其余题目：

```bash
python evaluate.py --label rebuild_v1 --case c_pointer
python evaluate.py --label rebuild_v1
```

可选题目 ID：`print`、`dict`、`c_pointer`、`missing`、`cpp_missing`、`version`。

结果保存在 `data/private/evaluation/<label>/<case>.json`。同一标签下已有文件会跳过；修改代码或配置后，使用新标签重跑，例如 `rebuild_v2`。仅生成参照与运行 Agent 应使用不同标签。

每份完整结果包含：

| 字段 | 含义 |
| --- | --- |
| `case` | 问题和人工检查标准 |
| `baseline` | 人工预设关键词找到的资料原文，不经过模型生成 |
| `agent` | Agent 实际返回的状态、回答、来源和耗时 |
| `debug` | 模型响应、工具参数和搜索过程 |

`baseline.method` 中“无模型生成”描述的是参照组，不是 Agent。参照组有来源也不代表 Agent 找到了相同文件，应检查 `agent.sources` 和 `debug`。

评测不自动执行生成代码，也不自动判定语义正确。按题目的 checks 分别核对检索、解释、示例、输出和依据是否一致。这六题是公开开发回归集，不能代替独立泛化评测。

## 已知限制

- 当前只有三份资料，未覆盖的语言或主题不能保证回答。Agent 本轮没有读取到资料时，程序会将最终回答替换为固定拒答；也可能在模型继续请求工具时达到轮次上限。
- 拆词回退会合并任一词的匹配，可能同时读取不相关文件；读取来源不等于证明答案有依据。
- 模型可能在读取正确原文后仍生成错误的类型解释、示例或版本结论，实际使用前需要核对。
- 熟悉库是用户显式登记的状态，不是程序对掌握程度的自动判断；复习由命令触发，没有后台提醒。
- 当前没有 Web 界面、向量数据库或自动代码执行；状态文件没有原子写入与损坏自动恢复保证。

## 修改记录

- [多关键词检索与评测结果排查](docs/多关键词检索与评测结果排查记录_2026-10-22.md)
- [熟悉提示未触发诊断](docs/熟悉提示未触发_诊断记录_2026-10-22.md)

## 许可证

采用 [MIT License](LICENSE)。本地资料中的外部参考文档权利归其原作者。

# studydocs-agent

面向个人编程学习的本地资料问答与复习助手。当前资料只有Python print、字典按键取值和C指针数组；不承诺完整语言或库覆盖。

**收尾状态：v0.1学习实验候选。日志/导出已接入，离线与新venv检查已有通过证据；六题真实模型复评未通过答案可靠性验收。C示例有已确认类型错误，部分问题到上限或问非所答。合并、CI和发布状态见发布检查清单。**

## 环境与安装

已用环境：WSL Ubuntu、Python 3.14.4、requests 2.34.2、Ollama模型 qwen3.5:2b-q4_K_M。
CLI使用readline；当前支持目标为Linux/WSL，原生Windows未验证。

```bash
git clone https://github.com/kkkarven/studydocs-agent.git
cd studydocs-agent
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

安装并启动Ollama后，准备模型：

```bash
ollama pull qwen3.5:2b-q4_K_M
python cli.py
```

可选环境变量（不需要.env文件；程序不自动读取.env）：

```bash
export OLLAMA_URL=http://localhost:11434/api/chat
export OLLAMA_MODEL=qwen3.5:2b-q4_K_M
```

默认值与以上相同。顶层依赖固定在requirements.txt；传递依赖尚未完整锁定。

## 使用

普通文本进入问答。名称忽略大小写，内部连续空白统一；可识别Python print、Python 打印、Python 字典按键取值、C 指针数组。

| 命令 | 行为 |
| --- | --- |
| /登记 Python print | 显式登记熟悉；重复登记不重复 |
| /熟悉库 | 显示已登记文件名 |
| /取消登记 Python print | 撤销熟悉状态，保留资料 |
| /复习 | 恢复当日最多三条复习组 |
| /查看 Python print | 查看资料原文 |
| /新会话 | 重置模型会话 |
| /导出 | 完成接入后，导出本次程序最近一次成功回答 |
| /退出 | 退出 |

熟悉提示只对能明确匹配名称表的输入触发，不理解任意自然语言同义表达。
最多保留两次成功问答，下一次自动重置；本地命令不计数。
每次问答最多四轮模型交互，每轮连接失败/超时最多尝试两次。
timeout=(5,60)为连接与读取等待，不是整个请求总时限。
已处理的请求、文件或数据错误提示后回到输入；不承诺所有深层响应错误均已覆盖。

每日复习按Asia/Shanghai日期：首次有候选时抽取最多三条，同日复用顺序；
撤销后再次/复习会移除条目、不补抽，新增下一日参与。首次空库不占用首次抽取；
已抽过后撤销成空组，当天重新登记仍不补抽。

## 记录与隐私

日志协议为每行一条JSON，保存时间、模型、问题、状态、回答、来源、耗时与错误。
成功、请求上限和已处理的失败分别记录；失败不伪造回答。日志写入失败不丢弃已获得的回答。
导出为Markdown；失败后保留之前最近的成功记录；重启程序后尚不支持选择旧记录导出。

个人状态、日志、导出及原始模型评价均位于data/private/并被Git忽略。
docs/private/、docs/learning-plan.md也被忽略。状态写入不具备原子更新与自动修复保证。

## 检查与评价

```bash
python -m unittest discover -s tests -v
python check_review.py
python evaluate.py --label before
python evaluate.py --label after
python check_release.py
```

离线检查不调用模型，使用临时状态与模拟响应。不要将check_familiar.py纳入批量回归：
它是旧手动脚本，会操作真实熟悉库。check_search.py为交互式检索入口。

真实评价需Ollama；原始结果保存在data/private/evaluation/，不自动执行生成的代码。
填写[评价表](docs/evaluation-review.md)，区分语义、示例、引用和耗时。
题集是公开开发回归集，不是独立泛化测试；基线使用人工预设关键词，比较边界见评价表。

check_release.py将公开交付文件复制到临时目录，创建新venv安装依赖并检查启动；
安装需要网络。它验证工程复现，不证明学习者独立复现能力；真实模型需单独检查。

## 已知限制与交付

无来源时固定说明已接入并完成前后评价，只限制这一类最终输出；并未解决模型的全部回答质量问题。有资料的模型回答仍需核对，实际读取文件也不等于答案必然有依据。
库筛选、通用条目解析、资料规模、DeepSeek后备接入尚未完成；后备目前不是可用运行选项。
项目没有向量检索、后台提醒、自动掌握评分、自动执行代码或Web界面。

- [首版原始范围](docs/project-scope.md)：历史需求，完成状态以实际验收与限制为准
- [Agent循环](docs/agent-loop-checks.md)
- [熟悉状态](docs/familiar-store-checks.md)
- [CLI与复习](docs/cli-review-checks.md)
- [失败恢复](docs/request-recovery-checks.md)
- [今天收尾步骤](docs/closeout-guide.md)
- [发布检查清单](docs/release-checklist.md)
- [贡献说明](CONTRIBUTING.md)

许可证采用MIT，见LICENSE。引用的外部文档权利归其原作者；本地短笔记保留参考出处。

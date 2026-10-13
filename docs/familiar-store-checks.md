# D6：熟悉状态与提示验收

日期：2026-10-13。功能范围：准确资料文件名作为条目标识，显式登记、列表查询、熟悉查询、撤销、本地 JSON 持久化及回答末尾提示。
当前条目对应三个资料文件：python_print.md、python_dict_lookup.md、c_pointer_array.md。
命令行产品命令与自然语言条目解析尚未实现；check_tool_call.py 使用显式 question_item。

## 数据与接口

真实状态文件：data/private/familiar.json。
数据格式：`{"familiar": ["python_print.md"]}`，空库为 `{"familiar": []}`。
register_familiar：新登记 True，重复登记 False。
unregister_familiar：成功撤销 True，未登记 False。
list_familiar：返回文件名列表。
is_familiar：返回是否登记的布尔值。
文件名不在 list_docs 清单中时，登记、撤销与熟悉查询均抛出 ValueError。
撤销只移除熟悉标记，不删除参考资料。模型不负责修改熟悉状态。

## 实践与修正

学习者亲手编写四个业务函数、检查脚本和回答提示接入；文件读写采用助手提供的参考实现。
撤销初稿误写为“filename in familiar 时返回 False”，导致已登记条目无法删除。
依据实际源码定位后，助手给出第 70 行改为“filename not in familiar”的局部修正及解释，学习者修改后报告检查正确。
使用参考代码和局部提示完成，不作为独立掌握证据。

## 已观察结果

| 检查 | 结果与证据 |
| --- | --- |
| 登记条目后的回答提示 | 用户原始终端输出显示完整 print 回答及熟悉提示 |
| 撤销后的提示消失 | 用户按集中复查反馈“这次对了”；助手只读确认真实 JSON 为空、查询 print 为 False |
| 私人状态不上传 | git check-ignore 返回 data/private/familiar.json |
| 不存在的条目 | 助手检查登记、撤销、查询均抛出 ValueError，前后真实状态文件字节相同 |
| 首次登记与重复登记 | 助手临时状态文件检查：True、False，列表只保留一项 |
| 登记后的查询 | 临时检查 print 为 True，未登记的字典条目为 False |
| 新进程恢复 | 独立 Python 子进程读取同一临时 JSON，仍得到 print 的登记记录 |
| 首次及重复撤销 | 临时检查 True、False，列表恢复为空，print 查询为 False |
| 初始文件不存在 | 临时检查 load_state 返回空库，无需预先手写 JSON |

临时检查仅在检查进程内指定临时 STATE_FILE，未修改真实熟悉记录、核心代码或调用模型，也未新增自动测试文件。
独立进程恢复结果确认文件持久化，不与同进程变量保留混淆。
提示集成修正后的通过按用户报告记录，未伪造新的模型日志。

## 复现入口

在项目目录启用虚拟环境后运行 `python check_familiar.py`。该脚本会登记 print，重复运行时首次登记也可能返回 False，不代表故障；初始状态不同，预期结果随之不同。
使用 `python -c 'from familiar_store import list_familiar; print(list_familiar())'` 可在新进程查询。
使用 `python -c 'from familiar_store import unregister_familiar, list_familiar; print(unregister_familiar("python_print.md")); print(unregister_familiar("python_print.md")); print(list_familiar())'` 撤销，已登记时预期 True、False、[]。
撤销后检查回答提示时，不要先运行会重新登记的 check_familiar.py。

## 范围限制与后续

本日基础状态功能按上述范围通过；理解、独立复现与迁移另行验证。
通用语义匹配、多个提问条目的识别、CLI 命令和每日复习留到后续；当前查询条目由用户显式填写，不能把所有检索文件当作提问条目。
完整异常处理、写入失败恢复与系统自动测试按后续日程安排。
D5 的 groupby 内容错误、未访问来源声称和版本展示等质量问题继续保留，不因 D6 通过而消失。
Git 上传、PR 合并与本地同步待实际结果确认。

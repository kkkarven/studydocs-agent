# 固定开发题集评价

状态：2026-10-18六题before/after均已实际采集并由助手初核；真实回答可靠性验收未通过。before使用D8业务实现及新增环境配置入口，尚未加无资料保护；模型qwen3.5:2b-q4_K_M。原始调试与基线保留在私人目录。初核未执行生成代码，不代替用户判断或独立评测。

运行前后对照：
```bash
python evaluate.py --label before
# 完成一项有证据的修正后
python evaluate.py --label after
```

结果在 data/private/evaluation/，保留原始回答、实际来源、耗时、错误与模型诊断。
公开评测问题位于 eval_cases.json，是开发回归集，不是独立未见测试集。
简单基线使用人工预设关键词并直接展示全文；它没有生成回答，关键词也优于一般自然语言输入。
因此只比较能找到哪些依据、输出正确性及使用体验，不据此声称Agent整体优于检索。

每条按正确性、示例输出、依据/版本标注分别写通过/失败/不适用，并写证据。
不知道如何核对的项写待核对；不自动执行模型生成代码。

| case | before判断及证据 | after判断及证据 | baseline观察 | 原始记录及耗时 |
| --- | --- | --- | --- | --- |
| print | sources为空仍声称依据标准文档，示例与返回值说明错误 | 无依据输出约束通过：固定说明且历史同步；原问题未解决，已有笔记仍未取到 | 关键词基线找到print与字典两份；print原笔记缺返回值说明 | before/print.json 13.3968秒；after/print.json 12.3188秒 |
| dict | 初核符合：KeyError、get默认值、90/0和字典来源；示例未另行运行 | 退化：sources为空，status=limit，answer=null | 找到字典笔记 | before/dict.json 4.4778秒；after/dict.json 2.8748秒 |
| c_pointer | 到上限，无来源或回答 | 失败：取到C笔记，但示例把int(*)[2]赋给int*；人工选取片段仅编译诊断，返回码1；说明混淆下标与解引用 | 能直接展示已核对的C笔记 | before/c_pointer.json 2.7263秒；after/c_pointer.json 9.4473秒；c_pointer_compile.json |
| missing | 到上限，无最终回答；本次未输出错误groupby示例 | 仍未完成：status=limit，answer=null，sources为空 | 无资料，明确说明 | before/missing.json 61.3294秒；after/missing.json 2.5962秒 |
| cpp_missing | 无来源仍输出不可靠规则和错误示例 | 不再输出该错误示例，但达到上限、无最终回答，不能记为成功完成 | 无资料，明确说明 | before/cpp_missing.json 6.5467秒；after/cpp_missing.json 2.5661秒 |
| version | 解释语法，未明确回答版本未注明 | 仍未满足问题：有C笔记来源，但未回答资料没有明确标准版本；示例未另行编译 | 可直接核对适用范围未标具体标准版本 | before/version.json 4.9375秒；after/version.json 5.328秒 |

拟优先研究D5已有证据的无资料编造问题。没有来源时程序固定返回说明，可以作为缩小回答范围的修正；
仍不能保证有资料的回答全部正确。若修改对既有场景有退化，应在表中保留。

## 复评结论

无来源最终说明的保护生效，但不能宣称整体回答质量提升。dict出现单次退化，有资料的C回答仍有错误，版本遵循不足。before/after为各一次公开开发样本；模型工具选择存在变化，不能把所有变化归因为代码，也不能把单次耗时差当性能提升。

C示例经人工查看后，使用gcc -std=c11 -Wall -Wextra -Werror -fsyntax-only做编译诊断，不执行代码。诊断：assignment to int* from incompatible pointer type int(*)[2]，对应p=&arr。原始诊断保存在私人评价目录。

可发布的是明确标注限制的学习实验预发布版本；程序流程通过与模型答案可靠性必须分别陈述。

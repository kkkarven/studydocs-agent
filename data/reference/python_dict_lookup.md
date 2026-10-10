# Python：字典按键取值

- 语言：Python
- 类别：字典操作
- 检索词：字典、`dict`、按键取值、`dict[key]`、`KeyError`、花括号
- 适用范围：Python 3 的普通字典

## 作用和写法

`dictionary[key]` 根据键 `key` 读取并返回对应的值。方括号中填写的是键；字典通过键和值的对应关系保存数据。

## 正常读取示例

```python
scores = {"Lin": 90, "Mei": 85}
print(scores["Lin"])
```

## 运行结果

```text
90
```

## 键不存在时

如果字典中没有这个键，使用方括号读取会引发 `KeyError`。下面的代码单独运行会报错：

```python
scores["Kai"]
```

如果键可能不存在，可以使用 `get()` 提供默认值：

```python
print(scores.get("Kai", 0))
```

运行结果：

```text
0
```

## 常见误区

- `scores["Lin"]` 中的 `"Lin"` 是键，`90` 是它对应的值。
- 普通字典用方括号读取不存在的键时，不会自动返回 `0`、空字符串或 `None`，而是引发 `KeyError`。
- `get()` 的行为不同：上例找不到 `"Kai"` 时返回我们提供的默认值 `0`。

## 参考来源

- [Python 官方文档：映射类型 `dict`](https://docs.python.org/3/library/stdtypes.html#mapping-types-dict)
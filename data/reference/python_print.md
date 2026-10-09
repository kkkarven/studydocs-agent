# Python：`print()` 输出文本

- 语言：Python
- 类别：内置函数
- 检索词：`print`、`print()`、输出、`sep`、`end`
- 适用范围：Python 3

## 作用

`print()` 把传入对象的文本表示写入输出流，默认输出到终端。一次传入多个对象时，默认在对象之间加一个空格，并在整次输出末尾换行。

## 示例

```python
print("Hello", "Python")
print("A", "B", sep="-", end="!")
print("完成")
```

## 运行结果

```text
Hello Python
A-B!完成
```

## 示例说明

- 第一行没有指定分隔内容，所以 `"Hello"` 和 `"Python"` 之间默认有一个空格。
- `sep` 用来设置多个对象之间的分隔内容。
- `end` 用来设置一次输出末尾追加的内容。第二行把它设为 `!`，所以第三行的内容会紧接着显示。

## 常见误区

- `sep` 控制对象之间的内容，`end` 控制整次输出的结尾。
- `print()` 负责输出；它和生成格式化字符串的 f-string 是不同的功能。

## 参考来源

- [Python 官方文档：内置函数 `print()`](https://docs.python.org/3/library/functions.html#print)
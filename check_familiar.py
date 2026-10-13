from familiar_store import (
    list_familiar,
    register_familiar,
    unregister_familiar,
    is_familiar,
)


print("初始熟悉库：", list_familiar())

print("第一次登记：", register_familiar("python_print.md"))
print("重复登记：", register_familiar("python_print.md"))

print("登记后的熟悉库：", list_familiar())
print("print 是否熟悉：", is_familiar("python_print.md"))
print("字典是否熟悉：", is_familiar("python_dict_lookup.md"))
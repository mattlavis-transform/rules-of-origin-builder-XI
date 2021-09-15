from classes.code_list import CodeList

albania = {
    "code":"AL",
    "prefix": "albania",
    "omit": 1
}
algeria = {
    "code":"DZ",
    "prefix": "algeria",
    "omit": 1
}
canada = {
    "code":"CA",
    "prefix": "canada",
    "omit": 1
}
japan = {
    "code":"JP",
    "prefix": "japan",
    "omit": 1
}
code_list = CodeList()
# code_list.load_example_codes()
code_list.export_to_json(canada)

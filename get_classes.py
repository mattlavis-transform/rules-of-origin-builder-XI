import os
import json


folder = os.path.join(os.getcwd(), "resources", "json_strategic")
files = os.listdir(folder)
files2 = []
for file in files:
    if ".json" in file:
        files2.append(file)

files2.sort()
my_classes = []
for file in files2:
    json_file_path = os.path.join(folder, file)
    print(file)
    f = open(json_file_path)
    data = json.load(f)
    rule_sets = data["rule_sets"]
    for rule_set in rule_sets:
        for rule in rule_set["rules"]:
            classes = rule["class"]
            my_classes += classes

my_classes = list(set(my_classes))
my_classes.sort()
f = open("all_classes.txt", "w")
for c in my_classes:
    f.write(c + "\n")

f.close()

import os
import json

def cleanse(s):
    s2 = ''.join(ch for ch in s if ch.isalnum()).lower()
    return s2

folder = os.path.join(os.getcwd(), "resources", "json_strategic")
export_path = os.path.join(os.getcwd(), "resources", "roo_classes")
files = os.listdir(folder)
files2 = []
for file in files:
    if ".json" in file:
        files2.append(file)

files2.sort()
my_classes = []
my_texts = {}

for file in files2:
    json_file_path = os.path.join(folder, file)
    f = open(json_file_path)
    data = json.load(f)
    rule_sets = data["rule_sets"]
    index = 0
    for rule_set in rule_sets:
        index += 1
        for rule in rule_set["rules"]:
            rule_text = rule["rule"]
            rule_text = cleanse(rule_text)
            classes = rule["class"]
            my_classes += classes

            if rule_text not in my_texts:
                if rule_text != "":
                    my_texts[rule_text] = classes

# Sort all files
my_classes = list(set(my_classes))
my_classes.sort()

# Write all classes to a persisted file
filename = os.path.join(export_path, "all_classes.txt")
f = open(filename, "w")
for c in my_classes:
    f.write(c + "\n")
f.close()

# Write all rule to class associations to a persisted file
filename = os.path.join(export_path, "all_rules.json")
f = open(filename, "w")
json.dump(my_texts, f, indent=4)
f.close()

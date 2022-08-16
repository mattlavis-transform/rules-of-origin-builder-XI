import os
import json

from classes_classic.classic_roo_folder import ClassicRooFolder


source_file = os.path.join(os.getcwd(), "resources", "source", "roo_countries.json")
f = open(source_file)
data = json.load(f)
f.close()
for item in data:
    if item["source"] == "classic":
        if item["omit"] != 1:
            classic_roo_folder = ClassicRooFolder(item["code"], item["prefix"], item["copy_options"])
            classic_roo_folder.process_roo_classic()

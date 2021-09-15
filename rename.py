import os

my_path = "/Users/mattlavis/sites and projects/1. Online Tariff/ott prototype/app/data/roo_psr/"

for root, dirs, files in os.walk(my_path, topdown=False):
    for name in files:
        if "FR_" in name:
            print(os.path.join(root, name))
            name_from = os.path.join(root, name)
            name_to = name_from.replace("FR_", "EU_")
            os.rename(name_from, name_to)
            a = 1

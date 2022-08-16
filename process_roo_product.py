import json
import os

from classes_product.product_roo_folder import ProductRooFolder


if 1 > 2:
    # Can't do any of these, as have no rules_decomposed
    product_roo_folder = ProductRooFolder("CM", "cameroon")

# product_roo_folder = ProductRooFolder("KR", "south-korea")
source_file = os.path.join(os.getcwd(), "resources", "source", "roo_countries.json")
f = open(source_file)
data = json.load(f)
f.close()
for item in data:
    if item["source"] == "product":
        if item["omit"] != 1:
            try:
                has_rules_decomposed = item["has_rules_decomposed"]
            except Exception as e:
                has_rules_decomposed = True

            product_roo_folder = ProductRooFolder(item["code"], item["prefix"], has_rules_decomposed)
            product_roo_folder.process_roo_product()

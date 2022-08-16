import os
import json

from classes_product.product_roo import ProductRoo
import classes.globals as g


class ProductRooFolder(object):
    def __init__(self, country_code, scheme_code):
        print("Processing data for {country_code} ({scheme_code})".format(country_code=country_code, scheme_code=scheme_code))
        self.country_code = country_code
        self.scheme_code = scheme_code
        self.rule_sets = []
        g.rule_ids = []

    def get_json_path(self):
        self.json_path = os.getcwd()
        self.json_path = os.path.join(self.json_path, "resources", "json", self.country_code)

    def process_roo_product(self):
        self.make_export_folder()
        self.get_jason_strategic_filename()
        self.get_json_path()
        self.get_json_files()
        self.process_files()
        self.write_json_data()

    def process_files(self):
        self.previous_json = {}
        for json_file in self.json_files:
            # json_file = "290110.json"
            self.process_file(json_file)
            self.previous_json = self.data_json

            if len(self.rule_sets) > 100000:
                break

    def process_file(self, json_file):
        subheading = json_file.replace(".json", "")
        json_file_path = os.path.join(self.json_path, json_file)
        f = open(json_file_path)
        self.data_json = json.load(f)
        f.close()

        if self.data_json != self.previous_json:
            product_roo = ProductRoo(self.data_json, subheading, self.country_code, self.scheme_code)
            self.rule_sets += product_roo.export
            a = 1
        else:
            a = 1
            pass

    def make_export_folder(self):
        self.json_strategic_folder = os.getcwd()
        self.json_strategic_folder = os.path.join(self.json_strategic_folder, "resources")
        self.json_strategic_folder = os.path.join(self.json_strategic_folder, "json_strategic")
        if not os.path.isdir(self.json_strategic_folder):
            os.mkdir(self.json_strategic_folder)

    def get_jason_strategic_filename(self):
        self.json_strategic_filename = os.path.join(self.json_strategic_folder, self.scheme_code + ".json")

    def write_json_data(self):
        data = {
            "rule_sets": self.rule_sets
        }
        f = open(self.json_strategic_filename, "w")
        json.dump(data, f, indent=4)
        f.close()

    def get_json_files(self):
        self.json_files = []
        files = os.listdir(self.json_path)
        for file in files:
            if ".json" in file:
                self.json_files.append(file)
        self.json_files.sort()

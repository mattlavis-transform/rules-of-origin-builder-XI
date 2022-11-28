import os
import json
import shutil
from dotenv import load_dotenv


from classes_product.product_roo import ProductRoo
import classes.globals as g


class ProductRooFolder(object):
    def __init__(self, country_code, scheme_code, has_rules_decomposed):
        print("Processing data for {country_code} ({scheme_code})".format(country_code=country_code, scheme_code=scheme_code))
        self.country_code = country_code
        self.scheme_code = scheme_code
        self.has_rules_decomposed = has_rules_decomposed
        self.rule_sets = []
        g.rule_ids = []

        load_dotenv('.env')
        self.export_path_uk = os.getenv('EXPORT_PATH_UK')
        self.export_path_xi = os.getenv('EXPORT_PATH_XI')
        self.get_overrides()
        self.get_chapters_to_process()

    def get_overrides(self):
        g.overrides = []
        folder = os.path.join(os.getcwd(), "resources", "overrides")
        file = os.path.join(folder, "overrides.json")
        f = open(file)
        data = json.load(f)
        for item in data:
            g.overrides.append(item)

        a = 1

    def get_chapters_to_process(self):
        load_dotenv('.env')
        self.chapters_to_process = os.getenv('CHAPTERS_TO_PROCESS')
        self.chapters_to_process = self.chapters_to_process.split(",")

        if (len(self.chapters_to_process)) == 1:
            if self.chapters_to_process[0] == "":
                self.chapters_to_process = []

        for i in range(0, len(self.chapters_to_process)):
            self.chapters_to_process[i] = self.chapters_to_process[i].zfill(2)

    def get_json_path(self):
        self.json_path = os.getcwd()
        self.json_path = os.path.join(self.json_path, "resources", "json", self.country_code)

    def process_roo_product(self):
        self.make_export_folder()
        self.get_json_strategic_filename()
        self.get_json_path()
        self.get_json_files()
        self.process_files()
        self.deal_with_ex_codes()
        self.write_json_data()
        self.copy_to_destination("xi")

    def copy_to_destination(self, which):
        source = self.json_strategic_filename
        if which == "xi":
            destination = self.export_path_xi
        else:
            destination = self.export_path_uk

        shutil.copy(source, destination)

    def process_files(self):
        self.previous_json = {}
        for json_file in self.json_files:
            if len(self.chapters_to_process) == 0:
                self.process_file(json_file)
                self.previous_json = self.data_json
            else:
                tmp = json_file.replace(".json", "").replace("chapter_", "")
                chapter = json_file[0:2]
                if chapter in self.chapters_to_process:
                    self.process_file(json_file)
                    self.previous_json = self.data_json

    def process_file(self, json_file):
        subheading = json_file.replace(".json", "")
        json_file_path = os.path.join(self.json_path, json_file)
        f = open(json_file_path)
        self.data_json = json.load(f)
        f.close()

        if self.data_json != self.previous_json:
            if "030611" in subheading:
                a = 1
            if "160100" in subheading:
                a = 1
            product_roo = ProductRoo(self.data_json, subheading, self.country_code, self.scheme_code, self.has_rules_decomposed)
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

    def get_json_strategic_filename(self):
        self.json_strategic_filename = os.path.join(self.json_strategic_folder, self.scheme_code + ".json")

    def deal_with_ex_codes(self):
        for chapter in range(1, 98):
            all_ex_codes = True
            if chapter == 4:
                a = 1
            is_chapter_mentioned = False
            rule_set_count = 0
            if chapter != 77:
                for rule_set in self.rule_sets:
                    if rule_set["chapter"] == chapter:
                        rule_set_count += 1
                        # if not rule_set["is_ex_code"]:
                        #     all_ex_codes = False
                        # if rule_set["is_chapter"]:
                        #     is_chapter_mentioned = True

            if not all_ex_codes:  # If it is all ex-codes, then we can just leave it as-is
                if rule_set_count > 1 and is_chapter_mentioned:
                    # Check if there are any ex codes anywhere except for on the chapter itself
                    # If there are not, then we can just replicate rules, ignoring the headings that are exceptions
                    has_ex_code_headings = False
                    for rule_set in self.rule_sets:
                        if rule_set["chapter"] == chapter:
                            if "chapter" not in rule_set["heading"].lower():
                                if "ex" in rule_set["heading"]:
                                    has_ex_code_headings = True
                                    break

                    if not has_ex_code_headings:
                        # self.normalise_standard_chapter(chapter)
                        print("normalise_standard_chapter")
                        a = 1
                    else:
                        # self.normalise_complex_chapter(chapter)
                        print("normalise_complex_chapter")
                        a = 1

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

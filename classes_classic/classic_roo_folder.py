import os
import json
import shutil
from dotenv import load_dotenv

from classes_classic.classic_roo import ClassicRoo


class ClassicRooFolder(object):
    def __init__(self, country_code, scheme_code, copy_options):
        print("Processing data for {country_code} ({scheme_code})".format(country_code=country_code, scheme_code=scheme_code))
        self.get_chapters_to_process()

        load_dotenv('.env')
        self.export_path_uk = os.getenv('EXPORT_PATH_UK')
        self.export_path_xi = os.getenv('EXPORT_PATH_XI')
        self.country_code = country_code
        self.scheme_code = scheme_code
        self.copy_options = copy_options
        self.rule_sets = []

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
        a = 1

    def process_roo_classic(self):
        self.make_export_folder()
        self.get_json_strategic_filename()
        self.get_json_path()
        self.get_json_files()
        self.process_files()
        self.strip_invalid_entries()
        self.write_json_data()
        self.copy_to_destination("xi")
        self.copy_to_destination("uk")

    def strip_invalid_entries(self):
        rule_set_count = len(self.rule_sets)
        for i in range(rule_set_count - 1, -1, -1):
            rule_set = self.rule_sets[i]
            if rule_set["valid"] is False:
                self.rule_sets.pop(i)
            elif len(rule_set["rules"]) == 0:
                self.rule_sets.pop(i)

    def process_files(self):
        for json_file in self.json_files:
            if len(self.chapters_to_process) == 0:
                rule_sets = self.process_file(json_file)
                if rule_sets is not None:
                    self.rule_sets += rule_sets
            else:
                tmp = json_file.replace(".json", "").replace("chapter_", "")
                if tmp in self.chapters_to_process:
                    rule_sets = self.process_file(json_file)
                    if rule_sets is not None:
                        self.rule_sets += rule_sets

    def process_file(self, json_file):
        subheading = json_file.replace(".json", "")
        json_file_path = os.path.join(self.json_path, json_file)
        f = open(json_file_path)
        data_json = json.load(f)
        if len(data_json) > 1:
            data_json = [data_json[0]]
        classic_roo = ClassicRoo(data_json, subheading, self.country_code, self.scheme_code)
        self.rule_sets += classic_roo.rules_json
        f.close()

    def make_export_folder(self):
        self.json_strategic_folder = os.getcwd()
        self.json_strategic_folder = os.path.join(self.json_strategic_folder, "resources")
        self.json_strategic_folder = os.path.join(self.json_strategic_folder, "json_strategic")
        if not os.path.isdir(self.json_strategic_folder):
            os.mkdir(self.json_strategic_folder)

    def get_json_strategic_filename(self):
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

    def copy_to_destination(self, which):
        if which in self.copy_options:
            source = self.json_strategic_filename
            if which == "xi":
                destination = self.export_path_xi
            else:
                destination = self.export_path_uk

            shutil.copy(source, destination)

import os
import glob
import json

from classes.database import Database


class CoverageChecker:
    def __init__(self):
        self.missing_codes = []
        self.get_files()
        self.get_exceptions()
        self.get_codes()

    def get_exceptions(self):
        filename = os.path.join(self.coverage_report_folder, "exceptions.json")
        with open(filename) as f:
            self.exceptions = json.load(f)
            a = 1

    def get_files(self):
        self.files = []
        self.folder = os.path.join(os.getcwd(), "resources", "json_strategic")
        self.coverage_report_folder = os.path.join(os.getcwd(), "resources", "coverage_report")

        # specific_country = "pacific"
        specific_country = ""

        if specific_country != "":
            for file in glob.glob(os.path.join(self.folder, "*.json")):
                if specific_country in file:
                    self.files.append(file)
        else:
            for file in glob.glob(os.path.join(self.folder, "*.json")):
                self.files.append(file)

        self.files.sort()

    def get_codes(self):
        self.codes = []
        sql = """
        select distinct left(goods_nomenclature_item_id, 6)
        from utils.materialized_commodities_new mcn
        where productline_suffix = '80'
        and validity_end_date > current_date
        and number_indents > 0
        and goods_nomenclature_item_id < '9800000000'
        order by 1
        """
        d = Database()
        params = []
        rows = d.run_query(sql, params)
        for row in rows:
            self.codes.append(row[0] + "0000")

    def check_coverage(self):
        for file in self.files:
            self.check(file)

    def check(self, file):
        f = open(file)
        file = file.replace(self.folder, "")
        file = file.replace("/", "")
        data = json.load(f)
        rule_sets = []
        for rule_set in data["rule_sets"]:
            obj = {
                "min": rule_set["min"],
                "max": rule_set["max"]
            }
            rule_sets.append(obj)
            a = 1
        a = 1
        f.close()

        for code in self.codes:
            found = False
            for rule_set in rule_sets:
                if rule_set["min"] <= code and rule_set["max"] >= code:
                    found = True
                    a = 1
            if found is False:
                obj = {
                    "file": file,
                    "code": code
                }
                self.missing_codes.append(obj)
        a = 1

    def write_report(self):
        problem_countries = []
        filename = os.path.join(self.coverage_report_folder, "coverage_report.csv")
        f = open(filename, "w")
        for missing_code in self.missing_codes:
            if missing_code["code"][0:2] != "93":
                write_exception = True
                for exception in self.exceptions:
                    if write_exception:
                        if exception in missing_code["file"]:
                            for excepted_code in self.exceptions[exception]:
                                if missing_code["code"].startswith(excepted_code):
                                    write_exception = False
                                    break
                if write_exception:
                    f.write(missing_code["file"] + ", ")
                    f.write(missing_code["code"] + "\n")
                    if missing_code["file"] not in problem_countries:
                        problem_countries.append(missing_code["file"])

        f.close()

        filename = os.path.join(self.coverage_report_folder, "problem_countries.csv")
        f = open(filename, "w")
        for problem_country in problem_countries:
            f.write(problem_country + "\n")

        f.close()

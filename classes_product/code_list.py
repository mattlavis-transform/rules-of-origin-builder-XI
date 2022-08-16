import os
from re import sub
import sys
from datetime import datetime
import csv
import filecmp
import collections
import shutil
import json
from urllib.request import urlopen
from dotenv import load_dotenv
import logging

from classes.database import Database
from classes_product.eu_roo import EuRoo
from classes_product.rule import Rule


class CodeList(object):
    def __init__(self):
        logging.basicConfig(filename='log/app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')
        load_dotenv('.env')
        self.config = {}
        self.config["min_code"] = os.getenv('MIN_CODE')
        self.config["max_code"] = os.getenv('MAX_CODE')
        self.config["specific_country"] = os.getenv('SPECIFIC_COUNTRY')
        self.config["specific_code"] = os.getenv('SPECIFIC_CODE')
        self.config["write_files"] = bool(os.getenv('WRITE_FILES'))
        # self.config["save_to_db"] = bool(os.getenv('SAVE_TO_DB'))
        # self.config["overwrite_db"] = bool(os.getenv('OVERWRITE_DB'))

        self.url_template = os.getenv('url_template')
        self.url_template_classic = os.getenv('url_template_classic')

        self.rule_sets = []

        self.get_current_subheadings()
        self.get_countries()

    def get_current_subheadings(self):
        self.commodity_code_folder = os.getenv('commodity_code_folder')
        files_temp = []
        files = os.listdir(self.commodity_code_folder)
        for file in files:
            if ".csv" in file:
                if "eu_commodities" in file:
                    files_temp.append(file)

        files_temp.sort(reverse=True)
        latest_file = os.path.join(self.commodity_code_folder, files_temp[0])
        self.exemplar_codes = []
        with open(latest_file) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            for row in csv_reader:
                if line_count > 0:
                    subheading = row[1][0:6]
                    leaf = int(row[6])
                    if leaf == 1:
                        if subheading not in self.exemplar_codes:
                            self.exemplar_codes.append(subheading)

                line_count += 1

        self.strip_redundant_codes_from_simple_chapters()

    def strip_redundant_codes_from_simple_chapters(self):
        # simple_chapters = [1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 97, 98]
        simple_chapters = [1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 97, 98]
        simple_chapter_exemplars = {}
        expurgated_codes = []
        for code in self.exemplar_codes:
            chapter_as_integer = int(code[0:2])
            subheading = code[0:4]
            if chapter_as_integer in simple_chapters:
                if subheading not in simple_chapter_exemplars:
                    simple_chapter_exemplars[code[0:4]] = code
                    expurgated_codes.append(code)
            else:
                expurgated_codes.append(code)

        a = 1
        self.exemplar_codes = None
        self.exemplar_codes = expurgated_codes

    def get_countries(self):
        folder = os.getcwd()
        folder = os.path.join(folder, "resources")
        folder = os.path.join(folder, "source")
        countries_file = os.path.join(folder, "roo_countries.json")
        f = open(countries_file)
        self.countries = json.load(f)

        if self.config["specific_country"] != "" and self.config["specific_country"] is not None:
            tmp = self.countries
            self.countries = []
            for country in tmp:
                if country["code"] == self.config["specific_country"]:
                    self.countries.append(country)
        a = 1

    def scrape_roo(self):
        for country in self.countries:
            if country["omit"] != 1:
                if country["source"] == "product":
                    for exemplar_code in self.exemplar_codes:
                        if exemplar_code >= self.config["min_code"] and exemplar_code < self.config["max_code"]:
                            print("Getting commodity {0} from MADB for {1} ({2})".format(
                                exemplar_code,
                                country["code"],
                                country["prefix"]
                            ))

                            url = self.url_template.replace("{{country}}", country["code"])
                            url = url.replace("{{id}}", exemplar_code)

                            try:
                                response = urlopen(url)
                                data_json = json.loads(response.read())

                                # Save the raw data
                                folder = os.getcwd()
                                folder = os.path.join(folder, "resources")
                                folder = os.path.join(folder, "json")
                                folder = os.path.join(folder, country["code"])
                                if not os.path.isdir(folder):
                                    os.mkdir(folder)
                                file = os.path.join(folder, exemplar_code) + ".json"
                                f = open(file, "w+")
                                json.dump(data_json, f, indent=4)
                                f.close()
                            except Exception as e:
                                logging.error("Exception occurred", exc_info=True)
                else:
                    # Classic lookup for Turkey, Kenya and GSP
                    for chapter in range(1, 99):
                        if chapter != 77:
                            chapter_string = str(chapter).zfill(2)

                            print("Getting chapter {0} from MADB for {1} ({2})".format(
                                chapter_string,
                                country["code"],
                                country["prefix"]
                            ))

                            url = self.url_template_classic.replace("{{country}}", country["code"])
                            url = url.replace("{{id}}", chapter_string)

                            try:
                                response = urlopen(url)
                                data_json = json.loads(response.read())

                                # Save the raw data
                                folder = os.getcwd()
                                folder = os.path.join(folder, "resources")
                                folder = os.path.join(folder, "json")
                                folder = os.path.join(folder, country["code"])
                                if not os.path.isdir(folder):
                                    os.mkdir(folder)
                                file = os.path.join(folder, "chapter_" + chapter_string + ".json")
                                f = open(file, "w+")
                                json.dump(data_json, f, indent=4)
                                f.close()
                            except Exception as e:
                                logging.error("Exception occurred", exc_info=True)

    def get_heading_descriptions(self):
        d = Database()
        sql = """
        select distinct left(gn.goods_nomenclature_item_id, 4)
        from goods_nomenclatures gn
        where right(gn.goods_nomenclature_item_id, 6) = '000000'
        -- and right(gn.goods_nomenclature_item_id, 8) != '00000000'
        and gn.validity_end_date is null
        order by 1;
        """
        self.heading_extents = d.run_query(sql)
        self.heading_extents_dict = {}
        for i in range(1, 100):
            if i != 77:
                chapter = str(i).zfill(2)
                self.heading_extents_dict[chapter] = []
                for extent in self.heading_extents:
                    if extent[0][0:2] == chapter:
                        if extent[0][2:4] != "00":
                            self.heading_extents_dict[chapter].append(extent[0])

        a = 1
        d = Database()
        sql = """
        select distinct on (gnd.goods_nomenclature_item_id)
        gnd.goods_nomenclature_item_id, coalesce(gnd.description, '') as description
        from goods_nomenclature_descriptions gnd, goods_nomenclature_description_periods gndp
        where gnd.goods_nomenclature_sid = gndp.goods_nomenclature_sid
        and right(gnd.goods_nomenclature_item_id, 4) = '0000'
        -- and right(gnd.goods_nomenclature_item_id, 8) != '00000000'
        order by gnd.goods_nomenclature_item_id,  gndp.validity_start_date desc
        """
        self.headings = d.run_query(sql)
        self.headings_dict = {}
        for head in self.headings:
            self.headings_dict[head[0]] = head[1]

    def process_roo(self):
        self.get_heading_descriptions()
        root_path = os.getcwd()
        root_path = os.path.join(root_path, "resources", "json")
        paths = []
        directory_contents = os.listdir(root_path)
        for file in directory_contents:
            file_path = os.path.join(root_path, file)
            if os.path.isdir(file_path):
                print(file_path)
                paths.append(file)

        if self.config["specific_country"] is not None:
            paths2 = []
            for path in paths:
                if path == self.config["specific_country"]:
                    paths2.append(path)

            paths = paths2

        paths.sort()
        # In which the paths are the countries that are representative of the RoO schemes
        for path in paths:
            if path == "AF":
                self.clear_db(path)

            country = self.get_country(path)
            path2 = os.path.join(root_path, path)
            directory_contents = os.listdir(path2)
            self.do_timestamp()
            json_files = []
            if self.config["specific_code"] != "" and self.config["specific_code"] is not None:
                json_files.append(self.config["specific_code"][0:6] + ".json")
            else:
                for item in directory_contents:
                    json_files.append(item)

            json_files.sort()
            # In which the items are the downloaded files (the headings for the new RoO types, and the chapters for the old, classic ones)
            for json_file in json_files:
                json_file_path = os.path.join(path2, json_file)
                subheading = json_file.replace(".json", "")
                if os.path.isfile(json_file_path) and ".json" in json_file_path:  # and item >= "3824":
                    if country["source"] == "product":
                        # New data files
                        print("Getting commodity {0} from MADB for {1} ({2})".format(
                            subheading,
                            country["code"],
                            country["prefix"]
                        ))

                        f = open(json_file_path)
                        data_json = json.load(f)
                        rules = data_json["rules"]
                        footnotes = data_json["footnotes"]

                        for (k, v) in rules.items():
                            eu_roo = EuRoo(k, v, footnotes, country, subheading, self.config, self.headings_dict, self.heading_extents_dict)

            # if country["source"] != "product":
            #     self.apply_classic_rules_to_commodities()

            self.export_to_json(country, "xi")
            self.export_rule_sets_strategic(country)
            self.do_timestamp()

    def apply_classic_rules_to_commodities(self):
        # Get the rules that have been written for GSP
        sql = """
        select id_rule, key_first, key_last
        from roo.rules r where country_prefix = 'gsp'
        order by key_first, key_last;
        """
        d = Database()
        params = []
        classic_rules = d.run_query(sql, params)

        for ex in self.exemplar_codes:
            print("Finding rule for subheading", ex.goods_nomenclature_item_id[0:6])
            ex1 = ex.goods_nomenclature_item_id[0:6] + "0000"
            ex2 = ex.goods_nomenclature_item_id[0:6] + "9999"
            for classic_rule in classic_rules:
                if ex2 >= classic_rule[1] and ex1 < classic_rule[2]:
                    # Then save the relationship with the subheading
                    d = Database()
                    sql = """
                    INSERT INTO roo.rules_to_commodities
                    (
                        id_rule, scope, subheading, country_prefix
                    )
                    VALUES
                    (%s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                    """

                    params = [
                        classic_rule[0],
                        "xi",
                        ex.goods_nomenclature_item_id[0:6],
                        "gsp",
                    ]
                    d.run_query(sql, params)

                    break
        a = 1

    def clear_db(self, path):
        print("Clearing database of previous entries")

        # Delete the rules themselves
        sql = """delete from roo.rules r where country_prefix = 'gsp';"""
        d = Database()
        params = []
        d.run_query(sql, params)

        # Delete the rules' associations with commodities
        sql = """delete from roo.rules_to_commodities where country_prefix = 'gsp';"""
        d = Database()
        params = []
        d.run_query(sql, params)

    def export_to_json(self, country, scope):
        d = Database()

        sql = """
        select subheading, heading, description, rule,
        alternate_rule, quota_amount, quota_unit, key_first, key_last
        from roo.rules_to_commodities rtc, roo.rules r
        where r.id_rule = rtc.id_rule
        and r.country_prefix = %s
        and r.scope = %s
        and rtc.scope = %s
        order by subheading;
        """

        params = [
            country["prefix"],
            scope,
            scope
        ]
        rows = d.run_query(sql, params)
        object = {}
        object["rules"] = []
        previous_rule = Rule()
        for row in rows:
            rule = Rule(row)
            # if not rule.equates_to(previous_rule):
            #     object["rules"].append(rule.asdict())
            object["rules"].append(rule.asdict())
            previous_rule = rule

        load_dotenv('.env')
        export_path = os.getenv('EXPORT_PATH')
        filename = os.path.join(export_path, country["prefix"] + "_roo.json")
        with open(filename, 'w') as f:
            json.dump(object, f, indent=4)
        a = 1
        f.close()

    def do_timestamp(self):
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        print("Current Time =", current_time)

    def get_country(self, path):
        ret = ""
        for country in self.countries:
            if country["code"] == path:
                ret = country
                break

        return ret

    def do_replacements(self, s):
        s = s.replace('<td><p class="doc_text">', '<td class="doc_text">')
        return (s)

    def combine_like_files(self):
        self.get_export_folder()
        self.html_finals = {}
        index = 0

        for entry in os.scandir(self.export_folder):
            index += 1
            if entry.path.endswith(".html") and entry.is_file():
                stem = entry.name[0:7]
                try:
                    self.html_finals[stem]["files"].append(entry.name)
                except Exception as e:
                    obj = {}
                    obj["files"] = [entry.name]
                    self.html_finals[stem] = obj

        self.html_finals = collections.OrderedDict(
            sorted(self.html_finals.items()))
        for key in self.html_finals:
            files = self.html_finals[key]["files"]
            files.sort()
            if len(files) > 1:
                all_same = True
                file0 = os.path.join(self.export_folder, files[0])
                for n in range(1, len(files)):
                    file_n = os.path.join(self.export_folder, files[n])
                    comp = filecmp.cmp(file0, file_n, shallow=False)
                    if comp is False:
                        all_same = False
                        break

                if all_same is False:
                    for n in range(1, len(files)):
                        source = os.path.join(self.export_folder, files[n])
                        destination = source.replace("html/", "html_final/")
                        shutil.copy(source, destination)
                else:
                    # All files the same
                    filename = files[0][0:7] + "00.html"
                    source = os.path.join(self.export_folder, files[0])
                    destination = source.replace("html/", "html_final/")
                    destination = destination.replace(files[0], filename)
                    shutil.copy(source, destination)

    def export_rule_sets_strategic(self, country):
        self.scheme_code = country["prefix"]
        self.make_export_folder()
        self.get_jason_strategic_filename()
        self.extract = {}
        self.extract["rule_sets"] = self.rule_sets
        f = open(self.json_strategic_filename, "w")
        json.dump(self.extract, f, indent=4)
        f.close()

    def make_export_folder(self):
        self.json_strategic_folder = os.getcwd()
        self.json_strategic_folder = os.path.join(self.json_strategic_folder, "resources")
        self.json_strategic_folder = os.path.join(self.json_strategic_folder, "json_strategic")
        if not os.path.isdir(self.json_strategic_folder):
            os.mkdir(self.json_strategic_folder)
        a = 1

    def get_jason_strategic_filename(self):
        a = 1
        self.json_strategic_filename = os.path.join(self.json_strategic_folder, self.scheme_code + ".json")

import os
from re import sub
import sys
from datetime import datetime
from classes.database import Database
from classes.classification import Classification
from classes.eu_roo import EuRoo
from classes.classic_roo import ClassicRoo
import requests
import csv
from bs4 import BeautifulSoup
import filecmp
import collections
import shutil
import json
from urllib.request import urlopen
from dotenv import load_dotenv
import logging


class CodeList(object):
    def __init__(self):
        logging.basicConfig(filename='log/app.log', filemode='w',
                            format='%(name)s - %(levelname)s - %(message)s')
        load_dotenv('.env')
        self.config = {}
        self.config["min_code"] = os.getenv('MIN_CODE')
        self.config["specific_country"] = os.getenv('SPECIFIC_COUNTRY')
        self.config["specific_code"] = os.getenv('SPECIFIC_CODE')
        self.config["write_files"] = bool(os.getenv('WRITE_FILES'))
        self.config["save_to_db"] = bool(os.getenv('SAVE_TO_DB'))
        self.config["overwrite_db"] = bool(os.getenv('OVERWRITE_DB'))

        self.load_exemplar_codes()

        self.get_countries()
        self.url_template = "https://webgate.ec.europa.eu/roo/public/v1/rules/product/{{id}}/country/EU/partner/{{country}}?app=madb&direction=IMPORT&format=HTML&language=EN"
        self.url_template_classic = "https://webgate.ec.europa.eu/roo/public/v1/classic/chapter/{{id}}/country/{{country}}?language=EN"

    def load_exemplar_codes(self):
        self.get_exemplar_codes_filename()
        self.exemplar_codes = []
        with open(self.filename) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            for row in csv_reader:
                ex = Classification(row[0], row[1], "80", -1, 1)
                self.exemplar_codes.append(ex)

        if self.config["specific_code"] is not None and self.config["specific_code"] != "":
            tmp = self.exemplar_codes
            self.exemplar_codes = []
            for item in tmp:
                if item.goods_nomenclature_item_id == self.config["specific_code"]:
                    self.exemplar_codes.append(item)
        a = 1

    def get_exemplar_codes_filename(self):
        folder = os.getcwd()
        folder = os.path.join(folder, "resources")
        folder = os.path.join(folder, "csv")
        filename = "exemplar_codes.csv"
        self.filename = os.path.join(folder, filename)

    def get_countries(self):
        folder = os.getcwd()
        folder = os.path.join(folder, "resources")
        folder = os.path.join(folder, "source")
        countries_file = os.path.join(folder, "countries.json")
        f = open(countries_file)
        self.countries = json.load(f)

        if self.config["specific_country"] != "" and self.config["specific_country"] is not None:
            tmp = self.countries
            self.countries = []
            for country in tmp:
                if country["code"] == self.config["specific_country"]:
                    self.countries.append(country)

    def scrape_roo(self):
        for country in self.countries:
            if country["omit"] != 1:
                if country["source"] == "product":
                    for ex in self.exemplar_codes:
                        if ex.goods_nomenclature_item_id >= self.config["min_code"]:
                            print("Getting commodity {0} from MADB for {1} ({2})".format(
                                ex.goods_nomenclature_item_id,
                                country["code"],
                                country["prefix"]
                            ))

                            url = self.url_template.replace("{{country}}", country["code"])
                            url = url.replace("{{id}}", ex.goods_nomenclature_item_id[0:6])

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
                                file = os.path.join(
                                    folder, ex.goods_nomenclature_item_id[0:6]) + ".json"
                                f = open(file, "w+")
                                json.dump(data_json, f, indent=4)
                                f.close()

                                if 1 > 2:
                                    rules = data_json["rules"]
                                    footnotes = data_json["footnotes"]

                                    for (k, v) in rules.items():
                                        eu_roo = EuRoo(
                                            k, v, footnotes, country, ex.goods_nomenclature_item_id, self.config)
                            except:
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
                            except:
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
        for item in directory_contents:
            item2 = os.path.join(root_path, item)
            if os.path.isdir(item2):
                print(item2)
                paths.append(item)

        if self.config["specific_country"] is not None:
            paths2 = []
            for path in paths:
                if path == self.config["specific_country"]:
                    paths2.append(path)
                    
            paths = paths2
        
        paths.sort()
        for path in paths:
            country = self.get_country(path)
            path2 = os.path.join(root_path, path)
            directory_contents = os.listdir(path2)
            self.do_timestamp()
            items = []
            if self.config["specific_code"] != "" and self.config["specific_code"] is not None:
                items.append(self.config["specific_code"][0:6] + ".json")
            else:
                for item in directory_contents:
                    items.append(item)
                    
            items.sort()
            for item in items:
                item2 = os.path.join(path2, item)
                subheading = item.replace(".json", "")
                if os.path.isfile(item2) and ".json" in item2: # and item >= "3824":
                    if country["source"] == "product":
                        print("Getting commodity {0} from MADB for {1} ({2})".format(
                            subheading,
                            country["code"],
                            country["prefix"]
                        ))

                        f = open(item2)
                        data_json = json.load(f)
                        rules = data_json["rules"]
                        footnotes = data_json["footnotes"]

                        for (k, v) in rules.items():
                            eu_roo = EuRoo(k, v, footnotes, country, subheading, self.config, self.headings_dict, self.heading_extents_dict)
                    else:
                        print("Getting classic {0} from MADB for {1} ({2})".format(
                            subheading,
                            country["code"],
                            country["prefix"]
                        ))

                        f = open(item2)
                        data_json = json.load(f)
                        classic_roo = ClassicRoo(data_json, country, subheading, self.config)
                        
            self.export_to_json(country, "xi")
            self.do_timestamp()
            # sys.exit()
            
    def export_to_json(self, country, scope):
        d = Database()
        
        sql = """
        select sub_heading, heading, description, rule,
        alternate_rule, quota_amount, quota_unit, key_first, key_last
        from roo.rules_to_commodities rtc, roo.rules r
        where r.id_rule = rtc.id_rule 
        and r.country_prefix = %s
        and r.scope = %s
        and rtc.scope = %s
        order by sub_heading;
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
                except:
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

    def scrape_twuk(self):
        self.get_export_folder()

        url_template = "https://www.get-rules-tariffs-trade-with-uk.service.gov.uk/country/{{country}}/commodity/{{id}}/{{sid}}"
        # countries = ["FR", "JP"]
        countries = ["CA"]
        min_code = "271020"
        # min_code = "6201999999"
        # min_code = "0"
        for country in countries:
            for ex in self.exemplar_codes:
                if ex.goods_nomenclature_item_id > min_code:
                    url = url_template.replace("{{country}}", country)
                    url = url.replace("{{sid}}", ex.goods_nomenclature_sid)
                    url = url.replace("{{id}}", ex.goods_nomenclature_item_id)

                    response = requests.get(url)
                    soup = BeautifulSoup(response.text, "html.parser")
                    # ('div#rules-of-origin')
                    my_divs = soup.findAll("div", {"id": "rules-of-origin"})
                    if (my_divs):
                        my_div = my_divs[0]
                        temp = my_div.select(".app-flexible-table")

                        if len(temp) > 0:
                            pse_table = my_div.select(
                                ".app-flexible-table")[0].prettify()
                            pse_table = pse_table.replace(
                                " app-flexible-table__header", "")
                            pse_table = pse_table.replace(
                                " app-flexible-table__head", "")
                            pse_table = pse_table.replace(
                                " app-flexible-table__body", "")
                            pse_table = pse_table.replace(
                                " app-flexible-table__row", "")
                            pse_table = pse_table.replace(
                                " app-flexible-table__cell", "")
                            pse_table = pse_table.replace(
                                " app-flexible-table", "")
                            pse_table = pse_table.replace(' rowspan="1"', "")
                            pse_table = pse_table.replace(
                                ' data-target="hierarchy-modal" data-toggle="modal" href="javascript:void(0)"', "")
                            pse_table = pse_table.replace(
                                ' class="hierarchy-modal"', "")
                            pse_table = sub(
                                r'<a data-href=[^>]+>([^<]+)<\/a>', r'\1', pse_table)
                        else:
                            pse_table = "<p>No data</p>"

                        filename = country + "_" + \
                            ex.goods_nomenclature_item_id[0:6] + ".html"
                        print(filename)
                        filename = os.path.join(self.export_folder, filename)

                        f = open(filename, "w+")
                        f.write(pse_table)
                        f.close()

    def get_codes(self):
        self.get_exemplar_codes_filename()
        self.exemplar_codes = []
        d = datetime.now()
        d2 = datetime.strftime(d, '%Y-%m-%d')
        self.unique_subheadings = []
        self.classifications = []
        for i in range(0, 10):
            chapter = str(i) + "%"
            sql = """
            select goods_nomenclature_sid, goods_nomenclature_item_id, producline_suffix, number_indents, leaf
            from utils.goods_nomenclature_export_new('""" + chapter + """', '""" + d2 + """')
            where validity_end_date is null
            order by goods_nomenclature_item_id, producline_suffix;
            """

            print(
                "Getting complete commodity code list for codes beginning with " + str(i))
            d = Database()
            rows = d.run_query(sql)
            for row in rows:
                classification = Classification(
                    row[0],
                    row[1],
                    row[2],
                    row[3],
                    row[4]
                )
                if classification.leaf == 1:
                    self.classifications.append(classification)
                    self.unique_subheadings.append(
                        classification.goods_nomenclature_item_id[0:6])

        self.unique_subheadings = list(set(self.unique_subheadings))
        self.unique_subheadings.sort()

        start_index = 0

        for subheading in self.unique_subheadings:
            found = False
            for i in range(start_index, len(self.classifications) - 1):
                c = self.classifications[i]
                if c.goods_nomenclature_item_id[0:6] == subheading:
                    self.exemplar_codes.append(c)
                    found = True
                    a = 1
                    start_index = i + 1
                    break

        f = open(self.filename, "w+")
        for ex in self.exemplar_codes:
            f.write(str(ex.goods_nomenclature_sid) + ",")
            f.write(ex.goods_nomenclature_item_id + "\n")

        f.close()

class Rule(object):
    def __init__(self, row = None):
        if row is None:
            self.sub_heading = None
            self.heading = None
            self.description = None
            self.rule = None
            self.alternate_rule = None
            self.quota_amount = None
            self.quota_unit = None
            self.key_first = None
            self.key_last = None
        else:
            self.sub_heading = row[0]
            self.heading = row[1]
            self.description = row[2]
            self.rule = row[3]
            self.alternate_rule = row[4]
            self.quota_amount = row[5]
            self.quota_unit = row[6]
            self.key_first = row[7]
            self.key_last = row[8]

    def equates_to(self, rule):
        equal = True
        if self.sub_heading != rule.sub_heading:
            equal = False
        elif self.heading != rule.heading:
            equal = False
        elif self.description != rule.description:
            equal = False
        elif self.description != rule.description:
            equal = False
        elif self.rule != rule.rule:
            equal = False
        elif self.alternate_rule != rule.alternate_rule:
            equal = False
        elif self.key_first != rule.key_first:
            equal = False
        elif self.key_last != rule.key_last:
            equal = False
        
        return equal
    
    def asdict(self):
        return {
            'sub_heading': self.sub_heading,
            'heading': self.heading,
            'description': self.description,
            'rule': self.rule,
            'alternate_rule': self.alternate_rule,
            'quota_amount': self.quota_amount,
            'quota_unit': self.quota_unit,
            'key_first': self.key_first,
            'key_last': self.key_last
        }

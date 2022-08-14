from datetime import datetime
import sys
import re
from markdownify import markdownify as md
from classes.database import Database
from classes.footnote import Footnote
import logging


class EuRoo(object):
    def __init__(self, key, rules, footnote_data, country, goods_nomenclature_item_id, config, headings_dict, heading_extents_dict):
        global code_list
        logging.basicConfig(filename='log/app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')
        self.goods_nomenclature_item_id = goods_nomenclature_item_id
        self.subheading = self.goods_nomenclature_item_id[0:6]
        self.config = config
        self.headings_dict = headings_dict
        self.heading_extents_dict = heading_extents_dict

        self.key_verbatim = key.replace(".", "")
        if "ex" in self.key_verbatim:
            self.key = self.key_verbatim.replace("ex ", "")
            # self.key = self.key_verbatim
            self.ex = True
        else:
            self.key = self.key_verbatim
            self.ex = False

        self.rules = rules
        self.footnote_data = footnote_data
        self.country_code = country["code"]
        self.country_prefix = country["prefix"]

        self.parse_key()
        self.parse_rule_description()
        self.parse_footnotes()

        self.format_rules_and_descriptions()
        if self.config["save_to_db"]:
            self.save_to_db()
        a = 1

    def parse_footnotes(self):
        self.footnotes = {}
        for footnote in self.footnote_data:
            f = Footnote()
            f.code = footnote["code"]
            f.content = self.fmt(footnote["content"])
            f.content = md(f.content)
            f.save()
            self.footnotes[f.code] = f.content

    def parse_key(self):
        tmp = self.key

        if " and " in self.key:
            self.key = self.key.replace("and", "-")

        if "-" in self.key:
            self.key = self.key.replace(" ", "")
            parts = self.key.split("-")
            self.key_min = parts[0]
            self.key_max = parts[1]

            # Check if this is actually the whole chapter but written as (e.g.) 0101-0106
            self.chapter = self.goods_nomenclature_item_id[0:2]
            if self.key_min == self.heading_extents_dict[self.chapter][0]:
                if self.key_max == self.heading_extents_dict[self.chapter][len(self.heading_extents_dict[self.chapter]) - 1]:
                    comm_code = self.chapter.ljust(10, "0")
                    self.description = "Chapter " + \
                        str(int(self.chapter)) + " - " + \
                        self.headings_dict[comm_code].lower().capitalize()
            a = 1
            self.key = self.key_verbatim

        elif "Chapter" in tmp:
            tmp = tmp.replace("Chapter", "")
            tmp = tmp.strip()
            if int(tmp) < 10:
                self.key_min = "0" + tmp
                self.key_max = "0" + tmp
            else:
                self.key_min = tmp
                self.key_max = tmp

            if self.ex:
                self.key = "ex&nbsp;" + self.key
        else:
            self.key_min = self.key
            self.key_max = self.key
            self.key = self.key_verbatim

        self.key_first = self.key_min + ("0" * (10 - len(self.key_min)))
        self.key_last = self.key_max + ("9" * (10 - len(self.key_max)))
        self.key = self.key.replace("ex ", "ex&nbsp;")
        self.key = self.key.replace("Chapter ", "Chapter&nbsp;")

    def parse_rule_description(self):
        self.rules[0]["description"] = self.rules[0]["description"].strip("- ")
        heading = HeadingRange(
            self.rules[0]["description"],
            self.goods_nomenclature_item_id,
            self.heading_extents_dict,
            self.headings_dict
        )
        self.rules[0]["description"] = heading.parse_description()

    def format_rules_and_descriptions(self):
        for i in range(0, len(self.rules)):
            self.rules[i]["description_string"] = self.fmt(self.rules[i]["description"], do_markdown=False)
            self.rules[i]["rule_string"] = self.fmt(self.rules[i]["rule"])
            self.rules[i]["alternate_rule_string"] = self.fmt(self.rules[i]["alternateRule"])

            # For Canada - CC
            if "Change of chapter" in self.rules[i]["rule_string"]:
                if "CC" not in self.rules[i]["rule_string"]:
                    self.rules[i]["rule_string"] = self.rules[i]["rule_string"].replace("Change of chapter", "Change of chapter - CC")
                self.rules[i]["rule_string"] += "{{CC}}"

            # For Japan - CC
            elif "CC" in self.rules[i]["rule_string"]:
                self.rules[i]["rule_string"] = self.rules[i]["rule_string"].replace("CC", "Change of chapter - CC")
                self.rules[i]["rule_string"] += "{{CC}}"

            # For Canada - CTH
            if "A change from any other heading" in self.rules[i]["rule_string"]:
                if "CTH" not in self.rules[i]["rule_string"]:
                    self.rules[i]["rule_string"] = self.rules[i]["rule_string"].replace("A change from any other heading", "A change from any other heading - CTH")
                self.rules[i]["rule_string"] += "{{CTH}}"

            # For Japan - CTH
            elif "CTH" in self.rules[i]["rule_string"]:
                self.rules[i]["rule_string"] = self.rules[i]["rule_string"].replace("CTH", "A change from any other heading - CTH")
                self.rules[i]["rule_string"] += "{{CTH}}"

            # For Canada - CTSH
            if "A change from any other subheading" in self.rules[i]["rule_string"]:
                if "CTSH" not in self.rules[i]["rule_string"]:
                    self.rules[i]["rule_string"] = self.rules[i]["rule_string"].replace("A change from any other subheading", "A change from any other subheading - CTSH")
                self.rules[i]["rule_string"] += "{{CTSH}}"

            # For Japan - CTSH
            elif "CTSH" in self.rules[i]["rule_string"]:
                self.rules[i]["rule_string"] = self.rules[i]["rule_string"].replace("CTSH", "A change from any other subheading - CTSH")
                self.rules[i]["rule_string"] += "{{CTSH}}"

            # For Japan - RVC
            if "RVC" in self.rules[i]["rule_string"]:
                self.rules[i]["rule_string"] = self.rules[i]["rule_string"].replace("RVC", "Regional Value Content - RVC")

            if "wholly obtained" in self.rules[i]["rule_string"]:
                self.rules[i]["rule_string"] += "{{WO}}"

            if self.rules[i]["quota"]["amount"] is not None:
                self.rules[i]["description_string"] = self.rules[i]["description_string"] + "{{RELAX}}"

            self.rules[i]["rule_string"] = self.rules[i]["rule_string"].replace(" ;", ";")
            self.rules[i]["rule_string"] = self.rules[i]["rule_string"].replace("; ", ";\n\n")

            if self.rules[i]["description_string"][-10:] == "except for":
                self.rules[i]["description_string"] = self.rules[i]["description_string"][:-10]

            self.rules[i]["description_string"] = self.rules[i]["description_string"].strip()
            self.rules[i]["description_string"] = self.rules[i]["description_string"].strip(";")

    def fmt(self, s, do_markdown=True):
        footnote = ""
        if s is None:
            return ""
        else:
            # return s
            s = s.replace(' xmlns="http://trade.europa.eu"', '')
            s = s.replace(' xmlns:fn="http://www.w3.org/2005/xpath-functions"', '')
            s = s.replace(' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"', '')
            s = s.replace('</p>\n', '</p>')

            s = s.replace(" %", "%")
            s = s.replace(r'[ul]', '<ul>')
            s = s.replace(r'[\ul]', '</ul>')
            s = s.replace(r'[ol]', '<ol>')
            s = s.replace(r'[\ol]', '</ol>')
            s = s.replace(r'[bl]', '<li>')
            s = s.replace(r'[\bl]', '</li>')
            s = s.replace("<note-ref", " <note-ref")
            s = s.replace("\n                    ", " ")
            s = s.replace("\n                   ", " ")
            s = re.sub(r'\n[ ]{5,20}', '', s)
            s = s.replace(r'; or ', ";\n\nor\n\n")
            s = s.replace(r')', ") ")
            s = s.replace(r',', ", ")
            s = re.sub(r'[ \t]+', ' ', s)

            s = s.replace("<li><p>", "<li>")
            s = s.replace("</li> </ul>", "</li></ul>")

            # Get footnotes
            regex = r'<footnote-ref[^>]+>([^<]+)<\/footnote-ref>'
            match = re.search(regex, s)
            if match is not None:
                footnote = match.group(1).strip()
            s = re.sub(regex, '', s)
            s = s.strip()
            s = s.rstrip(":")

            s = s.replace("\n", " ")
            s = s.replace("  ", " ")

            # Convert the HTML into markdown
            if do_markdown:
                s = md(s)
            s = re.sub(r'\n\n\n', '\n\n', s, re.MULTILINE)
            if footnote != "":
                try:
                    s = s + ". " + self.footnotes[footnote]
                except Exception as e:
                    pass

            s = s.replace("()", "")
            s = s.replace("..", "")
            s = s.replace(":*", ":\n*")
            s = s.replace("* \n", "* ")
            s = s.replace("\n. ", "\n")
            s = s.replace("\n.", "\n")
            s = s.replace("\n", "\n\n")
            s = s.replace("\n\n\n", "\n\n")

            s = s.replace(" :", ":")
            s = re.sub(r'[\n]{1,5}:', ':', s, re.MULTILINE)
            s = re.sub(r'[ ]+,', ',', s, re.MULTILINE)

            s = md(s)

            return (s)

    def save_to_db(self):
        print("Saving to DB")
        for i in range(0, len(self.rules)):
            if self.rules[i]["idRule"] is not None:
                # First save the rule itself, if it needs to be saved
                d = Database()
                sql = """
                INSERT INTO roo.rules
                (
                    id_rule, scope, country_code, country_prefix,
                    heading, description, rule, alternate_rule,
                    quota_amount, quota_unit, key_first, key_last
                )
                VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id_rule) DO UPDATE SET
                (scope, country_code, country_prefix,
                heading, description, rule, alternate_rule,
                quota_amount, quota_unit, key_first, key_last, date_created)
                =
                (EXCLUDED.scope, EXCLUDED.country_code, EXCLUDED.country_prefix,
                EXCLUDED.heading, EXCLUDED.description, EXCLUDED.rule, EXCLUDED.alternate_rule,
                EXCLUDED.quota_amount, EXCLUDED.quota_unit, EXCLUDED.key_first, EXCLUDED.key_last, current_timestamp)
                """

                params = [
                    self.rules[i]["idRule"],
                    "xi",
                    self.country_code,
                    self.country_prefix,
                    self.key,
                    self.rules[i]["description_string"],
                    self.rules[i]["rule_string"],
                    self.rules[i]["alternate_rule_string"],
                    self.rules[i]["quota"]["amount"],
                    self.rules[i]["quota"]["unit"],
                    self.key_first,
                    self.key_last,
                ]
                d.run_query(sql, params)

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
                    self.rules[i]["idRule"],
                    "xi",
                    self.subheading,
                    self.country_prefix,
                ]
                d.run_query(sql, params)
                a = 1


class HeadingRange(object):
    def __init__(
        self,
        description,
        goods_nomenclature_item_id,
        heading_extents_dict,
        headings_dict
    ):
        self.description = description
        self.goods_nomenclature_item_id = goods_nomenclature_item_id
        self.heading_extents_dict = heading_extents_dict
        self.headings_dict = headings_dict
        self.key_min = None
        self.key_max = None

    def parse_description(self):
        self.description = self.description.replace("\n\t\t\t\t\t\t\t\t", " ")

        if self.description == "Missing description":
            self.description = 'The List of "Product-specific Rules of Origin" does not contain a description of the product at this point.'

        elif "-" in self.description:
            # Matches 01.02 - 01.09, here we are looking just for a range
            # which actually covers an entire chapter
            # self.description = self.description.replace(" ", "")
            parts = self.description.split("-")
            if len(parts) == 2:
                for i in range(0, len(parts)):
                    parts[i] = parts[i].strip()
                    parts[i] = parts[i].replace(".", "")
                chapter_match = False
                if len(parts[0]) == 4 and len(parts[1]) == 4:
                    self.key_min = parts[0]
                    self.key_max = parts[1]

                    # Check if this is actually the whole chapter but written as (e.g.) 0101-0106
                    self.chapter = self.goods_nomenclature_item_id[0:2]
                    if self.key_min == self.heading_extents_dict[self.chapter][0]:
                        if self.key_max == self.heading_extents_dict[self.chapter][len(self.heading_extents_dict[self.chapter]) - 1]:
                            chapter_match = True

                    if chapter_match:
                        comm_code = self.chapter.ljust(10, "0")
                        self.description = "Chapter " + \
                            str(int(self.chapter)) + " - " + \
                            self.headings_dict[comm_code].lower().capitalize()
                    else:
                        # this matches contiguous ranges of headings
                        chapter_extent = self.heading_extents_dict[self.chapter]
                        tmp = ""
                        match_count = 0
                        for heading in chapter_extent:
                            if heading >= self.key_min:
                                if heading <= self.key_max:
                                    match_count += 1

                        if match_count < 11:
                            for heading in chapter_extent:
                                if heading >= self.key_min:
                                    if heading <= self.key_max:
                                        try:
                                            tmp += heading + ": " + self.headings_dict[heading.ljust(10, "0")] + "\n\n"
                                        except Exception as e:
                                            print(heading)
                                            sys.exit()

                            self.description = tmp

        elif len(self.description) == 5:
            # Matches 04.01 etc.
            if "." in self.description:
                self.description = self.description.replace(".", "")
                if self.description.isdecimal():
                    comm_code = self.description.ljust(10, "0")
                    self.description = self.headings_dict[comm_code].lower().capitalize()

        elif len(self.description) == 7:
            # Matches 0402.10 etc.
            if "." in self.description:
                self.description = self.description.replace(".", "")
                if self.description.isdecimal():
                    comm_code_heading = self.description[0:4].ljust(10, "0")
                    comm_code_subheading = self.description.ljust(10, "0")
                    self.description = self.headings_dict[comm_code_heading].lower().capitalize()
                    self.description += " : "
                    self.description += self.headings_dict[comm_code_subheading].lower().capitalize()

        return self.description

from datetime import datetime
import os
import json
import re
from markdownify import markdownify as md
from classes.database import Database
from classes.footnote import Footnote
import logging
from bs4 import BeautifulSoup as bs

class ClassicRoo(object):
    def __init__(self, data, country, sub_heading, config):
        logging.basicConfig(filename='log/app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')
        self.data = data
        self.country = country
        self.sub_heading = sub_heading
        self.config = config
        self.schemes = []
        for scheme in self.data:
            scheme = ClassicRooScheme(scheme, country, sub_heading, config)
            self.schemes.append(scheme)
            a = 1
        
        a = 1
        # if self.config["save_to_db"]:
        #     self.save_to_db()

class ClassicRooScheme(object):
    def __init__(self, data, country, sub_heading, config):
        self.data = data
        self.country = country
        self.sub_heading = sub_heading
        self.config = config
        self.rules = self.data["rules"]
        self.cleanse_rules()
        self.save_rules()

    def cleanse_rules(self):
        if self.rules is None:
            self.rules = ""
        self.rules = self.rules + ""
        self.rules = re.sub(r"\n", " ", self.rules)
        self.rules = re.sub(r'<TR', "<tr", self.rules)
        self.rules = re.sub(r'<TD', "<td", self.rules)
        self.rules = re.sub(r'</TD>', "</td>", self.rules)
        self.rules = re.sub(r'</TR>', "</tr>", self.rules)
        self.rules = re.sub(r'<center>', "", self.rules)
        self.rules = re.sub(r"</center>", "", self.rules)
        self.rules = re.sub(r'<CHAPTER>', "", self.rules)
        self.rules = re.sub(r'</CHAPTER>', "", self.rules)
        self.rules = re.sub(r'<!-- required for colum width -->', "", self.rules)
        self.rules = re.sub(r'<tr[^>]*>', "<tr>", self.rules)
        self.rules = re.sub(r'<td[^>]*>', "<td>", self.rules)
        self.rules = re.sub(r'<th[^>]*>', "<th>", self.rules)
        self.rules = re.sub(r'<table[^>]*>', "<table>", self.rules)
        self.rules = re.sub(r'>[ ]+', ">", self.rules)
        self.rules = re.sub(r'[ ]+<', "<", self.rules)
        self.rules = re.sub(r'<div class=chapter>', "", self.rules)
        self.rules = re.sub(r'</div>', "", self.rules)
        self.rules = re.sub(r'<tr><td></table>', "</table>", self.rules)
        self.rules = re.sub(r'</td></td>', "</td>", self.rules)
        self.rules = re.sub(r'<tr><td></td><td></td><td></td><td></td></tr>', "", self.rules)

        self.rules = self.rules.strip()
        
        # Use Beautiful Soup to prettify
        soup = bs(self.rules, "lxml")
        self.rules = soup.prettify()

        # Then take out some of the unwanted replacements
        self.rules = re.sub(r'<t([dh])>\s*', r"<t\1>", self.rules)
        self.rules = re.sub(r'\s*</t([dh])>', r"</t\1>", self.rules)
        a = 1
    
    def save_rules(self):
        folder = os.getcwd()
        folder = os.path.join(folder, "resources")
        folder = os.path.join(folder, "json")
        folder = os.path.join(folder, self.country["code"])
        if not os.path.isdir(folder):
            os.mkdir(folder)
        file = os.path.join(
            folder, self.sub_heading + ".html")
        f = open(file, "w+")
        f.write(self.rules)
        f.close()
         
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
            a = 1
        elif "Chapter" in tmp:
            tmp = tmp.replace("Chapter", "")
            tmp = tmp.strip()
            if int(tmp) < 10:
                self.key_min = "0" + tmp
                self.key_max = "0" + tmp
            else:
                self.key_min = tmp
                self.key_max = tmp
            a = 1
        else:
            self.key_min = self.key
            self.key_max = self.key

        self.key_first = self.key_min + ("0" * (10 - len(self.key_min)))
        self.key_last = self.key_max + ("9" * (10 - len(self.key_max)))
        
    def format_rules_and_descriptions(self):
        for i in range(0, len(self.rules)):
            self.rules[i]["description_string"] = self.fmt(self.rules[i]["description"], do_markdown = False)
            self.rules[i]["rule_string"] = self.fmt(self.rules[i]["rule"])
            self.rules[i]["alternate_rule_string"] = self.fmt(self.rules[i]["alternateRule"])
        a = 1

    def fmt(self, s, do_markdown = True):
        footnote = ""
        if s is None:
            return ""
        else:
            s = s.replace(r'[ul]', '<ul>')
            s = s.replace(r'[\ul]', '</ul>')
            s = s.replace(r'[ol]', '<ol>')
            s = s.replace(r'[\ol]', '</ol>')
            s = s.replace(r'[bl]', '<li>')
            s = s.replace(r'[\bl]', '</li>')
            s = s.replace("<note-ref", " <note-ref")
            s = s.replace("\n                    ", " ")
            s = re.sub(r'\s+', ' ', s)
            # Get footnotes
            regex = r'<footnote-ref[^>]+>([^<]+)<\/footnote-ref>'
            match = re.search(regex, s)
            if match is not None:
                footnote = match.group(1).strip()
            s = re.sub(regex, '', s)
            s = s.strip()
            s = s.rstrip(":")
            if do_markdown:
                s = md(s)
            s = re.sub(r'\n\n\n', '\n\n', s, re.MULTILINE)
            if footnote != "":
                try:
                    s = s + ". " + self.footnotes[footnote]
                except:
                    pass

            s = s.replace("..", "")
            s = s.replace(":*", ":\n*")
            s = s.replace("\n. ", "\n")
            s = s.replace("\n.", "\n")
            s = s.replace("\n", "\n\n")
            s = s.replace("\n\n\n", "\n\n")
            
            
            
            return (s)
        
    def save_to_db(self):
        for i in range(0, len(self.rules)):
            if self.rules[i]["idRule"] is not None:
                # First save the rule itsefl, if it needs to be saved
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
                quota_amount, quota_unit, key_first, key_last)
                =
                (EXCLUDED.scope, EXCLUDED.country_code, EXCLUDED.country_prefix,
                EXCLUDED.heading, EXCLUDED.description, EXCLUDED.rule, EXCLUDED.alternate_rule,
                EXCLUDED.quota_amount, EXCLUDED.quota_unit, EXCLUDED.key_first, EXCLUDED.key_last)
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
                
                # Then save the realtionship with the subheading
                d = Database()
                sql = """
                INSERT INTO roo.rules_to_commodities
                (
                    id_rule, scope, sub_heading, country_prefix
                )
                VALUES
                (%s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                """
                
                params = [
                    self.rules[i]["idRule"],
                    "xi",
                    self.sub_heading,
                    self.country_prefix, 
                ]
                d.run_query(sql, params)
                a = 1
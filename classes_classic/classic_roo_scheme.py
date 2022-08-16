import os
import sys
import re
from markdownify import markdownify as md
from bs4 import BeautifulSoup as bs
from lxml import html
from lxml.cssselect import CSSSelector
from cssselect import GenericTranslator

from classes_classic.classic_roo_row import ClassicRooRow
from classes_classic.classic_roo_scheme_html import ClassicRooSchemeHtml
# from classes.footnote import Footnote


class ClassicRooScheme(object):
    # The ClassicRooScheme object is called against each of the downloaded raw JSON files
    # to generate a set of rows, made of cells that represent parsed RoO content
    def __init__(self, data, subheading, country_code, scheme_code):
        self.roo_rows = []
        self.data = data
        self.subheading = subheading
        self.country_code = country_code
        self.scheme_code = scheme_code
        self.rules = self.data["rules"]
        self.cleanse_rules()
        html_version = ClassicRooSchemeHtml(self.subheading, self.rules, self.country_code, self.scheme_code)
        self.get_table_rows()
        self.duplicate_rows_for_non_consecutive_headings()
        self.get_heading_min_max()
        self.get_rules_json()

    def get_table_rows(self):
        if self.rules is not None and self.rules != "":
            try:
                tree = html.fromstring(self.rules)
            except Exception as e:
                print("Error on document {}".format(self.subheading))
                sys.exit()
            self.table_rows = tree.cssselect('tr')

            # This just gets the maximum number of columns in the table
            # This needs to get passed into the row-parsing function
            # in case there are odd row or colspans
            max_number_of_columns_in_table = 0
            for table_row in self.table_rows:
                table_cells = table_row.cssselect('td')
                if len(table_cells) > max_number_of_columns_in_table:
                    max_number_of_columns_in_table = len(table_cells)

            # Loop through all the rows in the table and process them
            # Pass in the previous row, in case there is a need to use
            # come data from the previous row in the new row, i.e. where
            # a rowspan of greater than one has been used.
            previous_row = None
            row_index = 0
            for table_row in self.table_rows:
                table_cells = table_row.cssselect('td')
                table_cell_count = len(table_cells)
                if table_cell_count > 0:
                    new_row = ClassicRooRow(table_cells, row_index, max_number_of_columns_in_table, previous_row, self.subheading)
                    if new_row.valid:
                        self.roo_rows.append(new_row)
                        previous_row = new_row
                    row_index += 1

    def duplicate_rows_for_non_consecutive_headings(self):
        self.roo_rows2 = []
        for row in self.roo_rows:
            row.process_heading()
            for heading in row.heading_list:
                new_row = ClassicRooRow()
                new_row.heading_text = heading.strip()
                new_row.subdivision_text = row.subdivision_text
                new_row.rule_text = row.rule_text
                new_row.get_chapter(row.subheading)
                new_row.format_rules()
                new_row.valid = True
                self.roo_rows2.append(new_row)

    def get_heading_min_max(self):
        for row in self.roo_rows2:
            row.get_check_for_ex_code()
            row.get_heading_min_max()

    def get_rules_json(self):
        self.rules_json = []
        for row in self.roo_rows2:
            if row.is_ex_code:
                row.heading_text = "ex " + row.heading_text
            self.rules_json.append(row.as_dict())
        a = 1

    def cleanse_rules(self):
        # Standardises the content of the rules of origin cells in the rules node
        if self.rules is None:
            self.rules = ""
        self.rules = self.rules + ""
        if "calendering" in self.rules:
            a = 1

        self.rules = re.sub(r'\t', " ", self.rules)
        self.rules = re.sub("\\'fnB?[0-9]{1,3}\\'", "", self.rules)
        self.rules = re.sub("onclick=\"scrollToRoo\(\)\"", "", self.rules)
        self.rules = re.sub(' class="[^"]{1,50}"', "", self.rules)
        self.rules = re.sub(' id="[^"]{1,50}"', "", self.rules)
        self.rules = re.sub(' +>', ">", self.rules)
        self.rules = re.sub('<a>\[[0-9]+\]</a>', "", self.rules)
        self.rules = re.sub('<sup>', "", self.rules)
        self.rules = re.sub('</sup>', "", self.rules)
        self.rules = re.sub('<li>', "\nBULLET", self.rules)
        self.rules = re.sub('</li>', "\n", self.rules)
        self.rules = re.sub('<ul>', "\n", self.rules)
        self.rules = re.sub('</ul>', "\n", self.rules)

        self.rules = re.sub(r'<i>', "", self.rules)
        self.rules = re.sub(r'</i>', "", self.rules)
        self.rules = re.sub(r'<b>', "", self.rules)
        self.rules = re.sub(r'</b>', "", self.rules)
        self.rules = re.sub(r'<em>', "", self.rules)
        self.rules = re.sub(r'</em>', "", self.rules)
        self.rules = re.sub(r'<strong>', "", self.rules)
        self.rules = re.sub(r'</strong>', "", self.rules)
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
        self.rules = re.sub(r' width="[0-9]*"', "", self.rules)
        self.rules = re.sub(r' width=[0-9]*%', "", self.rules)
        self.rules = re.sub(r' class="chapter"', "", self.rules)
        self.rules = re.sub(r'<td><br/></td>', "<td>&nbsp;</td>", self.rules)
        self.rules = re.sub(r'wholly\nobtained', "wholly obtained", self.rules)
        self.rules = re.sub(r'<th[^>]*>', "<th>", self.rules)
        self.rules = re.sub(r'<table[^>]*>', "<table>", self.rules)
        self.rules = re.sub(r'>[ ]+', ">", self.rules)
        self.rules = re.sub(r'[ ]+<', "<", self.rules)
        self.rules = re.sub(r'<div class=chapter>', "", self.rules)
        self.rules = re.sub(r'</div>', "", self.rules)
        self.rules = re.sub(r'<tr><td></table>', "</table>", self.rules)
        self.rules = re.sub(r'</td></td>', "</td>", self.rules)
        self.rules = re.sub(r'<tr><td></td><td></td><td></td><td></td></tr>', "", self.rules)
        self.rules = re.sub(r' class="Normal_Left"', "", self.rules)
        self.rules = re.sub(r'<td><div>', "<td>", self.rules)
        self.rules = re.sub(r'</div></td>', "</td>", self.rules)
        self.rules = re.sub(r'\s{1,100}<a class=\"pointer\" id=\"fnB[0-9]{1,3}\" onclick=\"[^\"]+\\">\s{1,100}\[[0-9]{1,3}\]\s{1,100}</a>\s{1,100}', " ", self.rules)
        self.rules = re.sub(r'<a class=\"pointer\" id=\"fnB[0-9]{1,3}\" onclick=\"scrollToRoo', " ", self.rules)
        self.rules = re.sub(r' class="?roo"?', "", self.rules)
        self.rules = re.sub(r' ROWSPAN=1', "", self.rules, flags=re.IGNORECASE)
        self.rules = re.sub(r' COLSPAN=1', "", self.rules, flags=re.IGNORECASE)
        self.rules = re.sub(r' VALIGN="TOP"', "", self.rules, flags=re.IGNORECASE)
        self.rules = re.sub(r'<td\s+>', "<td>", self.rules)
        self.rules = re.sub(r'<td>\s+<div>', "<td>", self.rules)
        self.rules = re.sub(r'\<td\>\<div\>', "<td>", self.rules)
        self.rules = re.sub(r'<td></td>', "<td>&nbsp;</td>", self.rules)

        self.rules = self.rules.replace("BULLET", "-")
        self.rules = self.rules.replace("Chapter s ", "Chapters ")
        self.rules = self.rules.replace(" %", "%")

        self.rules = self.rules.strip()

        # Use Beautiful Soup to prettify
        soup = bs(self.rules, "lxml")
        self.rules = soup.prettify()

        # Then take out some of the unwanted replacements
        self.rules = re.sub(r'<t([dh])>\s*', r"<t\1>", self.rules)
        self.rules = re.sub(r'\s*</t([dh])>', r"</t\1>", self.rules)

        # Get rid of footnotes
        # self.rules = re.sub(r"\('fn[0-9]*'\)\"&gt;[[0-9]*]", "", self.rules)
        self.rules = re.sub(r"<td><br/></td>", "<td>&nbsp;</td>", self.rules)

        # Try again to sort out rogue divs
        self.rules = re.sub(r'</div>\s+</td>', '</td>', self.rules)
        self.rules = re.sub(r'</div></td>', '</td>', self.rules)
        self.rules = re.sub(r'<td>\s+<div>', '<td>', self.rules)
        self.rules = re.sub(r'<td colspan="([0-9])">\s+<div>', '<td colspan="\\1">', self.rules)
        self.rules = re.sub(r'<td></td>', "<td>&nbsp;</td>", self.rules)

        # Must get rid of all divs and spans
        self.rules = re.sub(r'<div[^>]+>', '', self.rules)
        self.rules = re.sub(r'</div>', '', self.rules)
        self.rules = re.sub(r'<span[^>]+>', '', self.rules)
        self.rules = re.sub(r'</span>', '', self.rules)
        a = 1

    def parse_key(self):
        # Function not used
        tmp = self.key

        if " and " in self.key:
            self.key = self.key.replace("and", "-")

        if "-" in self.key:
            self.key = self.key.replace(" ", "")
            parts = self.key.split("-")
            self.key_min = parts[0]
            self.key_max = parts[1]
        elif "Chapter" in tmp:
            tmp = tmp.replace("Chapter", "")
            tmp = tmp.strip()
            if int(tmp) < 10:
                self.key_min = "0" + tmp
                self.key_max = "0" + tmp
            else:
                self.key_min = tmp
                self.key_max = tmp
        else:
            self.key_min = self.key
            self.key_max = self.key

        self.key_first = self.key_min + ("0" * (10 - len(self.key_min)))
        self.key_last = self.key_max + ("9" * (10 - len(self.key_max)))

    def format_rules_and_descriptions(self):
        for i in range(0, len(self.rules)):
            self.rules[i]["description_string"] = self.fmt(self.rules[i]["description"], convert_to_markdown=False)
            self.rules[i]["rule_string"] = self.fmt(self.rules[i]["rule"])
            self.rules[i]["alternate_rule_string"] = self.fmt(self.rules[i]["alternateRule"])

    def fmt(self, s, convert_to_markdown=True):
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
            if convert_to_markdown:
                s = md(s)
            s = re.sub(r'\n\n\n', '\n\n', s, re.MULTILINE)
            if footnote != "":
                try:
                    s = s + ". " + self.footnotes[footnote]
                except Exception as e:
                    pass

            s = s.replace("..", "")
            s = s.replace(":*", ":\n*")
            s = s.replace("\n. ", "\n")
            s = s.replace("\n.", "\n")
            s = s.replace("\n", "\n\n")
            s = s.replace("\n\n\n", "\n\n")

            return (s)

    def get_rule_sets(self):
        rule_sets = []
        for row in self.roo_rows:
            obj = {}
            obj["min"] = row.key_first
            obj["max"] = row.key_last
            rule_sets.append(obj)

        return rule_sets

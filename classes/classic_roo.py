from datetime import datetime
import os
import sys
import re
from markdownify import markdownify as md
import logging
from bs4 import BeautifulSoup as bs
from lxml import html
from lxml.etree import XPath
from lxml.cssselect import CSSSelector
from cssselect import GenericTranslator

from classes.database import Database
from classes.footnote import Footnote
import classes.globals as g


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


class ClassicRooScheme(object):
    def __init__(self, data, country, sub_heading, config):
        self.clear_db()
        self.roo_rows = []
        self.data = data
        self.country = country
        self.sub_heading = sub_heading
        self.config = config
        self.rules = self.data["rules"]
        self.setup_styles()
        self.cleanse_rules()
        self.save_rules_to_html()
        self.deconstruct_rules_html()
        self.sort_roo_rules()
        self.save_rules_to_db()
        
    def clear_db(self):
        return
        print("Clearing")
        sql = """
        delete from roo.rules r where country_prefix = 'gsp';
        """
        d = Database()
        params = [
        ]
        d.run_query(sql, params)

    def sort_roo_rules(self):
        return
        try:
            self.roo_rows = sorted(self.roo_rows, key=lambda x: key_first)
        except:
            a = 1

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
        self.rules = re.sub(r' width="[0-9]*"', "", self.rules)
        self.rules = re.sub(r' width=[0-9]*%', "", self.rules)
        self.rules = re.sub(r' class="chapter"', "", self.rules)
        self.rules = re.sub(r'<td><br/></td>', "<td>&nbsp;</td>", self.rules)

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
        
        self.rules = self.rules.strip()
        
        # Use Beautiful Soup to prettify
        soup = bs(self.rules, "lxml")
        self.rules = soup.prettify()

        # Then take out some of the unwanted replacements
        self.rules = re.sub(r'<t([dh])>\s*', r"<t\1>", self.rules)
        self.rules = re.sub(r'\s*</t([dh])>', r"</t\1>", self.rules)
        
        # Add in the styles
        self.rules = re.sub(r'<body>', self.styles + "<body>", self.rules)

        # Get rid of footnotes
        self.rules = re.sub(r"\('fn[0-9]*'\)\"&gt;[[0-9]*]", "", self.rules)
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

    def save_rules_to_html(self):
        # Save the rules to an HTML file
        # This is probably an interim step that will be superseded
        # by some sort of lxml wizardry
        folder = os.getcwd()
        folder = os.path.join(folder, "resources")
        folder = os.path.join(folder, "json")
        folder = os.path.join(folder, self.country["code"])
        if not os.path.isdir(folder):
            os.mkdir(folder)
        file = os.path.join(folder, self.sub_heading + ".html")
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
            self.rules[i]["description_string"] = self.fmt(self.rules[i]["description"], do_markdown = False)
            self.rules[i]["rule_string"] = self.fmt(self.rules[i]["rule"])
            self.rules[i]["alternate_rule_string"] = self.fmt(self.rules[i]["alternateRule"])

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
        # This is not live code
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
                
                # Then save the relationship with the subheading
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
                
    def setup_styles(self):
        self.styles = """
        <head>
        <style type='text/css'>
        body { font-family: calibri, arial;}
        table { border:1px solid black;}
        td { border:1px solid black; }
        th { background-color:black; color: white}
        </style>
        </head>
        """
        
    def deconstruct_rules_html(self):
        if self.rules is not None and self.rules != "":
            try:
                tree = html.fromstring(self.rules)
            except:
                print("Error on document {}".format(self.sub_heading))
                sys.exit()
            self.table_rows = tree.cssselect('tr')

            # First, we need to go through the table rows and work out what to
            # do if there are rowspans and colspans, which will cause issues otherwise

            column_max = 0
            for table_row in self.table_rows:
                table_cells = table_row.cssselect('td')
                if len(table_cells) > column_max:
                    column_max = len(table_cells)

            previous_row = None
            row_count = 0
            for table_row in self.table_rows:
                table_cells = table_row.cssselect('td')
                if len(table_cells) > 0:
                    new_row = ClassicRooRow(table_cells, row_count, column_max, previous_row, self.sub_heading, self)
                    if new_row.valid:
                        self.roo_rows.append(new_row)
                        previous_row = new_row
                    row_count += 1
                    
    def save_rules_to_db(self):
        # return
        """
        id_rule needs to be autoincrementing for classic RoO
        scope
        country_code
        country_prefix
        heading
        description
        quota_amount
        quota_unit
        alternate_rule
        date_created
        """
        a = g.id_rule
        
        for row in self.roo_rows:
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
                g.id_rule,
                "xi",
                "gsp",
                "gsp", 
                row.cells[0].text.strip(),
                row.cells[1].text.strip(),
                row.cells[2].text.strip(),
                None,
                None,
                None,
                row.key_first,
                row.key_last
            ]
            d.run_query(sql, params)    
            g.id_rule += 1
            

class ClassicRooRow(object):
    def __init__(self, table_cells = None, row_count = None, column_max = None, previous_row = None, sub_heading = None, parent = None):
        self.cells = []
        self.key_first = -1
        self.key_last = -1
        
        
        if table_cells is not None:
            self.row_count = row_count
            self.column_max = column_max
            self.table_cells = table_cells
            self.sub_heading = sub_heading
            self.column_count = len(self.table_cells)
            self.parent = parent
            
            if self.column_count == 1:
                self.valid = False
            else:
                self.valid = True
                self.previous_row = previous_row
                self.sub_heading = sub_heading
                self.normalise_cells()
                self.validate_row()
                self.get_key_first_and_last()
                self.delete_unwanted_variables()
        else:
            self.sub_heading = None
           
            
    def get_key_first_and_last(self):
        if self.valid:
            self.cells[0].text = self.cells[0].text.replace(" to ", " - ")
            self.cells[0].text = self.cells[0].text.replace("-", " - ")
            self.cells[0].text = self.cells[0].text.replace(";", ",")
            self.cells[0].text = self.cells[0].text.replace(",", ", ")
            self.cells[0].text = self.cells[0].text.replace("  ", " ")
            self.cells[0].text = self.cells[0].text.strip()
            
            if "Chapter" in self.cells[0].text:
                tmp = self.cells[0].text.replace("Chapter", "")
                tmp = tmp.replace("ex ", "").strip()
                tmp = tmp.rjust(2, "0")
                self.key_first = tmp + "00000000"
                self.key_last = tmp + "99999999"
                a = 1
            else:
                if " - " in self.cells[0].text:
                    tmp = self.cells[0].text.replace("ex ", "")
                    parts = tmp.split(" - ")
                    for part in parts:
                        part = part.replace(" ", "")
                        part = part.replace(".", "")

                    self.key_first = parts[0] + "0" * (10 - len(parts[0]))
                    self.key_last = parts[1] + "9" * (10 - len(parts[1]))
                        
                    a = 1
                else:
                    tmp = self.cells[0].text.replace("ex ", "")
                    tmp = tmp.replace(" ", "")
                    tmp = tmp.replace(".", "")
                    self.key_first = tmp + "0" * (10 - len(tmp))
                    self.key_last = tmp + "9" * (10 - len(tmp))
                    a = 1
        a = 1
            
    def delete_unwanted_variables(self):
        del self.table_cells
        del self.previous_row
        del self.row_count
        del self.column_max
        del self.column_count
        del self.sub_heading
        
    def normalise_cells(self):
        index = 0
        for table_cell in self.table_cells:
            cell = ClassicRooCell(table_cell, index)
            index += 1
            self.cells.append(cell)
            
    def validate_row(self):
        # Where the previous row has a rowspan greater than one, repeat that row's value in the next row
        if self.previous_row is not None:
            cell_index = 0
            for cell in self.previous_row.cells:
                if cell.rowspan > 1:
                    self.cells.insert(cell_index, cell)
                    self.cells[cell_index].rowspan = cell.rowspan - 1
                cell_index += 1
        
        # If there are 4 cells, then add 4 onto 3
        if len(self.cells) == 4:
            if self.cells[2].text != "" and self.cells[3].text != "":
                self.cells[2].text = self.cells[2].text + "\n\n" + self.cells[3].text
                # self.cells[3].text = ""
                self.cells.pop(3)
                
        self.valid = False
        for cell in self.cells:
            if cell.text != "":
                self.valid = True
                break
            
        # Check for "ands" and commas in the row (classification)
        found = True
        while found:
            if "and" in self.cells[0].text:
                parts = self.cells[0].text.split(" and ")
                new_row = ClassicRooRow()

                cl0 = ClassicRooCell()
                cl1 = ClassicRooCell()
                cl2 = ClassicRooCell()

                cl0.set_text(parts[len(parts) - 1])
                cl1.set_text(self.cells[1].text)
                cl2.set_text(self.cells[2].text)

                new_row.apply_cells(cl0, cl1, cl2)
                self.parent.roo_rows.append(new_row)
                self.cells[0].text = parts[0]
                a = 1
                
            elif "," in self.cells[0].text:
                if self.cells[0].text.count(",") == 1:
                    parts = self.cells[0].text.split(",") 
                    for part in parts:
                        part = part.strip()
                        
                    if ("ex" not in parts[0]) and ("ex" not in parts[1]) and (int(parts[1]) - int(parts[0]) == 1):
                        # There is one comma and the items are actually only 1 code apart, therefore a "-" is more appropriate
                        self.cells[0].text = self.cells[0].text.replace(",", " - ")
                        self.cells[0].text = self.cells[0].text.replace("  ", " ")
                    else:
                        # There is one comma and the items are more distant than 1 code apart
                        parts = self.cells[0].text.split(",") 
                        for part in parts:
                            part = part.strip()
                            
                        
                        for part_index in range(1, len(parts)):
                            part = parts[part_index]
                            new_row = ClassicRooRow()

                            cl0 = ClassicRooCell()
                            cl1 = ClassicRooCell()
                            cl2 = ClassicRooCell()

                            cl0.set_text(part)
                            cl1.set_text(self.cells[1].text)
                            cl2.set_text(self.cells[2].text)

                            new_row.apply_cells(cl0, cl1, cl2)
                            self.parent.roo_rows.append(new_row)

                        self.cells[0].text = parts[0]
                        
                else:
                    # There is more than a single comma, in this case it is just simpler to create multiple rows,
                    # and not try and join those together where the items are just one apart
                    a = 1
                    parts = self.cells[0].text.split(",") 
                    for part in parts:
                        part = part.strip()
                        
                    
                    for part_index in range(1, len(parts)):
                        part = parts[part_index]
                        new_row = ClassicRooRow()

                        cl0 = ClassicRooCell()
                        cl1 = ClassicRooCell()
                        cl2 = ClassicRooCell()

                        cl0.set_text(part)
                        cl1.set_text(self.cells[1].text)
                        cl2.set_text(self.cells[2].text)

                        new_row.apply_cells(cl0, cl1, cl2)
                        self.parent.roo_rows.append(new_row)
                        
                        a = 1
                        
                    # Last bit
                    self.cells[0].text = parts[0]
                    a = 1
                        
                    
                pass
            else:
                found = False
                break
        
    def apply_cells(self, cl0, cl1, cl2):
        self.cells.append(cl0)
        self.cells.append(cl1)
        self.cells.append(cl2)
        self.valid = True
        self.column_count = 3
        self.get_key_first_and_last()

class ClassicRooCell(object):
    def __init__(self, table_cell = None, index = 0):
        if table_cell is not None:
            self.table_cell = table_cell
            self.rowspan = int(self.table_cell.get("rowspan") or 1)
            self.colspan = int(self.table_cell.get("colspan") or 1)
            self.format_cell_content(index)
            del self.table_cell
            
    def format_cell_content(self, index):
        self.text = md((self.table_cell.text or "").strip())
        self.text = self.text.replace('\xa0', '')
        if index == 0:
            self.text = self.text.replace(';', ',')
        
    def set_text(self, text):
        self.rowspan = 1
        self.colspan = 1
        self.text = text
        
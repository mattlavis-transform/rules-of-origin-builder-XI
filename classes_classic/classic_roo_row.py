import re
from markdownify import markdownify as md

from classes_classic.classic_roo_cell import ClassicRooCell
from classes_classic.classic_roo_rule import ClassicRooRule
import classes.globals as g


class ClassicRooRow(object):
    def __init__(self, table_cells=None, row_count=None, column_max=None, previous_row=None, subheading=None):
        self.cells = []
        self.key_min = 0
        self.key_max = 0
        self.is_ex_code = False
        self.heading_text = ""
        self.subdivision_text = ""
        self.rule_text = ""
        self.cells = []
        self.previous_row = previous_row

        if table_cells is not None:
            self.row_count = row_count
            self.column_max = column_max
            self.table_cells = table_cells
            self.subheading = subheading
            self.column_count = len(self.table_cells)

            if self.column_count < 2:
                self.valid = False
            else:
                self.valid = True
                self.previous_row = previous_row
                self.subheading = subheading
                self.normalise_cells()
                self.validate_row()
                self.assign_cells_to_objects()
                self.format_subdivision()
                self.format_heading_text()
                self.carry_over_heading()
                self.formal_rules_final()
                self.delete_unwanted_variables()
        else:
            self.subheading = None
            self.valid = False

    def formal_rules_final(self):
        self.rule_text = self.rule_text.replace("and \n", "and\n")
        self.rule_text = self.rule_text.replace(" and\n-", " *and*\n-")
        self.rule_text = self.rule_text.replace("- - ", "- ")
        self.rule_text = self.rule_text.replace("\n ", "\n")
        self.rule_text = self.rule_text.replace("acrylic\n\nyarn", "acrylic yarn")
        self.rule_text = self.rule_text.replace("coating\n\nOnly", "coating. Only")
        self.rule_text = self.rule_text.replace("and/or", "and&nbsp;/&nbsp;or")
        self.rule_text = self.rule_text.replace("or\n", "or ")
        self.rule_text = self.rule_text.replace("\n\n\n", "\n\n")
        self.rule_text = self.rule_text.replace("9\ndecitex", "9 decitex")
        self.rule_text = self.rule_text.replace("decitex,\n\nmay", "decitex, may")
        self.rule_text = self.rule_text.replace("fabric\nformation", "fabric\nformation")
        self.rule_text = self.rule_text.replace("of\n\nm\n\n-phenylenediamine", "of m-phenylenediamine")
        self.rule_text = self.rule_text.replace("\npoly(\n\np\n\n-phenylene\n", "poly (p-phenylene ")
        self.rule_text = self.rule_text.replace("Chapter ruleapplies", "Chapter rule applies")
        self.rule_text = re.sub("\n-([^ ])", "\n- \\1", self.rule_text)
        self.rule_text = self.rule_text.replace("\n-  ", "\n- ")
        self.rule_text = self.rule_text.replace("headings Nos", "headings")
        self.rule_text = self.rule_text.replace("heading No", "heading")
        self.rule_text = self.rule_text.replace(" or \n- ", " *or*\n\n- ")

        # This is meant to remove all single \n combos.
        # \n\nor\n\n
        self.rule_text = self.rule_text.replace("or \n", "or\n")
        self.rule_text = self.rule_text.replace("\n\nor\n", "\n\nor\n\n")
        self.rule_text = self.rule_text.replace("\nor\n- ", "\n\nor\n\n- ")
        self.rule_text = self.rule_text.replace("\n\n\n", "\n\n")
        self.rule_text = self.rule_text.replace("\n\nor\n\n", "TEMPOR")
        self.rule_text = re.sub(r"([^\n])\n([^\n])", "\\1 \\2", self.rule_text)
        self.rule_text = self.rule_text.replace(" \n", "\n")
        self.rule_text = self.rule_text.replace("TEMPOR", "\n\nor\n\n")

        if "formation" in self.rule_text:
            a = 1

        self.rule_text = self.rule_text.replace(",\n", "\n")

        self.rule_text = re.sub("([0-9]{1,2}),([0-9]{1,2})%", "\\1.\\2%", self.rule_text)

        # self.rule_text = self.rule_text + "."
        self.rule_text = self.rule_text.strip()

    def format_subdivision(self):
        self.subdivision_text = self.subdivision_text.replace("except\nfor:", "except for")
        self.subdivision_text = self.subdivision_text.replace("except for:", "")
        self.subdivision_text = self.subdivision_text.replace("except for", "")
        self.subdivision_text = self.subdivision_text.replace("- - ", "- ")
        self.subdivision_text = self.subdivision_text.strip()
        self.subdivision_text = self.subdivision_text.rstrip(";")

    def carry_over_heading(self):
        self.is_heading = False
        if self.valid:
            if len(self.cells) == 3:
                if self.cells[2].text == '':
                    self.is_heading = True
            elif len(self.cells) == 4:
                if self.cells[2].text == '' and self.cells[3].text == '':
                    self.is_heading = True

        if self.is_heading:
            g.heading_carry_over = self.cells[1].text
            # self.valid = False
        else:
            g.heading_carry_over = ""

    def format_rules(self):
        self.rules = []
        self.rule_text = self.rule_text.replace("or \n", "or\n")
        self.rule_text = self.rule_text.replace("\n \n", "\n\n")
        self.rule_text = self.rule_text.replace("\n\nor\n", "\n\nor\n\n")
        self.rule_text = self.rule_text.replace("\n\n\n", "\n\n")
        self.rule_text = self.rule_text.replace("\n or", "\nor")
        self.rule_text = self.rule_text.replace("\n\nOr\n\n", "\n\nor\n\n")
        self.rule_text = re.sub("\[[0-9]{1,3}\]", "", self.rule_text)
        # self.rule_text = self.rule_text.replace("ORDIVIDER", "\n\nor\n\n")
        parts = self.rule_text.split("\n\nor\n\n")
        if len(parts) > 1:
            for part in parts:
                rule = ClassicRooRule(part)
                self.rules.append(rule.as_dict())
        else:
            rule = ClassicRooRule(self.rule_text)
            self.rules.append(rule.as_dict())

        self.rules_json = []
        for rule in self.rules:
            if rule["rule"] != "":
                self.rules_json.append(rule)

    def assign_cells_to_objects(self):
        if self.valid:
            self.heading_text = self.cells[0].text
            if g.heading_carry_over != "":
                # Carry over the 'heading' text from the previous row
                self.subdivision_text = g.heading_carry_over
                self.subdivision_text += self.cells[1].text
            else:
                self.subdivision_text = self.cells[1].text

            if len(self.cells) > 2:
                self.rule_text = self.cells[2].text
            else:
                self.rule_text = ""
                if self.heading_text == "":
                    if self.subdivision_text == "":
                        if self.rule_text == "":
                            self.valid = False

    def process_heading(self):
        self.heading_list = [self.heading_text]
        if " and " in self.heading_text:
            self.heading_list = self.heading_text.split("and")
        if "," in self.heading_text:
            self.heading_list = self.heading_text.split(",")

    def format_heading_text(self):
        self.heading_text = self.heading_text.replace("\n", " ")
        self.heading_text = self.heading_text.replace(" to ", " - ")
        self.heading_text = self.heading_text.replace("-", " - ")
        self.heading_text = self.heading_text.replace(";", ",")
        self.heading_text = self.heading_text.replace(",", ", ")
        self.heading_text = self.heading_text.replace("  ", " ")
        self.heading_text = self.heading_text.strip()

    def get_check_for_ex_code(self):
        if "ex" in self.heading_text:
            self.is_ex_code = True
        else:
            self.is_ex_code = False

        self.heading_text = self.heading_text.replace("ex", "").strip()

    def get_chapter(self, subheading):
        self.subheading = subheading
        self.chapter = int(self.subheading.replace("chapter_", ""))
        a = 1

    def get_heading_min_max(self):
        if self.valid:
            self.heading_text = self.heading_text.strip()
            if "Chapter" in self.heading_text:
                tmp = self.heading_text.replace("Chapter", "")
                tmp = tmp.replace("ex ", "").strip()
                tmp = tmp.rjust(2, "0")
                self.key_min = tmp + "00000000"
                self.key_max = tmp + "99999999"
                a = 1
            else:
                if " - " in self.heading_text:
                    tmp = self.heading_text.replace("ex ", "")
                    tmp = self.heading_text.replace("ex", "")
                    parts = tmp.split(" - ")
                    for part in parts:
                        part = part.replace(" ", "")
                        part = part.replace(".", "")

                    self.key_min = parts[0] + "0" * (10 - len(parts[0]))
                    self.key_max = parts[1] + "9" * (10 - len(parts[1]))

                else:
                    tmp = self.heading_text.replace("ex ", "")
                    tmp = tmp.replace(" ", "")
                    tmp = tmp.replace(".", "")
                    self.key_min = tmp + "0" * (10 - len(tmp))
                    self.key_max = tmp + "9" * (10 - len(tmp))

    def delete_unwanted_variables(self):
        del self.table_cells
        del self.previous_row
        del self.row_count
        del self.column_max
        del self.column_count
        # del self.subheading
        # del self.cells

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
                self.cells[2].text = self.cells[2].text + "\n\nor\n\n" + self.cells[3].text
                self.cells.pop(3)

        # Rows are considered to be valid if there is anything in any of the cells
        self.valid = False
        for cell in self.cells:
            if cell.text != "":
                self.valid = True
                break

        # However, if it is just a list of (1), (2) etc then it is invalid
        if "(1)" in self.cells[0].text:
            self.valid = False

    def as_dict(self):
        s = {
            "heading": self.heading_text,
            "chapter": self.chapter,
            "subdivision": self.subdivision_text,
            "min": self.key_min,
            "max": self.key_max,
            "rules": self.rules_json,
            "valid": True
        }
        return s

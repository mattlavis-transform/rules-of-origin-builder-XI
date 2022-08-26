import re
import os
from markdownify import markdownify as md
from dotenv import load_dotenv


import classes.globals as g


class ProductRooRuleComponent(object):
    def __init__(self, heading, description, text, idRuleComponent, type, process_no_component_rules=False):
        load_dotenv('.env')
        self.insert_hyperlinks = int(os.getenv('INSERT_HYPERLINKS'))
        self.heading = heading
        self.description = description
        self.text = text
        self.idRuleComponent = idRuleComponent
        self.type = type

        self.format_fields()
        self.format_rule_text()
        if process_no_component_rules:
            self.format_rule_text_no_components()

    def format_rule_text(self):
        self.text = self.text.replace('\u2013', '-')
        self.text = re.sub('<footnote-ref code=\"[0-9]+\">[0-9]+</footnote-ref>', "", self.text)
        self.text = re.sub("\[footnote=\"[0-9]+\"\]", "", self.text)
        self.text = self.text.replace("and [\\bl]", "*and* [\\bl]")
        self.text = self.text.replace("[\\bl]", "")
        self.text = self.text.replace("[ul]", "")
        self.text = self.text.replace("[\\ul]", "\n\n")
        self.text = self.text.replace("[bl]", "\n\n- ")
        self.text = re.sub("\(([a-z])\)", "\\1)", self.text)
        self.text = self.text.replace(" ,", ",")
        self.text = self.text.replace(" .", ".")
        self.text = self.text.replace("nonwoven", "non-woven")
        # self.text = self.text.replace("and/or", "*and&nbsp;/&nbsp;or*")
        self.text = self.text.replace(" %", "%")
        self.text = self.text.replace(" \u00b0", "\u00b0")
        self.text = re.sub(r'\[footnote=\"[A-Z0-9]+\"\]', "", self.text)
        self.text = re.sub(r'-  (i+)\)', "   - \\1)", self.text)
        self.text = re.sub(r'-  \((i+)\)', "   - \\1)", self.text)
        self.text = re.sub(" ([0-9]+%) ", " **\\1** ", self.text)

        self.text = self.text.replace("-  ", "- ")
        self.text = self.text.replace("- - ", "- ")
        self.text = self.text.rstrip(";")

        self.text = self.text.strip()
        self.insert_the_hyperlinks()

    def insert_the_hyperlinks(self):
        if self.insert_hyperlinks == 0:
            return
        # Lower case the term Chapter in PSRs
        self.text = re.sub("Chapter", "chapter", self.text)

        # Where there are lists of chapters ...
        self.text = re.sub(" chapters ([0-9]{1,2}) and ([0-9]{1,2})", " chapter \\1 and chapter \\2 ", self.text)
        self.text = re.sub(" chapters ([0-9]{1,2}) or ([0-9]{1,2})", " chapter \\1 or chapter \\2 ", self.text)

        # Where there are lists of headings ...
        self.text = re.sub(" ([0-9]{4}) or ([0-9]{4})", " \\1 or heading \\2 ", self.text)
        self.text = re.sub(" heading ([0-9]{4}), ([0-9]{4})", " heading \\1, heading \\2 ", self.text)

        # Insert hyperlinks to chapters: mid rule
        self.text = re.sub(" ([Cc])hapter ([1-9][0-9])([ ,])", " [\\1hapter \\2](/chapters/\\2)\\3", self.text)
        self.text = re.sub(" ([Cc])hapter ([0-9])([ ,.])", " [\\1hapter \\2](/chapters/0\\2)\\3", self.text)

        # Insert hyperlinks to chapters: end of rule
        self.text = re.sub(" ([Cc])hapter ([1-9][0-9])$", " [\\1hapter \\2](/chapters/\\2)", self.text)
        self.text = re.sub(" ([Cc])hapter ([0-9])$", " [\\1hapter \\2](/chapters/0\\2)", self.text)

        # Insert hyperlinks to headings: mid rule
        self.text = re.sub(" ([Hh])eading ([0-9]{4})([, ])", " [\\1eading \\2](/headings/\\2)\\3", self.text)
        # Insert hyperlinks to headings: end of rule
        self.text = re.sub(" ([Hh])eading ([0-9]{4})$", " [\\1eading \\2](/headings/\\2)", self.text)

    def format_rule_text_no_components(self):
        self.text = self.text.replace(' xmlns=\"http://trade.europa.eu\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"', "")
        self.text = self.text.replace("\n", "")
        self.text = self.text.replace(" %", "%")
        self.text = self.text.replace("\u00a0%", "%")
        if "3824" in self.heading:
            a = 1

        self.text = md(self.text)
        if "ORDIVIDER" in self.text:
            self.text = self.text.replace("ORDIVIDER", "\n\nor\n\n")
            a = 1

    def format_fields(self):
        self.description = g.process_description(self.description)
        if "ex" in self.heading:
            self.is_ex_code = True
        else:
            self.is_ex_code = False

        self.heading = self.heading.replace("ex", "")
        self.heading = self.heading.strip()

        if self.is_ex_code:
            self.heading = "ex " + self.heading

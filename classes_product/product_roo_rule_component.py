import re
from markdownify import markdownify as md

import classes.globals as g


class ProductRooRuleComponent(object):
    def __init__(self, heading, description, text, idRuleComponent, type, process_no_component_rules=False):
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
        self.text = self.text.replace("and/or", "*and / or*")
        self.text = self.text.replace(" %", "%")
        self.text = self.text.replace(" \u00b0", "\u00b0")
        self.text = re.sub(r'\[footnote=\"[A-Z0-9]+\"\]', "", self.text)
        self.text = re.sub(r'-  (i+)\)', "   - \\1)", self.text)
        self.text = re.sub(r'-  \((i+)\)', "   - \\1)", self.text)

        self.text = self.text.replace("-  ", "- ")
        self.text = self.text.replace("- - ", "- ")
        self.text = self.text.rstrip(";")

        self.text = self.text.strip()

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

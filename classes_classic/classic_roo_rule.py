from markdownify import markdownify as md


class ClassicRooRule(object):
    def __init__(self, rule_text):
        self.rule_classes = []
        self.rule_text = rule_text
        self.format_rule()
        self.get_rule_class()

    def format_rule(self):
        self.rule_text = self.rule_text.replace("\n ", "\n")
        self.rule_text = self.rule_text.replace("\n\n\n", "\n\n")

    def get_rule_class(self):
        if "wholly obtained" in self.rule_text:
            self.rule_classes.append("WO")

    def as_dict(self):
        # s = {
        #     "rule": self.rule_text,
        #     "class": self.rule_classes,
        #     "operator": None,
        #     "specific_processes": False,
        #     "double_dash": False
        # }
        s = {
            "rule": self.rule_text,
            "class": self.rule_classes,
            "operator": None
        }
        return s

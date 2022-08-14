import logging

from classes.classic_roo_scheme import ClassicRooScheme
import classes.globals as g


class ClassicRoo(object):
    def __init__(self, data, subheading, country_code, scheme_code):
        self.data = data
        self.subheading = subheading
        self.country_code = country_code
        self.scheme_code = scheme_code
        self.rules_json = []
        for scheme in self.data:
            scheme = ClassicRooScheme(scheme, subheading, country_code, scheme_code)
            self.rules_json += scheme.rules_json

    def get_rule_sets(self):
        if len(self.schemes) > 0:
            self.rule_sets = self.schemes[0].get_rule_sets()
        else:
            self.rule_sets = []
        return self.rule_sets

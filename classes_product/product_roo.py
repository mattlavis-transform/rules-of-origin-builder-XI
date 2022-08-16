from classes_product.product_roo_rule import ProductRooRule
from classes_product.product_roo_rule_component import ProductRooRuleComponent
import classes.globals as g


class ProductRoo(object):
    def __init__(self, data, subheading, country_code, scheme_code):
        self.data = data
        self.subheading = subheading
        self.country_code = country_code
        self.scheme_code = scheme_code

        try:
            self.rules_json = self.data["rules"]
        except Exception as e:
            self.rules_json = []
        try:
            self.rules_decomposed_json = self.data["rulesDecomposed"]
        except Exception as e:
            self.rules_decomposed_json = []

        self.process_rules()
        self.prepare_for_export()

    def prepare_for_export(self):
        self.export = []
        for rule in self.rules:
            for component in rule.components:
                obj = {
                    "heading": rule.heading,
                    "chapter": rule.chapter,
                    "subdivision": rule.description,
                    "prefix": "",
                    "min": rule.min,
                    "max": rule.max,
                    "rules": [
                        {
                            "rule": component.text,
                            "class": component.type,
                            "operator": None,
                            "specific_processes": False,
                            "double_dash": False
                        }
                    ],
                    "valid": True
                }
                self.export.append(obj)
        a = 1

    def process_rules(self):
        self.rules = []
        self.rule_components = []

        # Get product rules decomposed
        for rule_decomposed in self.rules_decomposed_json:
            heading = rule_decomposed["heading"]
            description = rule_decomposed["description"]
            components = rule_decomposed["components"]
            for component in components:
                text = component["text"]
                idRuleComponent = component["idRuleComponent"]
                type = component["type"]
                product_roo_rule_component = ProductRooRuleComponent(heading, description, text, idRuleComponent, type)
                self.rule_components.append(product_roo_rule_component)

        # Get product rules
        for heading in self.rules_json:
            for rule in self.rules_json[heading]:
                id_rule = rule["idRule"]
                description = rule["description"]
                product_roo_rule = ProductRooRule(heading, id_rule, description, self.subheading)

                # Assign the components to the rules
                for component in self.rule_components:
                    if component.heading == product_roo_rule.heading:
                        if component.description == product_roo_rule.description:
                            product_roo_rule.components.append(component)

                if product_roo_rule.id_rule not in g.rule_ids:
                    self.rules.append(product_roo_rule)

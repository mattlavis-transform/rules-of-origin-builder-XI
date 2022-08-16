import uuid

from classes_product.product_roo_rule import ProductRooRule
from classes_product.product_roo_rule_component import ProductRooRuleComponent
import classes.globals as g


class ProductRoo(object):
    def __init__(self, data, subheading, country_code, scheme_code, has_rules_decomposed):
        self.data = data
        self.subheading = subheading
        self.country_code = country_code
        self.scheme_code = scheme_code
        self.has_rules_decomposed = has_rules_decomposed

        # Get the rules
        try:
            self.rules_json = self.data["rules"]
        except Exception as e:
            self.rules_json = []

        if self.has_rules_decomposed:
            # Get the rules decomposed
            try:
                self.rules_decomposed_json = self.data["rulesDecomposed"]
            except Exception as e:
                self.rules_decomposed_json = []

        self.process_rules()
        self.prepare_for_export()

    def get_heading_array(self, heading):
        # Split based on "ands" and commas
        heading = heading.replace(",", " and ")
        heading = heading.replace("  ", " ")

        # to -> hyphen
        heading = heading.replace("to", "-")

        if "and" in heading:
            headings = heading.split("and")
        else:
            headings = [heading]

        ret = []
        for heading in headings:
            ret.append(heading.strip())

        return ret

    def process_rules(self):
        self.rules = []
        self.rule_components = []

        # Get product rules
        for heading in self.rules_json:
            if "190120" in heading:
                a = 1

            headings = self.get_heading_array(heading)
            index = -1
            for h in headings:
                index += 1
                h = h.strip()
                for rule in self.rules_json[heading]:
                    id_rule = rule["idRule"]
                    if id_rule is None:
                        id_rule = uuid.uuid1()
                    else:
                        id_rule = str(id_rule)

                    # print(h, str(id_rule))
                    if index == 1:
                        id_rule = "A" + str(id_rule)
                    description = rule["description"]
                    product_roo_rule = ProductRooRule(h, id_rule, description, self.subheading)
                    if not self.has_rules_decomposed:
                        product_roo_rule.rule = rule["rule"]
                        product_roo_rule.alternate_rule = rule["alternateRule"]

                    if product_roo_rule.id_rule not in g.rule_ids:
                        self.rules.append(product_roo_rule)
                        g.rule_ids.append(product_roo_rule.id_rule)

        if self.has_rules_decomposed:
            # Get product rules decomposed
            for rule_decomposed in self.rules_decomposed_json:
                heading = rule_decomposed["heading"]
                headings = self.get_heading_array(heading)
                for h in headings:
                    h = h.strip()
                    description = rule_decomposed["description"]
                    components = rule_decomposed["components"]
                    for component in components:
                        text = component["text"]
                        idRuleComponent = component["idRuleComponent"]
                        type = component["type"]
                        product_roo_rule_component = ProductRooRuleComponent(h, description, text, idRuleComponent, type)
                        self.rule_components.append(product_roo_rule_component)

            # Assign the components to the rules
            for rule in self.rules:
                for component in self.rule_components:
                    if component.heading == rule.heading:
                        if component.description == rule.description:
                            rule.components.append(component)
                            break
        else:
            # There are no decomposed rules
            for rule in self.rules:
                description = rule.description
                idRuleComponent = None
                type = ""

                # Get the primary rule
                text = rule.rule if rule.rule else ""
                product_roo_rule_component = ProductRooRuleComponent(heading, description, text, idRuleComponent, type, process_no_component_rules=True)
                rule.components.append(product_roo_rule_component)

                # Get the alternative rule
                alternate_rule = rule.alternate_rule if rule.alternate_rule else ""
                if alternate_rule != "":
                    product_roo_rule_component2 = ProductRooRuleComponent(heading, description, alternate_rule, idRuleComponent, type, process_no_component_rules=True)
                    rule.components.append(product_roo_rule_component2)

                # if alternate_rule is not None:
                #     text += "ORDIVIDER" + alternate_rule

    def prepare_for_export(self):
        self.export = []
        for rule in self.rules:
            for component in rule.components:
                component_types = []
                types = component.type.replace('[', '').replace(']', '')
                my_types = types.split(',')
                for my_type in my_types:
                    my_type = my_type.strip()
                    if my_type != "":
                        component_types.append(my_type.strip())
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
                            "class": component_types,
                            "operator": None,
                            "specific_processes": False,
                            "double_dash": False
                        }
                    ],
                    "valid": True
                }
                self.export.append(obj)

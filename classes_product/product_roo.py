import uuid
import re
import sys

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

    def check_contained(self, heading_in_json_source):
        is_contained = False
        match_items = []
        g.records = []
        original = heading_in_json_source + ""
        heading_in_json_source2 = heading_in_json_source.lower().replace("ex", "").strip()
        heading_in_json_source2 = heading_in_json_source2.lower().replace(".", "").strip()
        heading_in_json_source2 = heading_in_json_source2.lower().replace("–", "to").strip()
        heading_in_json_source2 = heading_in_json_source2.lower().replace("-", "to").strip()
        heading_in_json_source2 = heading_in_json_source2.lower().replace(", and", "and").strip()
        heading_in_json_source2 = heading_in_json_source2.lower().replace(",", "and").strip()

        # First split off the ands (,)
        if "and" in heading_in_json_source2:
            parts = heading_in_json_source2.split("and")
            # Strip any spaces etc.
            for i in range(0, len(parts)):
                parts[i] = parts[i].strip()
        else:
            parts = [heading_in_json_source2]

        # Then split off the ranges (to)
        for part in parts:
            if "to" in part:
                parts2 = part.split("to")
                for i in range(0, len(parts2)):
                    parts2[i] = parts2[i].strip()
                    parts2[i] = parts2[i].replace(" ", "")
                a = 1
                if len(parts2[0]) == len(parts2[1]):
                    for i in range(int(parts2[0]), int(parts2[1]) + 1):
                        tmp = str(i)
                        if len(tmp) == 3:
                            tmp = "0" + tmp
                        elif len(tmp) == 5:
                            tmp = "0" + tmp
                        match_items.append(tmp)
                        a = 1
                else:
                    max_len = 0
                    for part3 in parts2:
                        if len(part3) > max_len:
                            max_len = len(part3)

                    for i in range(0, len(parts2)):
                        parts2[i] = parts2[i].ljust(max_len, "0")

                    for i in range(int(parts2[0]), int(parts2[1]) + 1):
                        match_items.append(str(i))

                    print("Mismatched lengths on parts - quitting", parts2[0], parts2[1])
            else:
                match_items.append(part)

        # Now loop through the match items and check that at least one of
        # them belongs to the current subheading
        for match_item in match_items:
            if "chapter" in match_item:
                match_item = match_item.replace("chapter", "").strip()
                if match_item.isnumeric():
                    match_item = match_item.rjust(2, "0")
                    if self.subheading[0:2] == match_item:
                        is_contained = True
                        break
                else:
                    print("Not a numeric chapter - quitting", original)
                    sys.exit()

            else:
                match_item = match_item.replace(" ", "")
                if match_item.isnumeric():
                    match_item_length = len(match_item)
                    if self.subheading[0:match_item_length] == match_item:
                        is_contained = True
                        break
                else:
                    print("Not a numeric heading - quitting", original)
                    sys.exit()

                a = 1

        return is_contained

    def process_rules(self):
        self.rules = []
        self.rule_components = []
        self.rules_json_overridden = {}
        self.rules_decomposed_json_overridden = []

        # Check for overrides
        for heading in self.rules_json:
            override = False
            for override_item in g.overrides:
                if override_item["country"] == self.country_code:
                    if heading == override_item["from"]:
                        # Has relevant overrides
                        override = True
                        break

            if override:
                for i in range(0, len(self.rules_json[heading])):
                    self.rules_json[heading][i]["description"] = override_item["to"]
                    tmp = self.rules_json[heading]
                    self.rules_json_overridden[override_item["to"]] = tmp
                    break
            else:
                self.rules_json_overridden[heading] = self.rules_json[heading]

        self.rules_json = self.rules_json_overridden

        if self.has_rules_decomposed:
            try:
                for rule in self.rules_decomposed_json:
                    override = False
                    for override_item in g.overrides:
                        if override_item["country"] == self.country_code:
                            if rule["heading"] == override_item["from"]:
                                # Has relevant overrides
                                override = True
                                break

                    if override:
                        rule["heading"] = override_item["to"]
                        rule["description"] = override_item["to"]
                        self.rules_decomposed_json_overridden.append(rule)
                    else:
                        self.rules_decomposed_json_overridden.append(rule)

                self.rules_decomposed_json = self.rules_decomposed_json_overridden
            except Exception as e:
                pass

        # Get product rules
        for heading in self.rules_json:
            is_contained = self.check_contained(heading)
            if is_contained:
                if "160100" in heading:
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

                    for override in g.overrides:
                        if override["country"] == self.country_code:
                            if heading == override["from"]:
                                heading = override["to"]
                                print("Overriding")
                                break

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
            rule.description = rule.description.replace("\t", " ")
            rule.description = re.sub(r'\s+', ' ', rule.description)

            for component in rule.components:
                component_types = []
                types = component.type.replace('[', '').replace(']', '')
                my_types = types.split(',')
                for my_type in my_types:
                    my_type = my_type.strip()
                    if my_type != "":
                        component_types.append(my_type.strip())
                # obj = {
                #     "heading": rule.heading,
                #     "chapter": rule.chapter,
                #     "subdivision": rule.description,
                #     "min": rule.min,
                #     "max": rule.max,
                #     "rules": [
                #         {
                #             "rule": component.text,
                #             "class": component_types,
                #             "operator": None,
                #             "specific_processes": False,
                #             "double_dash": False
                #         }
                #     ],
                #     "valid": True
                # }
                obj = {
                    "heading": rule.heading,
                    "chapter": rule.chapter,
                    "subdivision": rule.description,
                    "min": rule.min,
                    "max": rule.max,
                    "rules": [
                        {
                            "rule": component.text,
                            "class": component_types,
                            "operator": None
                        }
                    ],
                    "valid": True
                }
                self.export.append(obj)

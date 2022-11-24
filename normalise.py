class Winky(object):

    def normalise_chapters(self):
        for chapter in range(1, 98):
            all_ex_codes = True
            if chapter == 9:
                a = 1
            is_chapter_mentioned = False
            rule_set_count = 0
            if chapter != 77:
                for rule_set in self.rule_sets:
                    if rule_set["chapter"] == chapter:
                        rule_set_count += 1
                        if not rule_set["is_ex_code"]:
                            all_ex_codes = False
                        if rule_set["is_chapter"]:
                            is_chapter_mentioned = True

            if not all_ex_codes:  # If it is all ex-codes, then we can just leave it as-is
                if rule_set_count > 1 and is_chapter_mentioned:
                    # Check if there are any ex codes anywhere except for on the chapter itself
                    # If there are not, then we can just replicate rules, ignoring the headings that are exceptions
                    has_ex_code_headings = False
                    for rule_set in self.rule_sets:
                        if rule_set["chapter"] == chapter:
                            if "chapter" not in rule_set["heading"].lower():
                                if "ex" in rule_set["heading"]:
                                    has_ex_code_headings = True
                                    break

                    if not has_ex_code_headings:
                        self.normalise_standard_chapter(chapter)
                    else:
                        self.normalise_complex_chapter(chapter)

    def normalise_complex_chapter(self, chapter):
        # print(chapter)
        # Get all the other rules in that chapter that are not the chapter heading
        if chapter == 9:
            a = 1
        matches = {}
        contains_subheading = False
        index = 0
        chapter_index = None
        for rule_set in self.rule_sets:
            if rule_set["chapter"] == chapter:
                if rule_set["is_chapter"]:
                    chapter_index = index

                if rule_set["is_subheading"]:
                    contains_subheading = True

                matches[index] = rule_set
            index += 1

        # Loop through all of the headings in chapter (according to the DB)
        # If the heading is missing:
        #   add in the heading as a copy of the chapter rule_set

        chapter_string = str(chapter).rjust(2, "0")
        if contains_subheading is False:
            for heading in g.all_headings:
                if heading == "0903":
                    a = 1
                if heading[0:2] == chapter_string:
                    heading_exists_in_rule_set = False
                    for match in matches:
                        if heading in matches[match]["headings"]:
                            heading_exists_in_rule_set = True
                            if matches[match]["is_ex_code"]:
                                process_ex_code = True
                            else:
                                process_ex_code = False
                            break

                    if not heading_exists_in_rule_set:
                        # In expanding out the definition of a chapter to its subheadings, we will need
                        # to copy the rules from the chapter down to the headings that did not previously
                        # exist. In such cases, we need to create those headings and add them to the rule set.
                        obj = {
                            "heading": heading,
                            "headings": [heading],
                            "subheadings": [],
                            "chapter": chapter,
                            "subdivision": matches[chapter_index]["subdivision"],
                            "min": g.format_parts(heading, 0),
                            "max": g.format_parts(heading, 1),
                            "rules": matches[chapter_index]["rules"],
                            "is_ex_code": False,
                            "is_chapter": False,
                            "is_heading": True,
                            "is_subheading": False,
                            "is_range": False,
                            "valid": True
                        }
                        self.rule_sets.append(obj)
                    else:
                        if process_ex_code:
                            # This takes the definition of the chapter, reduced to 'Any other product'
                            # and assigns it to the matched heading as a counterpoint to the existing
                            # ex code, to cover all commodities that are not catered for within the
                            # specific ex code.
                            obj = {
                                "heading": matches[match]["heading"],
                                "headings": [],
                                "subheadings": [],
                                "chapter": chapter,
                                "subdivision": "Any other product",
                                "min": matches[match]["min"],
                                "max": matches[match]["max"],
                                "rules": matches[chapter_index]["rules"],
                                "is_ex_code": True,
                                "is_chapter": False,
                                "is_heading": True,
                                "is_subheading": False,
                                "is_range": False,
                                "valid": True
                            }
                            self.rule_sets.append(obj)

                if heading[0:2] > chapter_string:
                    break

            # Finally, remove the old chapter code, as its value has been copied elsewhere now
            self.rule_sets.pop(chapter_index)
        else:
            # Firstly check for any headings under the chapter that have rules that are based on subheadings and not headings
            this_chapter_headings = []
            headings_with_subheading_rules = []
            headings_without_subheading_rules = []

            for heading in g.all_headings:
                heading_contains_matches = False
                if heading[0:2] == chapter_string:
                    subheadings = []
                    contains_subheadings = False
                    matched = False
                    for match in matches:
                        if heading in matches[match]["headings"]:
                            if matches[match]["is_subheading"]:
                                contains_subheadings = True
                                subheadings.append(matches[match])
                            matched = True

                    if matched:
                        status = "matched"
                    else:
                        status = "unmatched"
                        contains_subheadings = False

                    obj = {heading: {
                        "status": status,
                        "contains_subheadings": contains_subheadings,
                        "subheadings": subheadings
                    }}
                    this_chapter_headings.append(obj)
                    if contains_subheadings:
                        headings_with_subheading_rules.append(heading)
                    else:
                        headings_without_subheading_rules.append(heading + "00")

            affected_subheadings = []
            for subheading in g.all_subheadings:
                if subheading[0:4] in headings_with_subheading_rules:
                    affected_subheadings.append(subheading)

            full_list = headings_without_subheading_rules + affected_subheadings
            full_list.sort()
            additional_rulesets = []
            for subheading in full_list:
                for match in matches:
                    if matches[match]["min"] <= str(subheading) + "0000" and matches[match]["max"] >= str(subheading) + "0000":
                        new_min = subheading + "0000"
                        if g.right(subheading, 2) == "00":
                            new_max = subheading[0:4] + "999999"
                        elif g.right(subheading, 1) == "0":
                            new_max = subheading[0:5] + "99999"
                        else:
                            new_max = subheading + "9999"
                        new_ruleset = self.copy_ruleset(matches[match], new_min, new_max)
                        additional_rulesets.append(new_ruleset)
                        a = 1

            # Remove any rulesets for the selected chapter, as these will all be replaced by the newly formed equivalents
            ruleset_count = len(self.rule_sets)
            for i in range(ruleset_count - 1, -1, -1):
                rule_set = self.rule_sets[i]
                if rule_set["chapter"] == chapter:
                    self.rule_sets.pop(i)

            # Then add the new rule sets onto the list
            self.rule_sets += additional_rulesets

    def normalise_standard_chapter(self, chapter):
        # First, get the chapter's own rule-set
        chapter_found = False
        string_to_find = "chapter " + str(chapter)
        index = -1
        for rule_set in self.rule_sets:
            index += 1
            heading_string = rule_set["heading"].lower()
            heading_string = heading_string.replace("ex", "")
            heading_string = heading_string.replace("  ", " ")
            heading_string = heading_string.strip()
            if string_to_find == heading_string:
                chapter_found = True
                rule_set_rubric = RuleSetLegacy()
                rule_set_rubric.rules = rule_set["rules"]
                break

        # Then, get all headings that do not have rulesets
        # and assign the rulesets to them
        chapter_string = str(chapter).rjust(2, "0")
        for heading in g.all_headings:
            if heading[0:2] == chapter_string:
                matched = False
                for rule_set in self.rule_sets:
                    if rule_set["heading"] == heading:
                        matched = True
                        break
                if not matched:
                    obj = {
                        "heading": heading,
                        "description": g.all_headings[heading],
                        "subdivision": "",
                        "is_ex_code": False,
                        "min": heading + "000000",
                        "max": heading + "999999",
                        "rules": rule_set["rules"],
                        "valid": True,
                        "chapter": chapter
                    }
                    self.rule_sets.append(obj)

            if heading[0:2] > chapter_string:
                break

        if chapter_found:
            self.rule_sets.pop(index)
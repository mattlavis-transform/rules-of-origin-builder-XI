import re

rule_ids = []
heading_carry_over = ""

def process_description(s):
    s = re.sub(r"\n", " ", s)
    s = re.sub(r" +", " ", s)
    s = s.replace(" %", "%")
    s = s.replace(" \u00b0", "&nbsp;\u00b0")
    s = s.replace("except\nfor:", "except for")
    s = s.replace("except for:", "")
    s = s.replace("except for", "")
    s = s.replace("- - ", "- ")
    s = s.replace("g/m2", "g/m2 ")
    s = s.replace("  ", " ")
    s = s.strip()
    s = s.rstrip(";")
    s = s.rstrip(",")
    s = s.strip()
    s = s[0].upper() + s[1:]
    return s

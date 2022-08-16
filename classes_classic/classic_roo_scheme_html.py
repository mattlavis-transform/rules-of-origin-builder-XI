import os
import re


class ClassicRooSchemeHtml(object):
    def __init__(self, subheading, rules, country_code, scheme_code):
        self.subheading = subheading
        self.rules = rules
        self.country_code = country_code
        self.country_code = country_code
        self.scheme_code = scheme_code
        self.format_rules_for_export()
        self.save_rules_to_html()

    def format_rules_for_export(self):
        self.setup_styles()
        self.rules = re.sub(r'<body>', self.styles + "<body>", self.rules)

    def save_rules_to_html(self):
        folder = os.getcwd()
        folder = os.path.join(folder, "resources")
        folder = os.path.join(folder, "json_html")
        folder = os.path.join(folder, self.country_code)
        if not os.path.isdir(folder):
            os.mkdir(folder)
        file = os.path.join(folder, self.subheading + ".html")
        f = open(file, "w+")
        f.write(self.rules)
        f.close()

    def setup_styles(self):
        self.styles = """
        <head>
        <style type='text/css'>
        body { font-family: calibri, arial;}
        table { border:1px solid black;}
        td { border:1px solid black; }
        th { background-color:black; color: white}
        </style>
        </head>
        """


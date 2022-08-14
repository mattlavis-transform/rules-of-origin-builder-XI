import os
from re import sub
import sys
from datetime import datetime
from classes.database import Database
from classes.classification import Classification
from classes.eu_roo import EuRoo
from classes.classic_roo import ClassicRoo
import requests
import csv
from bs4 import BeautifulSoup
import filecmp
import collections
import shutil
import json
from urllib.request import urlopen
from dotenv import load_dotenv
import logging


class Rule(object):
    def __init__(self, row=None):
        if row is None:
            self.subheading = None
            self.heading = None
            self.description = None
            self.rule = None
            self.alternate_rule = None
            self.quota_amount = None
            self.quota_unit = None
            self.key_first = None
            self.key_last = None
        else:
            self.subheading = row[0]
            self.heading = row[1]
            self.description = row[2]
            self.rule = row[3]
            self.alternate_rule = row[4]
            self.quota_amount = row[5]
            self.quota_unit = row[6]
            self.key_first = row[7]
            self.key_last = row[8]

    def equates_to(self, rule):
        equal = True
        if self.subheading != rule.subheading:
            equal = False
        elif self.heading != rule.heading:
            equal = False
        elif self.description != rule.description:
            equal = False
        elif self.description != rule.description:
            equal = False
        elif self.rule != rule.rule:
            equal = False
        elif self.alternate_rule != rule.alternate_rule:
            equal = False
        elif self.key_first != rule.key_first:
            equal = False
        elif self.key_last != rule.key_last:
            equal = False

        return equal

    def asdict(self):
        return {
            'subheading': self.subheading,
            'heading': self.heading,
            'description': self.description,
            'rule': self.rule,
            'alternate_rule': self.alternate_rule,
            'quota_amount': self.quota_amount,
            'quota_unit': self.quota_unit,
            'key_first': self.key_first,
            'key_last': self.key_last
        }

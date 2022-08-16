from datetime import datetime
import os


class Classification(object):
    def __init__(self, goods_nomenclature_sid, goods_nomenclature_item_id, productline_suffix, number_indents, leaf):
        self.goods_nomenclature_sid = goods_nomenclature_sid
        self.goods_nomenclature_item_id = goods_nomenclature_item_id
        self.productline_suffix = productline_suffix
        self.number_indents = int(number_indents)
        self.leaf = int(leaf)

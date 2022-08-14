from markdownify import markdownify as md


class ClassicRooCell(object):
    def __init__(self, table_cell=None, index=0):
        if table_cell is not None:
            self.table_cell = table_cell
            self.rowspan = int(self.table_cell.get("rowspan") or 1)
            self.colspan = int(self.table_cell.get("colspan") or 1)
            self.format_cell_content(index)
            del self.table_cell

    def format_cell_content(self, index):
        self.text = md((self.table_cell.text or "").strip())
        self.text = self.text.replace('\xa0', '')
        if index == 0:
            self.text = self.text.replace(';', ',')

    def set_text(self, text):
        self.rowspan = 1
        self.colspan = 1
        self.text = text

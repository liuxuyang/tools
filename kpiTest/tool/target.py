from openpyxl import *

from config import Config
from util import check_file_exist, log


class Excel:
    DEFAULT_SAVE_PATH = "sample.xlsx"
    DEFAULT_SHEET_NAME = "sheet"

    def __init__(self):
        self.wb = None
        self.ws = None
        self.save_path = None

    def open(self, path=DEFAULT_SAVE_PATH):
        if path and check_file_exist(path):
            self.wb = load_workbook(path)
            self.save_path = path
        else:
            self.wb = Workbook()
            self.save_path = Excel.DEFAULT_SAVE_PATH

    def close(self):
        self.wb.close()

    def write_data(self, **kwargs):
        device = kwargs["device"] if "data" in kwargs.keys() else None
        data = kwargs["data"] if "data" in kwargs.keys() else None
        title = kwargs["title"] if kwargs["title"] is not None else Excel.DEFAULT_SHEET_NAME
        if data is None or not isinstance(data, dict):
            return
        self.ws = self.wb.create_sheet(title, 0)  # create sheet

        if device:
            self.ws.cell(row=1, column=1, value="system version:")  # write system version
            self.ws.cell(row=1, column=2, value=device.system_version)
            self.ws.cell(row=2, column=1, value="app version:")  # write app version
            self.ws.cell(row=2, column=2, value=device.app_version)

        # write app
        app_data = data["app"]
        app_start_row = 3 if device else 1
        app_start_column = 1
        self.ws.cell(row=app_start_row, column=app_start_column, value="app")
        self.__write_item(app_data, "app_log", app_start_row + 1, app_start_column)  # write app data

        # write hal
        hal_data = data["hal"]
        hal_start_row = 3 if device else 1
        hal_start_column = 1 + len(app_data.keys())
        self.ws.cell(row=app_start_row, column=hal_start_column, value="hal")
        self.__write_item(hal_data, "hal_log", hal_start_row + 1, hal_start_column)  # write hal data

        print("output in %s" % os.path.abspath(self.save_path))
        self.wb.save(self.save_path)

    def __write_item(self, data, data_type, start_row, start_column):
        for i in xrange(len(data.keys())):
            title = Config.get_title(data_type, data.keys()[i])
            self.ws.cell(row=start_row, column=start_column + i, value=title)  # write header
            key = data.keys()[i]
            column_data = data.get(key)
            for j in xrange(len(column_data)):
                row = start_row + 1 + j
                column = start_column + i
                value = column_data[j]
                self.ws.cell(row=row, column=column, value=value)  # write data

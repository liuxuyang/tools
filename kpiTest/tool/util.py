import time
import os

from config import Config


def log(msg):
    if Config.is_debug():
        print(msg)


def date_to_time(date):
    """
    01-30 11:12:50.106
    :param date:
    :return:
    """
    timeArray = time.strptime("2017-" + date, "%Y-%m-%d %H:%M:%S")
    timeStamp = int(time.mktime(timeArray))
    return timeStamp

def check_file_exist(path):
    return os.path.exists(path)

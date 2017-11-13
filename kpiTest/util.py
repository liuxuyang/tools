import time
import os

from config import Config

PLATFORM_QCOM = "qcom"
PLATFORM_MTK = "mtk"


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


def detect_platform():
    return PLATFORM_QCOM


def detect_hal_pid():
    return 22177


def detect_app_pid():
    return 11511


def check_file_exist(path):
    return os.path.exists(path)

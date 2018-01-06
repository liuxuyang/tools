import time
import os

from config import Config

LOG_TYPE_APP = 0
LOG_TYPE_HAL = 1


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


def check_duration(duration):
    if duration.isdigit():
        return int(duration)
    else:
        return "NAN"


def check_file_exist(path):
    return os.path.exists(path)


def generate_log_path(log_type):
    cur_time = time.strftime('%Y_%m_%d_%H_%M_%S', time.localtime(time.time()))
    home_path = os.environ['HOME']
    log_path = "Kpi/log"
    if log_type == LOG_TYPE_APP:
        log_name = "app_log_%s.log" % cur_time
    elif log_type == LOG_TYPE_HAL:
        log_name = "hal_log_%s.log" % cur_time
    else:
        log_name = "temp.log"
    full_path = os.path.join(home_path, log_path)
    if not os.path.exists(full_path):
        os.makedirs(full_path)
    return os.path.join(full_path, log_name)


def generate_result_file_path(filename):
    if filename.find(".xlsx") == -1:
        filename = filename + ".xlsx"
    cur_date = time.strftime('%Y_%m_%d', time.localtime(time.time()))
    home_path = os.environ['HOME']
    log_path = "Kpi/result/%s" % cur_date
    full_path = os.path.join(home_path, log_path)
    if not os.path.exists(full_path):
        os.makedirs(full_path)
    return os.path.join(full_path, filename)

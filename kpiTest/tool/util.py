import time
import os

import sys

from datetime import datetime

from config import Config

LOG_TYPE_ALL = 0
LOG_TYPE_APP = 1
LOG_TYPE_HAL = 2


def log(msg):
    if Config.is_debug() and msg is not None:
        if not isinstance(msg, str):
            msg = str(msg)
        msg_array = msg.split(os.linesep)
        for msg_line in msg_array:
            if msg_line:
                print "%s : %s" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), msg_line)


def date_to_time(date):
    """
    01-30 11:12:50.106
    :param date:
    :return:
    """
    time_array = time.strptime("2017-" + date, "%Y-%m-%d %H:%M:%S")
    time_stamp = int(time.mktime(time_array))
    return time_stamp


def check_int(arg):
    if isinstance(arg, str) and arg.isdigit():
        return int(arg)
    elif isinstance(arg, int):
        return arg
    else:
        return None


def print_progress(index, count, format_str):
    percent = int(float(index) / count * 100)
    sys.stdout.write(("\r" + format_str) % percent)
    sys.stdout.flush()


def check_duration(duration):
    if isinstance(duration, str) and duration.isdigit():
        return int(duration)
    elif isinstance(duration, int) or isinstance(duration, float) or isinstance(duration, long):
        return duration
    else:
        return "NAN"


def check_file_exist(path):
    return os.path.exists(path)


def generate_log_path(log_type):
    cur_time = time.strftime('%Y_%m_%d_%H_%M_%S', time.localtime(time.time()))
    home_path = os.environ['HOME']
    log_path = "Kpi/log"
    if log_type == LOG_TYPE_ALL:
        log_name = "kpi_log_%s.log" % cur_time
    elif log_type == LOG_TYPE_APP:
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

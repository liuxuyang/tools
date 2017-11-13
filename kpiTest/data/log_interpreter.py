from config import Config
from util import *
from data.app_log import AppLogBean
from data.mtk_log import MtkHalLogBean
from data.qcom_log import QcomHalLogBean


class LogInterpreter:
    """

    """

    def __init__(self):
        self.__platform = detect_platform()
        self.__hal_pid = detect_hal_pid()
        self.__app_pid = detect_app_pid()
        self.__app_log = []
        self.__hal_log = []
        self.__result_data = {}

    def __str__(self):
        return "*********************************\n" \
               + "app log : " + str(len(self.__app_log)) + "\n" \
               + "*********************************\n" \
               + "hal log : " + str(len(self.__hal_log)) + "\n"

    def read_log(self, log_path):
        # print("read log path : " + log_path)
        with open(log_path, 'r') as f:
            for line in f:
                if str(self.get_app_pid()) in line:
                    self.__app_log.append(AppLogBean(line))
                elif str(self.get_hal_pid()) in line:
                    if self.get_platform() == PLATFORM_QCOM:
                        hal_log = QcomHalLogBean(line)
                        if hal_log.is_valid():
                            self.__hal_log.append(hal_log)
                    elif self.get_platform() == PLATFORM_MTK:
                        self.__hal_log.append(MtkHalLogBean(line))
        f.close()

    def get_platform(self):
        return self.__platform

    def get_hal_pid(self):
        return self.__hal_pid

    def get_app_pid(self):
        return self.__app_pid

    def get_result(self):

        return self.__result_data

    def analysis_hal_log(self):
        if self.is_qcom_platform():
            self.__analysis_qcom_hal_log()
        elif self.is_mtk_platform():
            self.__analysis_mtk_hal_log()

    def analysis_app_log(self):
        log("not support analysis APP data")

    def __analysis_mtk_hal_log(self):
        log("not support analysis mtk platform HAL data")

    def __analysis_qcom_hal_log(self):
        """
        TAG : [KPI Perf]
        :return:
        """
        for log in self.__hal_log:
            if log.is_method_start():
                end_log = self.__find_end_bean(log)
                # print("start : " + log.__str__())
                # print("end : " + end_log.__str__())
                if end_log is not None:
                    # print("start %s : end %s %s : %s " % (log.time, end_log.time, log.get_type(), end_log.get_type()))
                    self.__add_to_result(log, end_log)

    def __find_end_bean(self, start_bean):
        end_tag = Config.find_end_tag(start_tag=start_bean.get_type())
        #print(end_tag)
        search_start = self.__hal_log.index(start_bean) + 1
        offset = self.__get_index(self.__hal_log[search_start:], start_bean.get_type())
        if offset is None or offset == 0:
            logs = self.__hal_log[search_start:]
        else:
            logs = self.__hal_log[search_start:search_start + offset]
        for bean in logs:
            if bean.is_method_end() and end_tag == bean.get_type():
                return bean
        log("loss end!!!")
        return None

    def __add_to_result(self, start, end):
        if start is None or end is None:
            return
        duration = end - start
        if start.get_type() in self.__result_data:
            self.__result_data[start.get_type()].append(duration)
        else:
            self.__result_data[start.get_type()] = list([duration])

    def __get_index(self, log_list, tag):
        for i in xrange(len(log_list)):
            if log_list[i].get_type() == tag:
                return i

    def is_qcom_platform(self):
        return self.get_platform() == PLATFORM_QCOM

    def is_mtk_platform(self):
        return self.get_platform() == PLATFORM_MTK

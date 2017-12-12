from tool.devices import PLATFORM_MTK
from tool.devices import PLATFORM_QCOM
from tool.util import *
from data.app_log import AppLogBean
from data.mtk_log import MtkHalLogBean
from data.qcom_log import QcomHalLogBean


class LogInterpreter:
    """

    """

    # def __init__(self, platform, app_pid, hal_pid):
    #     self.__platform = platform
    #     self.__hal_pid = app_pid
    #     self.__app_pid = hal_pid
    #     self.__app_log = []
    #     self.__hal_log = []
    #     self.__result_data = {"hal": {}, "app": {}}

    def __init__(self, device):
        self.__platform = device.platform
        self.__hal_pid = device.hal_pid
        self.__app_pid = device.app_pid
        self.__app_log = []
        self.__hal_log = []
        self.__result_data = {"hal": {}, "app": {}}

    def __str__(self):
        return "*********************************\n" \
               + "app log : " + str(len(self.__app_log)) + "\n" \
               + "*********************************\n" \
               + "hal log : " + str(len(self.__hal_log)) + "\n"

    def read_log(self, log_path):
        # print("read log path : " + log_path)
        log("start read log %s" % time.time())
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
        log("end read log %s" % time.time())

    def get_platform(self):
        return str(self.__platform)

    def get_hal_pid(self):
        return int(self.__hal_pid)

    def get_app_pid(self):
        return int(self.__app_pid)

    def get_result(self):
        return self.__result_data

    def analysis_hal_log(self):
        if self.is_qcom_platform():
            self.__analysis_qcom_hal_log()
        elif self.is_mtk_platform():
            self.__analysis_mtk_hal_log()

    def analysis_app_log(self):
        log("start analysis app log , log len : %s" % len(self.__app_log))
        for app_log in self.__app_log:
            if app_log.is_valid(self.get_app_pid()):
                if app_log.has_mode_info():
                    self.__add__app_to_result_with_mode(app_log.get_type(), app_log.get_mode_type(),
                                                        app_log.get_duration())
                else:
                    self.__add_app_to_result(app_log.get_type(), app_log.get_duration())
        log("end analysis app log , result data len : %s" % len(self.__result_data["app"]))

    def __analysis_mtk_hal_log(self):
        log("not support analysis mtk platform HAL data")

    def __analysis_qcom_hal_log(self):
        """
        TAG : [KPI Perf]
        :return:
        """
        log("start analysis qcom hal log , log len : %s" % len(self.__hal_log))
        for hal_log in self.__hal_log:
            if hal_log.is_method_start():
                end_log = self.__find_end_bean(hal_log)
                # print("start : " + log.__str__())
                # print("end : " + end_log.__str__())
                if end_log is not None:
                    # print("start %s : end %s %s : %s " % (log.time, end_log.time, log.get_type(), end_log.get_type()))
                    self.__add_hal_to_result(hal_log, end_log)
        log("end analysis qcom hal log , result data len : %s" % len(self.__result_data["hal"]))

    def __find_end_bean(self, start_bean):
        end_tag = Config.find_end_tag(start_tag=start_bean.get_type())
        # print(end_tag)
        search_start = self.__hal_log.index(start_bean) + 1
        offset = self.__get_index(self.__hal_log[search_start:], start_bean.get_type())
        if offset is None or offset == 0:
            logs = self.__hal_log[search_start:]
        else:
            logs = self.__hal_log[search_start:search_start + offset]
        for bean in logs:
            if bean.is_method_end() and end_tag == bean.get_type():
                return bean
        log("%s loss end tag!!!" % start_bean.get_type())
        return None

    def __add_hal_to_result(self, start, end):
        if start is None or end is None:
            return
        duration = end - start
        if start.get_type() in self.__result_data["hal"]:
            self.__result_data["hal"][start.get_type()].append(duration)
        else:
            self.__result_data["hal"][start.get_type()] = list([duration])

    def __add_app_to_result(self, msg_type, duration):
        if msg_type in self.__result_data["app"]:
            self.__result_data["app"][msg_type].append(duration)
        else:
            self.__result_data["app"][msg_type] = list([duration])

    def __add__app_to_result_with_mode(self, msg_type, mode, duration):
        if msg_type in self.__result_data["app"]:
            if mode in self.__result_data["app"][msg_type].keys():
                self.__result_data["app"][msg_type][mode].append(duration)
                log("add to result with mode : %s and duration : %s" % (mode,duration))
            else:
                self.__result_data["app"][msg_type][mode] = list([duration])
        else:
            self.__result_data["app"][msg_type] = dict()

    def __get_index(self, log_list, tag):
        for i in xrange(len(log_list)):
            if log_list[i].get_type() == tag:
                return i

    def is_qcom_platform(self):
        return self.get_platform() == PLATFORM_QCOM

    def is_mtk_platform(self):
        return self.get_platform() == PLATFORM_MTK

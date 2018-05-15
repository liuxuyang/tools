import json

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
        self.__fwd_pid = device.fwk_pid
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
                elif self.get_fwk_pid() is None:
                    if str(self.get_hal_pid()) in line:
                        if self.get_platform() == PLATFORM_QCOM:
                            hal_log = QcomHalLogBean(line)
                            if hal_log.is_valid():
                                self.__hal_log.append(hal_log)
                        elif self.get_platform() == PLATFORM_MTK:
                            self.__hal_log.append(MtkHalLogBean(line))
                elif str(self.get_hal_pid()) in line or str(self.get_fwk_pid()) in line:
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

    def get_fwk_pid(self):
        if self.__fwd_pid is None:
            return None
        return int(self.__fwd_pid)

    def get_app_pid(self):
        return int(self.__app_pid)

    def get_result(self):
        return self.__result_data

    def analysis_hal_log(self):
        if self.is_qcom_platform():
            # self.__analysis_qcom_hal_log()
            self.__analysis_qcom_hal_log_new()
        elif self.is_mtk_platform():
            self.__analysis_mtk_hal_log()

    def analysis_app_log(self):
        log("start analysis app log , log len : %s" % len(self.__app_log))
        for app_log in self.__app_log:
            if app_log.is_valid(self.get_app_pid()):
                if app_log.has_mode_info():
                    self.__add_result_with_mode("app", app_log.get_type(), app_log.get_mode_type(),
                                                app_log.get_duration())
                else:
                    self.__add_app_to_result(app_log.get_type(), app_log.get_duration())
        log("end analysis app log , result data len : %s" % len(self.__result_data["app"]))

    def __analysis_mtk_hal_log(self):
        log("not support analysis mtk platform HAL data")

    def __analysis_qcom_hal_log_new(self):
        log("start new analysis qcom hal log , log : %s" % len(self.__hal_log))
        index = 0
        while index < len(self.__hal_log):
            index += self.__match_log(self.__hal_log[index])
        log("end new analysis qcom hal log , result data len : %s" % len(self.__result_data["hal"]))

    def __match_log(self, target):
        if target.is_kpi_log() and target.get_msg_data().is_method_start():
            tag = target.get_msg_data().get_type()
            end_tag = Config.find_end_tag(tag)
            search_start = self.__hal_log.index(target) + 1
            offset = self.__get_index(self.__hal_log[search_start:], tag)

            if offset is None or offset == 0:
                offset = 1
                logs = self.__hal_log[search_start:]
            else:
                logs = self.__hal_log[search_start:search_start + offset]

            mode, mode_method, algo_logs = None, None, []
            for bean in logs:
                if bean.is_mode_log():
                    mode_method = bean.get_msg_data().get_method()
                    if is_mode_method_valid(tag, mode_method):
                        mode = bean.get_msg_data().get_mode()
                elif bean.is_kpi_log():
                    if bean.get_msg_data().is_method_end() and end_tag == bean.get_msg_data().get_type():
                        option_duration = bean - target
                        algo_data = {}
                        if len(algo_logs) > 0 and len(algo_logs) % 2 ==0:
                            for i in xrange(len(algo_logs)):
                                if algo_logs[i].get_msg_data().is_start():
                                    algo_data[algo_logs[i].get_msg_data().get_algo_method()] = algo_logs[i + 1] - algo_logs[i]
                        self.__add_result_with_mode("hal", tag, mode, {option_duration: algo_data})
                        return self.__hal_log.index(bean) - self.__hal_log.index(target) + 1
                elif bean.is_algo_log():
                    if len(algo_logs) == 0:
                        algo_logs.append(bean)
                    elif algo_logs[0].get_msg_data().get_algo_type() == bean.get_msg_data().get_algo_type():
                        if len(algo_logs) % 2 == 0 and bean.get_msg_data().is_start():
                            algo_logs.append(bean)
                        elif len(algo_logs) % 2 == 1 and not bean.get_msg_data().is_start():
                            algo_logs.append(bean)
            return offset
        else:
            return 1


    def __analysis_qcom_hal_log(self):
        """
        TAG : [KPI Perf]
        :return:
        """
        log("start analysis qcom hal log , log len : %s" % len(self.__hal_log))
        for hal_log in self.__hal_log:
            if hal_log.is_kpi_log() and hal_log.get_msg_data().is_method_start():
                end_log, mode = self.__find_end_bean(hal_log)
                if end_log is not None:
                    msg_type = hal_log.get_msg_data().get_type()
                    duration = end_log - hal_log
                    self.__add_result_with_mode("hal", msg_type, mode, duration)
        log("end analysis qcom hal log , result data len : %s" % len(self.__result_data["hal"]))

    def __find_end_bean(self, start_bean):
        tag = start_bean.get_msg_data().get_type()

        end_tag = Config.find_end_tag(tag)
        search_start = self.__hal_log.index(start_bean) + 1
        offset = self.__get_index(self.__hal_log[search_start:], tag)
        if offset is None or offset == 0:
            logs = self.__hal_log[search_start:]
        else:
            logs = self.__hal_log[search_start:search_start + offset]

        end_bean, mode, mode_method = None, None, None
        for bean in logs:
            if bean.is_mode_log():
                mode_method = bean.get_msg_data().get_method()
                if is_mode_method_valid(tag, mode_method):
                    mode = bean.get_msg_data().get_mode()
            elif bean.is_kpi_log():
                if bean.get_msg_data().is_method_end() and end_tag == bean.get_msg_data().get_type():
                    end_bean = bean
                else:
                    pass
            # log("%s loss end tag!!!" % tag)
        return end_bean, mode

    def __add_result_with_mode(self, log_type, msg_type, mode, duration):
        if log_type not in ["app", "hal"]:
            return
        if msg_type in self.__result_data[log_type]:
            if mode in self.__result_data[log_type][msg_type].keys():
                self.__result_data[log_type][msg_type][mode].append(duration)
                log("add to result with mode : %s and duration : %s" % (mode, duration))
            else:
                self.__result_data[log_type][msg_type][mode] = list([duration])
                log("add to result with mode : %s and duration : %s" % (mode, duration))

        else:
            self.__result_data[log_type][msg_type] = dict()
            self.__add_result_with_mode(log_type, msg_type, mode, duration)

    def __add_app_to_result(self, msg_type, duration):
        if msg_type in self.__result_data["app"]:
            self.__result_data["app"][msg_type].append(duration)
        else:
            self.__result_data["app"][msg_type] = list([duration])

    def __get_index(self, log_list, tag):
        for i in xrange(len(log_list)):
            if log_list[i].is_kpi_log() and log_list[i].get_msg_data().get_type() == tag:
                return i

    def is_qcom_platform(self):
        return self.get_platform() == PLATFORM_QCOM

    def is_mtk_platform(self):
        return self.get_platform() == PLATFORM_MTK


mode_dict = {}


def is_mode_method_valid(tag, method):
    if tag not in mode_dict.keys():
        mode_dict[tag] = Config.get_mode_method(tag)
    return mode_dict[tag] is not None and method == mode_dict[tag]

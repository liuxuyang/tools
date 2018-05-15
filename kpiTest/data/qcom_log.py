import re

from tool.config import Config
from data.base_log import BaseLogBean

METHOD_FLAG_ENTER = "E"  # E
METHOD_FLAG_EXIT = "X"  # X
METHOD_FLAG_INVALID = None


class QcomHalLogBean(BaseLogBean):
    """
    Qcom HAL log data class.

    create from a stand android hal log format string,like :

    DATE TIME PID TID LEVEL TAG: '<JPEG><INFO>' METHOD: LINE: '[KPI Perf]': FLAG TYPE *

    normal:
    01-23 14:17:40.031   554  2145 I QCamera : <JPEG><INFO> int qcamera::QCamera2HardwareInterface::openCamera(struct hw_device_t **): 1934: [KPI Perf]: E PROFILE_OPEN_CAMERA camera id 0

    with mode:
    01-01 15:32:57.044   501   501 E QCamera2HWI: take_picture:KEY_POST_PROCESS_MODE:hdr
    """

    def __init__(self, line):
        BaseLogBean.__init__(self, line)
        if self.msg:
            if self.is_kpi_log():
                self.__msg_data = QcomMsgData(self.msg)
            elif self.is_mode_log():
                self.__msg_data = QcomModeData(self.msg)
            elif self.is_algo_log():
                self.__msg_data = QcomAlgoData(self.msg)
            else:
                self.__msg_data = None
        else:
            self.__msg_data = None

    def __str__(self):
        return BaseLogBean.__str__(self) + "QCOM HAL :\n" \
               + self.__msg_data.__str__()

    def get_msg_data(self):
        return self.__msg_data

    def is_valid(self):
        return self.is_mode_log() or self.is_kpi_log() or self.is_algo_log()

    def is_kpi_log(self):
        return self.msg is not None and QcomMsgData.KEY_WORD in self.msg

    def is_mode_log(self):
        return self.msg is not None and QcomModeData.KEY_WORD in self.msg

    def is_algo_log(self):
        return self.msg is not None and QcomAlgoData.KEY_WORD in self.msg


class QcomMsgData:
    KEY_WORD = "[KPI Perf]"

    method_pattern = re.compile(r"\sqcamera::.+\)")
    flag_pattern = re.compile(r"\s[E|X]\s")
    type_pattern = re.compile(r"\sPROFILE_\w+")

    def __init__(self, msg):
        """

        :param msg:
        """
        self.__method_name = None
        self.__method_flag = None
        self.__kpi_type = None
        self.__match_log(msg)

    def __match_log(self, msg):
        method_match = QcomMsgData.method_pattern.search(msg)
        if method_match:
            self.__method_name = method_match.group().strip()

        flag_match = QcomMsgData.flag_pattern.search(msg)
        if flag_match:
            self.__method_flag = flag_match.group().strip()

        type_match = QcomMsgData.type_pattern.search(msg)
        if type_match:
            self.__kpi_type = type_match.group().strip()

    def get_method_name(self):
        return self.__method_name

    def get_flag(self):
        return self.__method_flag

    def get_type(self):
        return self.__kpi_type

    def is_method_start(self):
        return self.get_flag() == METHOD_FLAG_ENTER and self.get_type() is not None and Config.is_start_tag(
            self.get_type())

    def is_method_end(self):
        return Config.is_end_tag(self.get_type()) and (self.get_flag() is None or self.get_flag() == METHOD_FLAG_EXIT)

    def __str__(self):
        return "\n method : %s\n flag : %s\n type : %s\n" % (self.get_method_name(), self.get_flag(), self.get_type())


class QcomModeData:
    KEY_WORD = "KEY_POST_PROCESS_MODE"

    def __init__(self, msg):
        s = str(msg).split(":")
        if len(s) < 3 and s[-2] != QcomModeData.KEY_WORD:
            return
        self.__method = s[-3]
        self.__mode = s[-1]

    def get_mode(self):
        return self.__mode

    def get_method(self):
        return self.__method


class QcomAlgoData:
    KEY_WORD = "[KPI PERF]"
    START_FLAG = "THIRD_PARTY_ALGO_START"
    END_FLAG = "THIRD_PARTY_ALGO_STOP"

    def __init__(self, msg):
        if QcomAlgoData.KEY_WORD in msg and (QcomAlgoData.START_FLAG in msg or QcomAlgoData.END_FLAG in msg):
            items = str(msg).split(" ")
            self.__algo_type = items[-1].split(":")[1]
            self.__algo_method = items[-1].split(":")[0]
            self.__is_start = QcomAlgoData.START_FLAG in msg

    def get_algo_type(self):
        return self.__algo_type

    def get_algo_method(self):
        return self.__algo_method

    def is_start(self):
        return self.__is_start

    def __str__(self):
        return ""

import re

from config import Config
from data.base_log import BaseLogBean

METHOD_FLAG_ENTER = "E"  # E
METHOD_FLAG_EXIT = "X"  # X
METHOD_FLAG_INVALID = None


class QcomHalLogBean(BaseLogBean):
    """
    Qcom HAL log data class.

    create from a stand android hal log format string,like :

    DATE TIME PID TID LEVEL TAG: '<JPEG><INFO>' METHOD: LINE: '[KPI Perf]': FLAG TYPE *

    01-23 14:17:40.031   554  2145 I QCamera : <JPEG><INFO> int qcamera::QCamera2HardwareInterface::openCamera(struct hw_device_t **): 1934: [KPI Perf]: E PROFILE_OPEN_CAMERA camera id 0
    """
    KEY_WORD = "[KPI Perf]"

    def __init__(self, line):
        BaseLogBean.__init__(self, line)
        if self.is_valid():
            self.__msg_data = QcomMsgData(self.msg)

    def __str__(self):
        return BaseLogBean.__str__(self) + "QCOM HAL :\n" \
               + self.__msg_data.__str__()

    def __get_msg_data(self):
        return self.__msg_data

    def get_method_name(self):
        return self.__get_msg_data().get_method_name()

    def get_flag(self):
        return self.__get_msg_data().get_flag()

    def get_type(self):
        return self.__get_msg_data().get_type()

    def is_pair(self, data):
        if (self.is_method_start() and data.is_method_end()) or (self.is_method_end() and data.is_method_start()):
            return self.get_method_name() == data.get_method_name()
        return False

    def is_valid(self):
        return QcomHalLogBean.KEY_WORD in self.msg

    def is_method_start(self):
        return self.is_valid() and self.get_flag() == METHOD_FLAG_ENTER and self.get_type() is not None \
               and Config.is_start_tag(self.get_type())

    def is_method_end(self):
        return self.is_valid() and Config.is_end_tag(self.get_type()) \
               and (self.get_flag() is None or self.get_flag() == METHOD_FLAG_EXIT)


class QcomMsgData:
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

    def __str__(self):
        return "\n method : %s\n flag : %s\n type : %s\n" % (self.get_method_name(), self.get_flag(), self.get_type())

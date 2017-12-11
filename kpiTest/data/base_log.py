import re

from tool.util import date_to_time


class BaseLogBean:
    """
    Base log data class.

    DATE TIME PID TID LEVEL TAG: MSG

    01-23 14:17:40.031   554  2145 I QCamera : <JPEG><INFO> int qcamera::QCamera2HardwareInterface::openCamera(struct hw_device_t **): 1934: [KPI Perf]: E PROFILE_OPEN_CAMERA camera id 0
    """
    msg_pattern = re.compile(r":\s.+$")
    split_pattern = re.compile(r"\s+")

    def __init__(self, line):
        self.date = BaseLogBean.split_pattern.split(line)[0]
        self.time = BaseLogBean.split_pattern.split(line)[1]
        self.pid = int(BaseLogBean.split_pattern.split(line)[2])
        self.tid = int(BaseLogBean.split_pattern.split(line)[3])
        self.level = BaseLogBean.split_pattern.split(line)[4]
        self.tag = BaseLogBean.split_pattern.split(line)[5]

        msg_match = BaseLogBean.msg_pattern.search(line)
        if msg_match:
            self.msg = msg_match.group()[2:]
        else:
            self.msg = None

    def __str__(self):
        result = "Base :\ndate [%s]\ntime [%s]\ntime_stamp [%s]\npid [%s]\ntid [%s]\nlevel [%s]\ntag [%s]\nmsg [%s]\n" % (
            self.date, self.time, self.get_time_stamp(), self.pid, self.tid, self.level, self.tag, self.msg)
        return result

    def __sub__(self, other):
        return self.get_time_stamp() - other.get_time_stamp()

    def get_time_stamp(self):
        millisecond = self.time[-3:]
        date_time = self.date + " " + self.time[:len(self.time) - 4]
        return date_to_time(date_time) * 1000 + int(millisecond)

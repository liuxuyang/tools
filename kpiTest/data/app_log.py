from data.base_log import BaseLogBean
from tool.util import log


class AppLogBean(BaseLogBean):
    """
    APP log data class.

    create from a stand android app log format string,like :

    DATE TIME PID TID LEVEL TAG: MSG

    01-01 03:29:26.425 19741 19741 I APP KPI Perf: PROFILE_STORAGE_PICTURE 197
    """
    TAG = "APP_KPI_Perf"

    def __init__(self, line):
        BaseLogBean.__init__(self, line)
        self.tag = self.tag[:-1]

    def __str__(self):
        return BaseLogBean.__str__(self) + "App :\n"

    def is_valid(self, pid):
        return self.pid == pid and self.tag == AppLogBean.TAG

    def get_duration(self):
        if self.msg:
            return str(self.msg).split(" ")[-1]
        return 0

    def get_type(self):
        if self.msg:
            return str(self.msg).split(" ")[0]
        return None


def app_log_test():
    line = "01-01 07:18:23.193  9328  9328 I APP_KPI_Perf: PROFILE_TAKE_PICTURE 827"
    bean = AppLogBean(line)
    if bean.is_valid(9328):
        print(bean.get_type())
        print(bean.get_duration())
    else:
        print bean.__str__()

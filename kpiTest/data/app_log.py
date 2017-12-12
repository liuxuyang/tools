from data.base_log import BaseLogBean
from data.mode_tag import get_mode_name
from tool.util import log


class AppLogBean(BaseLogBean):
    """
    APP log data class.

    create from a stand android app log format string,like :

    DATE TIME PID TID LEVEL TAG: MSG

    01-01 03:29:26.425 19741 19741 I APP KPI Perf: PROFILE_STORAGE_PICTURE 197
    """
    TAG = "APP_KPI_Perf"
    MODE_TYPE_TAG = "MODE_TYPE"

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

    def has_mode_info(self):
        return self.msg and AppLogBean.MODE_TYPE_TAG in str(self.msg)

    def get_mode_type(self):
        if self.has_mode_info():
            start_index = str(self.msg).find(AppLogBean.MODE_TYPE_TAG)
            end_index = start_index + str(self.msg)[start_index:].find(" ")
            log("start_index : %s & end_index : %s" % (start_index, end_index))
            try:
                mode_index = int(str(self.msg)[start_index:end_index].split(":")[-1])
                log("mode_index : %s" % mode_index)
                return get_mode_name(mode_index)
            except Exception, e:
                log(e.message)
                return None


def app_log_test():
    line = "01-02 16:27:50.501 23146 23146 I APP_KPI_Perf: PROFILE_TAKE_PICTURE  MODE_TYPE:0  2525"
    bean = AppLogBean(line)
    if bean.is_valid(23146):
        print(bean.get_type())
        print(bean.get_duration())
        print(bean.get_mode_type())
    else:
        print bean.__str__()

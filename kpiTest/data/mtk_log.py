from data.base_log import BaseLogBean


class MtkHalLogBean(BaseLogBean):
    """
    MTK HAL log data class.
    """

    def __init__(self, line):
        BaseLogBean.__init__(self, line)

    def __str__(self):
        return BaseLogBean.__str__(self) + "MTK HAL :\n"

from data.base_log import BaseLogBean


class AppLogBean(BaseLogBean):
    """
    APP log data class.

    create from a stand android app log format string,like :

    DATE TIME PID TID LEVEL TAG: MSG

    02-02 08:32:38.614 11511 11540 V FeatureConfig: get key feature =pref_video_quality_key   value=null
    """

    def __init__(self, line):
        BaseLogBean.__init__(self, line)

    def __str__(self):
        return BaseLogBean.__str__(self) + "App :\n"

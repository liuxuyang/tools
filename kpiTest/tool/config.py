import json


class Config:
    def __init__(self):
        pass

    CONFIG_PATH = "./config.json"
    config = None

    @staticmethod
    def open():
        with open(Config.CONFIG_PATH) as f:
            Config.config = json.load(f)
        f.close()
        if Config.config is None:
            raise Exception("config initialization failed")

    @staticmethod
    def get_value(*args):
        if Config.config is None:
            Config.open()
        value = None
        for key in args:
            if value is None:
                value = Config.config[key]
            else:
                value = value[key]
        return value

    @staticmethod
    def is_debug():
        return Config.get_value("debug")

    @staticmethod
    def get_pkg_name():
        return Config.get_value("pkg_name")

    @staticmethod
    def get_min_app_version():
        return Config.get_value("min_app_version")

    @staticmethod
    def get_min_hal_version():
        return Config.get_value("min_hal_version")

    @staticmethod
    def find_end_tag(start_tag):
        # hal
        hal_log_rules = Config.get_value("hal_log")
        for rule in hal_log_rules:
            if start_tag == rule["start_flag"]:
                if rule["end_flag"] == "":
                    return None
                return rule["end_flag"]
        # app

    @staticmethod
    def get_title(log_type, tag):
        print("get_title %s %s" %(log_type,tag))
        log_rules = Config.get_value(log_type)
        if tag is not None:
            for rule in log_rules:
                if rule["tag"] == tag:
                    print(rule["title"])
                    return rule["title"]
        else:
            return "unknown"

    @staticmethod
    def is_start_tag(tag):
        # hal
        hal_log_rules = Config.get_value("hal_log")
        for rule in hal_log_rules:
            if tag == rule["start_flag"]:
                return True
        # app
        return False

    @staticmethod
    def is_end_tag(tag):
        # hal
        hal_log_rules = Config.get_value("hal_log")
        for rule in hal_log_rules:
            if tag == rule["end_flag"] or (tag is None and rule["end_flag"] == ""):
                return True
        # app
        return False

    @staticmethod
    def is_pair(start, end):
        return Config.find_end_tag(start) == end

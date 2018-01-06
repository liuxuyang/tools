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
    def find_end_tag(tag, log_type="hal_log"):
        # hal
        hal_log_rules = Config.get_value(log_type)
        if tag in hal_log_rules.keys():
            return hal_log_rules[tag]["end_flag"]
        return None
        # app

    @staticmethod
    def get_mode_tag(tag, log_type="hal_log"):
        hal_log_rules = Config.get_value(log_type)
        if tag in hal_log_rules.keys() and "mode_flag" in hal_log_rules[tag].keys():
            return hal_log_rules[tag]["mode_flag"]
        return None

    @staticmethod
    def get_mode_method(tag, log_type="hal_log"):
        hal_log_rules = Config.get_value(log_type)
        if tag in hal_log_rules.keys() and "mode_method" in hal_log_rules[tag].keys():
            return hal_log_rules[tag]["mode_method"]
        return None

    @staticmethod
    def get_title(tag, log_type="hal_log"):
        if log_type == "hal_log":
            hal_log_rules = Config.get_value(log_type)
            if tag in hal_log_rules.keys():
                return hal_log_rules[tag]["title"]
            else:
                return "unknown"
        elif log_type == "app_log":
            app_log_rules = Config.get_value(log_type)
            for item in app_log_rules:
                if item["tag"] == tag:
                    return item["title"]

    @staticmethod
    def is_start_tag(flag, log_type="hal_log"):
        # hal
        if log_type == "hal_log":
            hal_log_rules = Config.get_value(log_type)
            for rule in hal_log_rules.keys():
                if hal_log_rules[rule]["start_flag"] == flag:
                    return True
            return False
        # app
        return False

    @staticmethod
    def is_end_tag(flag, log_type="hal_log"):
        # hal
        if log_type == "hal_log":
            hal_log_rules = Config.get_value(log_type)
            for rule in hal_log_rules.keys():
                if hal_log_rules[rule]["end_flag"] == flag:
                    return True
            return False
        # app
        return False

import os
import sys
import re
import subprocess
import time
import logging
import argparse
import ConfigParser

version = "1.0.9"

CFG_PATH = 'config.cfg'

CFG_SECTION_GLOBAL = 'global'

CFG_OPTION_PROJECT_NAME = "PROJECT_NAME"
CFG_OPTION_APP_NAME = "APP_NAME"
CFG_OPTION_CONFIG_PATH = "CONFIG_PATH"
CFG_OPTION_LOG_PATH = "LOG_PATH"
CFG_OPTION_GRADLE_PATH = "GRADLE_PATH"
CFG_OPTION_APK_BUILD_PATH = "APK_BUILD_PATH"
CFG_OPTION_APK_PUSH_PATH = "APK_PUSH_PATH"

CFG_SECTION_LOCAL = 'local'
CFG_OPTION_PROJECT_PATH = "PROJECT_PATH"
CFG_OPTION_APK_INSTALL_PATH = "APK_INSTALL_PATH"

INVALID_SIGN_MSG = "Internal error : invalid sign"
EXIT_MSG = [
    "Normal",  # 0
    "Devices need root",  # 1
    "Devices need remount",  # 2
    "Build fail",  # 3
    "Apk install fail",  # 4
    "Path error,please run this script on project root path",  # 5
    "App restart fail",  # 6
    "App restart fail",  # 7
    "Args invalid",  # 8
]


def init_config():
    global config
    config = ConfigParser.RawConfigParser()
    cur_path = os.path.split(os.path.realpath(__file__))[0]
    cfg_path = os.path.join(cur_path, CFG_PATH)
    if os.path.exists(cfg_path):
        config.read(cfg_path)
    else:
        config.add_section(CFG_SECTION_GLOBAL)

        config.set(CFG_SECTION_GLOBAL, CFG_OPTION_PROJECT_NAME, "CAM_DEBUG_TOOL")
        config.set(CFG_SECTION_GLOBAL, CFG_OPTION_APP_NAME, "ApeCamera")
        config.set(CFG_SECTION_GLOBAL, CFG_OPTION_CONFIG_PATH, cfg_path)
        config.set(CFG_SECTION_GLOBAL, CFG_OPTION_LOG_PATH, os.path.join(os.environ['HOME'], ".log/camera_debug_tool"))
        config.set(CFG_SECTION_GLOBAL, CFG_OPTION_GRADLE_PATH,
                   os.path.join(os.environ['HOME'], '/.gradle/wrapper/dists/'))
        config.set(CFG_SECTION_GLOBAL, CFG_OPTION_APK_BUILD_PATH, "app/build/outputs/apk/")
        config.set(CFG_SECTION_GLOBAL, CFG_OPTION_APK_PUSH_PATH, "/system/priv-app/")

        config.add_section(CFG_SECTION_LOCAL)
        with open(cfg_path, 'wb') as configfile:
            config.write(configfile)


def init_logger():
    global logger
    logger = logging.getLogger(config.get(CFG_SECTION_GLOBAL, CFG_OPTION_PROJECT_NAME))
    formatter = logging.Formatter('%(asctime)s %(levelname)-8s: %(message)s')

    if not os.path.exists(config.get(CFG_SECTION_GLOBAL, CFG_OPTION_LOG_PATH)):
        os.makedirs(config.get(CFG_SECTION_GLOBAL, CFG_OPTION_LOG_PATH))
    log_path = os.path.join(config.get(CFG_SECTION_GLOBAL, CFG_OPTION_LOG_PATH), "log")
    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.setLevel(logging.INFO)


def init_args():
    global args
    parse = argparse.ArgumentParser()

    parse.add_argument("-v", "--version", version=get_version(), action="version", help="prints the version number")

    build_group = parse.add_mutually_exclusive_group()
    build_group.add_argument("-b", "--build", dest="build_path", type=str, help="build app")
    build_group.add_argument("-c", "--choose", dest="build_path_index", action="store_true", default=False,
                             help="choose project path in cache")
    build_group.add_argument("-n", "--no-build", dest="no_build", action="store_true", default=False,
                             help="not build app ,just run with pre-build app")
    build_group.add_argument("-i", "--install", dest="app_path", type=str, help="install app")

    parse.add_argument("-s", dest="device_id", help="install app")
    parse.add_argument("-d", "--debug", action="store_true", default=False, help="run with debug app")
    parse.add_argument("-t", "--test", dest="test", action="store_true", default=False, help="test")
    args = parse.parse_args()


def init_project():
    global project_path
    if args.build_path is not None:
        project_path = args.build_path
        add_to_path_cache(project_path)
    elif args.build_path_index is not None:
        project_path = choose_project_path()
    elif args.no_build:
        project_path = choose_project_path()
    else:
        project_path = None


def init_remote(device_id):
    global apk_install_path
    if config.has_option(CFG_SECTION_LOCAL, CFG_OPTION_APK_INSTALL_PATH):
        paths = eval(config.get(CFG_SECTION_LOCAL, CFG_OPTION_APK_INSTALL_PATH))
        if device_id not in paths.keys():
            apk_install_path = find_install_path(device_id)
            update_config(CFG_SECTION_LOCAL, CFG_OPTION_APK_INSTALL_PATH, device_id, apk_install_path)
        else:
            apk_install_path = paths[device_id]
    else:
        apk_install_path = find_install_path(device_id)
        update_config(CFG_SECTION_LOCAL, CFG_OPTION_APK_INSTALL_PATH, device_id, apk_install_path)


def choose_project_path():
    if not config.has_option(CFG_SECTION_LOCAL, CFG_OPTION_PROJECT_PATH):
        logging.error("there is no cache yet")
        return None
    project_path_dict = eval(config.get(CFG_SECTION_LOCAL, CFG_OPTION_PROJECT_PATH))
    if not args.no_build:
        print_project_path_cache(project_path_dict)
        project_path_index = int(raw_input("pls input project index:"))
    else:
        project_path_index = 0
    if project_path_index is None or len(project_path_dict) == 0:
        sys.exit("there is no cache yet,pls use [-b path]")
    elif 0 > project_path_index or project_path_index >= len(project_path_dict):
        sys.exit("input a invalid index")
    else:
        return project_path_dict[project_path_index]


def add_to_path_cache(path):
    if path is not None or not config.has_option(CFG_SECTION_LOCAL, CFG_OPTION_PROJECT_PATH):
        if config.has_option(CFG_SECTION_LOCAL, CFG_OPTION_PROJECT_PATH):
            cache = eval(config.get(CFG_SECTION_LOCAL, CFG_OPTION_PROJECT_PATH))
        else:
            cache = []
        if path not in cache:
            cache.append(path)
        else:
            return
    else:
        logger.warn("add a none path to cache")
        return
    config.set(CFG_SECTION_LOCAL, CFG_OPTION_PROJECT_PATH, cache)
    save_config()


def update_config(section, option, key, value):
    if value is not None or not config.has_option(section, option):
        if config.has_option(section, option):
            cache = eval(config.get(section, option))
        else:
            cache = dict()
        if key in cache.keys() and cache.get(key) != value:
            logger.warn("device %s has change apk install path")
        cache[key] = value
    else:
        logger.warn("add a none path to cache")
        return
    config.set(section, option, value)
    save_config()


def get_device_id():
    # Get a list of connected devices
    devices = []
    command = "adb devices"
    output, error, code = run_task(command)
    for line in output.split(os.linesep):
        device_info = line.split()
        if len(device_info) == 2 and device_info[1] == "device":
            devices.append(device_info[0])

    if len(devices) == 0:
        sys.exit("No device is connected!")
    elif args.device_id is not None and args.device_id not in devices:
        sys.exit("%s is connected!" % args.device_id)
    elif args.device_id is not None:
        return [args.device_id]
    else:
        return devices


def get_key(section, option):
    if section == CFG_SECTION_LOCAL:
        if option == CFG_OPTION_PROJECT_PATH:
            return


def save_config():
    cfg_path = config.get(CFG_SECTION_GLOBAL, CFG_OPTION_CONFIG_PATH)
    with open(cfg_path, 'wb') as configfile:
        config.write(configfile)


def print_project_path_cache(cache):
    for i in xrange(len(cache)):
        print ("%s : %s\n" % (i, cache[i]))


def run_task(cmd):
    command = "%s" % cmd
    proc = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = proc.communicate()
    return_code = proc.returncode
    return output.strip(), error.strip(), return_code


def root_devices(device_id):
    if 0 != os.system('adb -s %s root' % device_id):
        exit_with_msg(1)


def remount_devices(device_id):
    if 0 != os.system('adb -s %s remount' % device_id):
        exit_with_msg(2)


def build_apk():
    if not go2project_dir():
        exit_with_msg(5)
    if 0 != os.system("%s build" % find_gradle_path()):
        exit_with_msg(3)


def find_apk_path(cur_project_path, is_debug):
    outs_path = os.path.join(cur_project_path, config.get(CFG_SECTION_GLOBAL, CFG_OPTION_APK_BUILD_PATH))
    apk_name = config.get(CFG_SECTION_GLOBAL, CFG_OPTION_APP_NAME)
    apks = []
    for root, dirs, files in os.walk(outs_path):
        for fn in files:
            if apk_name in fn and fn.endswith(".apk"):
                apks.append(os.path.join(root, fn))

    if len(apks) > 2:
        logger.warn("find to many apks : %s" % str(apks))

    debug_file = None
    release_file = None
    for name in apks:
        if "-debug" in name:
            debug_file = name
        else:
            release_file = name

    return release_file if is_debug else debug_file


def find_install_path(device_id):
    cmd = "adb -s %s shell ls /system/priv-app/" % device_id
    result = os.popen(cmd).read()
    for l in result.splitlines():
        if config.get(CFG_SECTION_GLOBAL, CFG_OPTION_APP_NAME) in l:
            return os.path.join(l, l + ".apk")


def install_apk(device_id, apk_path, is_debug):
    logger.info("install debug %s" % is_debug)
    if apk_path is None:
        install_apk_path = find_apk_path(project_path, is_debug)
    else:
        install_apk_path = apk_path

    cmd = 'adb -s %s push %s %s' % (device_id, install_apk_path, apk_install_path)
    if 0 != os.system(cmd):
        exit_with_msg(4)


def restart_app(device_id):
    apk_name = "com.myos.camera"
    if 0 != os.system('adb -s %s shell am force-stop %s' % (device_id, apk_name)):
        exit_with_msg(6)

    if 0 != os.system(
            'adb -s %s shell am start -a android.intent.action.MAIN -c android.intent.category.LAUNCHER -n '
            '%s/%s.activity.CameraActivity' % (device_id, apk_name, apk_name)):
        exit_with_msg(7)


def find_gradle_path():
    cur_path = os.getcwd()
    try:
        build_file = open(os.path.join(cur_path, '/gradle/wrapper/gradle-wrapper.properties'), 'r')

        gradle_version = 'gradle-3.3-all'
        for line in build_file.readlines():
            if '//services.gradle.org/distributions/' in line:
                gradle_version = line.split('/')[-1][:-5]
        logger.info('gradle version : ' + gradle_version)
        gradle_full_path = config.get(CFG_SECTION_GLOBAL, CFG_OPTION_GRADLE_PATH) + str(gradle_version)
        files = os.listdir(gradle_full_path)
        if os.path.isdir(os.path.join(gradle_full_path, files[0])):
            return os.path.join(gradle_full_path, files[0], gradle_version[:-4], '/bin/gradle')
        else:
            exit_with_msg(5)
    except IOError:
        exit_with_msg(5)


def exit_with_msg(sign):
    if sign >= len(EXIT_MSG):
        logger.critical(INVALID_SIGN_MSG)
        exit(-1)
    else:
        if sign != 0:
            logger.error(EXIT_MSG[sign])
        exit(sign)


def go2project_dir():
    logger.info(project_path)
    if project_path is not None:
        os.chdir(project_path)
        return True
    else:
        logger.error("project path has not set already")
        return False


def get_version():
    return version


def test():
    init_config()


def main():
    """
    Myos Camera debug tools.
    This program provide build & install Tinno ApeCamera features.
    """
    init_config()
    init_logger()
    init_args()
    init_project()
    init_remote()
    if args.test:
        test()
        exit(0)

    for device_id in get_device_id():
        if args.app_path is not None:
            root_devices(device_id)
            remount_devices(device_id)
            install_apk(device_id, args.app_path, args.debug)
            restart_app(device_id)
            exit_with_msg(0)
        else:
            start_time = time.time()
            root_devices(device_id)
            remount_devices(device_id)
            if not args.no_build:
                logger.info("start build")
                build_apk()
            install_apk(device_id, None, args.debug)
            restart_app(device_id)
            duration = time.time() - start_time
            logger.info("end! duration : %s" % duration)
            exit_with_msg(0)


if __name__ == '__main__':
    main()

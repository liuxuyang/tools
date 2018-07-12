import os
import sys
import subprocess
import time
import logging
import argparse
import ConfigParser

# version code
version = "1.2.0"
# config file name
CFG_PATH = 'config.cfg'
# section tags
CFG_SECTION_GLOBAL = 'global'
CFG_SECTION_DEVICES_PREFIX = 'device_'
CFG_SECTION_PROJECT_PREFIX = 'project_'
# global options
GLOBAL_OPTION_PROJECT_NAME = "PROJECT_NAME"
GLOBAL_OPTION_APP_NAME = "APP_NAME"
GLOBAL_OPTION_APP_PKG_NAME = "APP_PKG_NAME"
GLOBAL_OPTION_LOG_PATH = "LOG_PATH"
GLOBAL_OPTION_MONKEY_LOG_PATH = "MONKEY_LOG_PATH"
GLOBAL_OPTION_APK_BUILD_PATH = "APK_BUILD_PATH"
GLOBAL_OPTION_APK_PUSH_PATH = "APK_PUSH_PATH"
# devices options
DEV_OPTION_APK_INSTALL_PATH = "APK_INSTALL_PATH"
# projects options
PJT_OPTION_PROJECT_PATH = "PROJECT_PATH"
PJT_OPTION_PRODUCT_FLAVORS = "PRODUCT_FLAVORS"

#
CONFIG_SEP = ','

# error msg
INVALID_SIGN_MSG = "Internal error : invalid sign"
EXIT_MSG = [
    "Normal",  # 0
    "Devices need root",  # 1
    "Devices need remount",  # 2
    "Build fail",  # 3
    "Apk install fail",  # 4
    "Project path error",  # 5
    "App restart fail",  # 6
    "App path error",  # 7
    "Args invalid",  # 8
]


def init_config():
    global config, cfg_path
    config = ConfigParser.RawConfigParser()
    cur_path = os.path.split(os.path.realpath(__file__))[0]
    cfg_path = os.path.join(cur_path, CFG_PATH)
    if os.path.exists(cfg_path):
        config.read(cfg_path)
    else:
        config.add_section(CFG_SECTION_GLOBAL)

        config.set(CFG_SECTION_GLOBAL, GLOBAL_OPTION_PROJECT_NAME, "CAM_DEBUG_TOOL")
        config.set(CFG_SECTION_GLOBAL, GLOBAL_OPTION_APP_NAME, "ApeCamera")
        config.set(CFG_SECTION_GLOBAL, GLOBAL_OPTION_APP_PKG_NAME, "com.myos.camera")
        config.set(CFG_SECTION_GLOBAL, GLOBAL_OPTION_LOG_PATH,
                   os.path.join(os.environ['HOME'], ".log/camera_debug_tool"))
        config.set(CFG_SECTION_GLOBAL, GLOBAL_OPTION_MONKEY_LOG_PATH, os.path.join(os.environ['HOME'], ".log/monkey"))
        config.set(CFG_SECTION_GLOBAL, GLOBAL_OPTION_APK_BUILD_PATH, "app/build/outputs/apk/")
        config.set(CFG_SECTION_GLOBAL, GLOBAL_OPTION_APK_PUSH_PATH, "system/priv-app/")

        with open(cfg_path, 'wb') as configfile:
            config.write(configfile)


def init_logger():
    global logger
    logger = logging.getLogger(config.get(CFG_SECTION_GLOBAL, GLOBAL_OPTION_PROJECT_NAME))
    formatter = logging.Formatter('%(asctime)s %(levelname)-8s: %(message)s')

    if not os.path.exists(config.get(CFG_SECTION_GLOBAL, GLOBAL_OPTION_LOG_PATH)):
        os.makedirs(config.get(CFG_SECTION_GLOBAL, GLOBAL_OPTION_LOG_PATH))
    log_path = os.path.join(config.get(CFG_SECTION_GLOBAL, GLOBAL_OPTION_LOG_PATH), "log")
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

    commend_group = parse.add_argument_group(title="commend")
    commend_group.add_argument("-v", version=get_version(), action="version",
                               help="prints the version number")
    commend_group.add_argument("-d", dest="debug", action="store_true", default=False, help="run with debug app")
    commend_group.add_argument("-t", dest="test", action="store_true", default=False, help="test")
    commend_group.add_argument("-r", dest="reset", action="store_true", default=False,
                               help="reset tool's local config")
    commend_group.add_argument("-e", dest="device_id", help="specified device id")
    commend_group.add_argument("-f", dest="flavors", type=str, help="specify product flavors")
    commend_group.add_argument("-p", dest="project_path", type=str, help="specify project path")

    build_group = parse.add_argument_group(title="build & install").add_mutually_exclusive_group()
    build_group.add_argument("-b", dest="build", action="store_true", default=False,
                             help="build & install app")
    build_group.add_argument("-c", dest="clean", action="store_true", default=False, help="clean build cache")
    build_group.add_argument("-n", dest="no_build", action="store_true", default=False,
                             help="install app , find app path in current dir")
    build_group.add_argument("-i", dest="install_app_path", type=str, help="install app")

    monkey_group = parse.add_argument_group(title="monkey")
    monkey_group.add_argument("-m", dest="monkey", action="store_true", help="run monkey with default options")
    monkey_group.add_argument("-o", dest="monkey_options", help="specified monkey options")

    args = parse.parse_args()


def init_project():
    if args.project_path:
        project_path = args.project_path
    else:
        project_path = os.getcwd()

    if check_project_path(project_path):
        add_to_cache(get_project_section(-1), PJT_OPTION_PROJECT_PATH, project_path)
    else:
        project_path = choose_project(PJT_OPTION_PROJECT_PATH, None)

    if project_path is None:
        exit_with_msg(5)

    if args.flavors:
        flavors = args.flavors
    else:
        flavors = choose_flavors(project_path, "")

    return project_path, flavors


def init_remote(device_id):
    section = get_device_section(device_id)
    if config.has_section(section):
        apk_install_path = config.get(section, DEV_OPTION_APK_INSTALL_PATH)
    else:
        apk_install_path = find_install_path(device_id)
        add_to_cache(section, DEV_OPTION_APK_INSTALL_PATH, apk_install_path)
    return apk_install_path


def choose_sections():
    list_data = []
    for section in config.sections():
        if CFG_SECTION_GLOBAL != section:
            list_data.append(section)
    return choose(list_data, None)


def choose(list_data, default):
    if list_data is None or len(list_data) == 0:
        logger.debug("there is no cache yet")
        return default
    print_choose_cache(list_data)
    choose_index = int(raw_input("pls input index:"))
    if 0 > choose_index or choose_index >= len(list_data):
        sys.exit("input a invalid index")
    else:
        return list_data[choose_index]


def choose_project(option, default):
    prefix = CFG_SECTION_PROJECT_PREFIX
    project_list = []
    for section in config.sections():
        if prefix in section:
            data = config.get(section, option)
            project_list.append(data)
    return choose(project_list, default)


def choose_flavors(project_path, default):
    prefix = CFG_SECTION_PROJECT_PREFIX
    list_data = []
    for section in config.sections():
        if prefix in section:
            data = config.get(section, PJT_OPTION_PROJECT_PATH)
            if data == project_path and config.has_option(section, PJT_OPTION_PRODUCT_FLAVORS):
                list_data = str(config.get(section, PJT_OPTION_PRODUCT_FLAVORS)).split(CONFIG_SEP)
    return choose(list_data, default)


def add_to_cache(section, option, value, cover=True):
    if value is None or section is None:
        logger.error("add to cache error, why [%s-%s : %s]" % (section, option, value))
        return
    if config.has_section(section):
        cache = ""
        if config.has_option(section, option) and not cover:
            cache = config.get(section, option)
        if value not in cache.split(CONFIG_SEP):
            config.set(section, option, "%s,%s" % (cache, value) if cache else value)
    else:
        config.add_section(section)
        config.set(section, option, value)
    save_config()


def check_project_path(path):
    if path is None:
        return False
    else:
        # rough check
        return "settings.gradle" in os.listdir(path)


def remove_config(section):
    if config.remove_section(section):
        logger.info("reset %s config successful!" % section)
        save_config()
    else:
        logger.info("reset %s config fail!" % section)


def get_device_section(id):
    prefix = CFG_SECTION_DEVICES_PREFIX
    if id is None:
        logger.error("get device section with error %s" % id)
        exit_with_msg(8)
    else:
        return "%s%s" % (prefix, id)


def get_project_section(value):
    prefix = CFG_SECTION_PROJECT_PREFIX
    if isinstance(value, int):
        index = int(value)
        if index >= 0:
            project_section_count = index
        else:
            sections = config.sections()
            project_section_count = 0
            for section in sections:
                if prefix in section:
                    project_section_count += 1
        return "%s%s" % (prefix, project_section_count)
    elif isinstance(value, str):
        project_path = str(value)
        for section in config.sections():
            if prefix in section:
                if project_path == config.get(section, PJT_OPTION_PROJECT_PATH):
                    return section
    else:
        logger.error("get project section with error %s" % value)
        exit_with_msg(8)


def reset_config():
    section = choose_sections()
    remove_config(section)


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
        sys.exit("%s is not connected!" % args.device_id)
    elif args.device_id is not None:
        return [args.device_id]
    else:
        return devices


def save_config():
    with open(cfg_path, 'wb') as configfile:
        config.write(configfile)


def print_choose_cache(cache):
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


def clean(project_path):
    logger.info("clean project build")
    start_time = time.time()
    if not go2project_dir(project_path):
        exit_with_msg(5)
    if 0 != os.system("%s clean" % find_gradle_path(project_path)):
        exit_with_msg(3)
    duration = time.time() - start_time
    logger.info("end! duration : %s" % duration)


def build_apk(project_path, flavors, is_debug):
    logger.info("start build")
    start_time = time.time()
    if not go2project_dir(project_path):
        exit_with_msg(5)

    build_cmd = "%s %s" % (find_gradle_path(project_path), gradle_build_task_name(flavors, is_debug))
    logger.info("run build task : %s " % build_cmd)
    if 0 != os.system(build_cmd):
        exit_with_msg(3)

    # save product flavors
    if flavors:
        add_to_cache(get_project_section(project_path), PJT_OPTION_PRODUCT_FLAVORS, flavors, False)

    duration = time.time() - start_time
    logger.info("end! duration : %s" % duration)

    apk_path = find_apk_path(project_path, flavors, is_debug)
    logger.info("build apk's path : %s " % apk_path)
    return apk_path


def install(app_path):
    if app_path is None:
        exit_with_msg(7)
    logger.info("install apk : " + app_path)
    for device_id in get_device_id():
        root_devices(device_id)
        remount_devices(device_id)

        install_path = init_remote(device_id)
        install_apk(device_id, app_path, install_path)
        restart_app(device_id)


def find_apk_path(cur_project_path, flavors, is_debug):
    outs_path = os.path.join(cur_project_path, config.get(CFG_SECTION_GLOBAL, GLOBAL_OPTION_APK_BUILD_PATH))
    apk_name = config.get(CFG_SECTION_GLOBAL, GLOBAL_OPTION_APP_NAME)
    apk_path = []

    def find_apk(arg, dirname, files):
        for fn in files:
            file_path = os.path.join(dirname, fn)
            if (not flavors or flavors in file_path) \
                    and (not is_debug or "debug" in fn) \
                    and apk_name in fn \
                    and fn.endswith(".apk") \
                    and os.path.isfile(file_path):
                apk_path.append(file_path)

    os.path.walk(outs_path, find_apk, ())
    if len(apk_path) == 0:
        return None
    else:
        return apk_path[0]


def find_install_path(device_id):
    cmd = "adb -s %s shell ls /system/priv-app/" % device_id
    result = os.popen(cmd).read()
    for l in result.splitlines():
        if config.get(CFG_SECTION_GLOBAL, GLOBAL_OPTION_APP_NAME) in l:
            return os.path.join("/system/priv-app/", l, l + ".apk")


def install_apk(device_id, apk_path, install_path):
    if apk_path is None:
        exit_with_msg(8)

    install_apk_path = apk_path

    cmd = 'adb -s %s push %s %s' % (device_id, install_apk_path, install_path)
    if 0 != os.system(cmd):
        exit_with_msg(4)


def restart_app(device_id):
    apk_name = "com.myos.camera"
    if 0 != os.system('adb -s %s shell am force-stop %s' % (device_id, apk_name)):
        exit_with_msg(6)

    if 0 != os.system(
            'adb -s %s shell am start -a android.intent.action.MAIN -c android.intent.category.LAUNCHER -n '
            '%s/%s.activity.CameraActivity' % (device_id, apk_name, apk_name)):
        exit_with_msg(6)


def find_gradle_path(project_path):
    try:
        gradlew_path = os.path.join(project_path, 'gradlew')
        if os.path.exists(gradlew_path):
            return gradlew_path
        else:
            exit_with_msg(5)
    except IOError, e:
        logger.error(e.message)
        exit_with_msg(5)


def gradle_build_task_name(flavors, is_debug):
    prefix = "assemble"
    suffix = "Release" if not is_debug else "Debug"
    task_name = prefix + title_str(flavors) + suffix
    logger.error("task_name " + task_name)
    return task_name


def title_str(s):
    if s is not None and len(s) > 0:
        return s[0].upper() + s[1:]
    else:
        return ""


def build_monkey_log(device_id):
    log_root = config.get(CFG_SECTION_GLOBAL, GLOBAL_OPTION_MONKEY_LOG_PATH)
    date_str = time.strftime("%y%m%d")
    time_str = time.strftime("%H%M%S")
    log_path = os.path.join(log_root, date_str)
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    main_log = os.path.join(log_root, date_str, "logcat_%s_%s.log" % (device_id, time_str))
    monkey_log = os.path.join(log_root, date_str, "monkey_%s_%s.log" % (device_id, time_str))
    return main_log, monkey_log


def monkey(pkg_name):
    proc_info = dict()
    for device_id in get_device_id():
        per_run_monkey(device_id)
        logcat_log, monkey_log = build_monkey_log(device_id)
        proc_info[device_id] = [run_logcat(device_id, logcat_log), run_monkey(device_id, pkg_name, monkey_log)]
    wait_monkey_stop(proc_info)
    exit_with_msg(0)


def wait_monkey_stop(proc_info):
    print("now there are %s devices run monkey,they are %s" % (len(proc_info.keys()), proc_info.keys()))
    input_str = raw_input("input q <id> to quit a specify device or quit all tasks without specified id :\n")

    if input_str.startswith("q"):
        if len(input_str) > 2:
            device_id = input_str[2:]
            if device_id in proc_info.keys() and device_id in get_device_id():
                procs = proc_info.pop(device_id)
                stop(procs, procs)
            else:
                print("you should input id which in %s " % proc_info.keys())
        else:
            ids = get_device_id()
            for device_id in proc_info.keys():
                procs = proc_info.pop(device_id)
                if device_id in ids:
                    stop(procs, device_id)

    if proc_info:
        wait_monkey_stop(proc_info)


def stop(procs, device_id):
    # stop logging
    procs[0].kill()
    # stop monkey logging
    procs[1].kill()
    # stop monkey
    stop_monkey(device_id)


def stop_monkey(device_id):
    # stop monkey on specify device
    cmd = "adb -s %s shell ps | awk '/com\.android\.commands\.monkey/ { system(\"adb -s %s shell kill \" $2) }'" % (
        device_id, device_id)
    logger.debug("stop monkey : %s " % cmd)
    if 0 != os.system(cmd):
        exit_with_msg("stop monkey fail")


def run_monkey(device_id, pkg_name, log):
    count = 5000000
    option = "monkey --pct-touch 50 --pct-motion 15 --pct-anyevent 5 --pct-majornav 12 --pct-trackball 1 --pct-nav 0 " \
             "--pct-syskeys 15 --pct-appswitch 2 --throttle 200 -p %s -s 500 " \
             "--ignore-security-exceptions --ignore-crashes --ignore-timeouts --ignore-native-crashes -v -v %d " \
             % (pkg_name, count)

    if args.monkey_options is not None:
        option = args.monkey_options
    command = "adb -s %s shell %s %s" % (device_id, option, count)
    log_file = open(log, 'wb')
    proc = subprocess.Popen(command.split(), stdout=log_file, stderr=log_file)
    logger.info("start monkey pid : %s for device : %s, and log save at %s" % (proc.pid, device_id, log))
    return proc


def per_run_monkey(device_id):
    logcat_size = '16M'
    set_logcat_size = "adb -s %s logcat -G %s" % (device_id, logcat_size)
    proc = subprocess.Popen(set_logcat_size.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    proc.communicate()


def run_logcat(device_id, log):
    logging_command = "adb -s %s logcat" % device_id
    log_file = open(log, 'wb')
    proc = subprocess.Popen(logging_command.split(), stdout=log_file, stderr=log_file)
    logger.info("start logcat pid : %s for device : %s, and log save at %s" % (proc.pid, device_id, log))
    return proc


def exit_with_msg(sign):
    if sign >= len(EXIT_MSG):
        logger.critical(INVALID_SIGN_MSG)
        exit(-1)
    else:
        if sign != 0:
            logger.error(EXIT_MSG[sign])
        exit(sign)


def go2project_dir(project_path):
    logger.info("project path : %s" % project_path)
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
    # global init
    init_config()
    init_logger()
    init_args()

    # options
    if args.test:
        test()
    elif args.reset:
        reset_config()
    elif args.monkey or args.monkey_options:
        pkg_name = config.get(CFG_SECTION_GLOBAL, GLOBAL_OPTION_APP_PKG_NAME)
        monkey(pkg_name)
    elif args.clean:
        project_path, flavors = init_project()
        clean(project_path)
    elif args.build:
        project_path, flavors = init_project()
        apk_path = build_apk(project_path, flavors, args.debug)
        install(apk_path)
    elif args.no_build:
        project_path, flavors = init_project()
        apk_path = find_apk_path(project_path, flavors, args.debug)
        install(apk_path)
    elif args.install_app_path:
        apk_path = args.install_app_path
        install(apk_path)
    else:
        logger.warn("pls input a option! Use '-h' show help info")


if __name__ == '__main__':
    main()

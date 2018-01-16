import os
import sys
import re
import subprocess
from datetime import datetime

CONFIG_PATH = "config"
GRADLE_PATH = os.environ['HOME'] + '/.gradle/wrapper/dists/'
APK_BUILD_PATH = "app/build/outputs/apk/"
APK_PUSH_PATH = "/system/priv-app/"
APP_NAME = "ApeCamera"
VERSION_TYPE_KEYS = ["stable", "beta"]
VERSION_TYPE = {"stable": "master", "beta": "develop"}

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

IS_DEBUG = True
config = None


def init_config():
    pass


def log(msg):
    if IS_DEBUG and msg is not None:
        if not isinstance(msg, str):
            msg = str(msg)
        msg_array = msg.split(os.linesep)
        for msg_line in msg_array:
            if msg_line:
                print "%s : %s" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), msg_line)


def run_task(cmd):
    command = "%s" % cmd
    proc = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = proc.communicate()
    return_code = proc.returncode
    return output, error, return_code


def root_devices():
    if 0 != os.system('adb root'):
        exit_with_msg(1)


def remount_devices():
    if 0 != os.system('adb remount'):
        exit_with_msg(2)


def clear_old_apk():
    os.system("rm -rf " + APK_BUILD_PATH)


def build_apk():
    if 0 != os.system("%s build" % find_gradle_path()):
        exit_with_msg(3)


def find_install_path():
    cmd = "adb shell ls /system/priv-app/"
    result = os.popen(cmd).read()
    for l in result.splitlines():
        if APP_NAME in l:
            return l


def install_apk(apk_path, is_debug):
    debug_file = ""
    release_file = ""
    apks = []
    for root, dirs, files in os.walk(APK_BUILD_PATH):
        for fn in files:
            if APP_NAME in fn:
                apks.append(os.path.join(root, fn))

    for name in apks:
        if "-debug.apk" in name:
            debug_file = name
        else:
            release_file = name
    if not apk_path:
        if is_debug:
            install_apk_path = debug_file
        else:
            install_apk_path = release_file
    else:
        install_apk_path = apk_path

    install_file_path = find_install_path()
    install_file_name = find_install_path() + '.apk'
    push_path = os.path.join(APK_PUSH_PATH, install_file_path, install_file_name, )
    cmd = 'adb push ' + install_apk_path + " " + push_path
    if 0 != os.system(cmd):
        exit_with_msg(4)


def restart_app():
    apk_name = "com.myos.camera"
    if 0 != os.system('adb shell am force-stop ' + apk_name):
        exit_with_msg(6)

    if 0 != os.system('adb shell am start -a android.intent.action.MAIN -c android.intent.category.LAUNCHER -n '
                      + apk_name + '/' + apk_name + '.activity.CameraActivity'):
        exit_with_msg(7)


def find_gradle_path():
    cur_path = os.getcwd()
    try:
        build_file = open(cur_path + '/gradle/wrapper/gradle-wrapper.properties', 'r')

        gradle_version = 'gradle-3.3-all'
        for line in build_file.readlines():
            if '//services.gradle.org/distributions/' in line:
                gradle_version = line.split('/')[-1][:-5]
        log('gradle version : ' + gradle_version)
        gradle_full_path = GRADLE_PATH + str(gradle_version)
        files = os.listdir(gradle_full_path)
        if os.path.isdir(gradle_full_path + '/' + files[0]):
            return gradle_full_path + '/' + files[0] + '/' + gradle_version[:-4] + '/bin/gradle'
        else:
            exit_with_msg(5)
    except IOError:
        exit_with_msg(5)


def exit_with_msg(sign):
    if sign >= len(EXIT_MSG):
        print INVALID_SIGN_MSG
        exit(-1)
    else:
        if sign != 0:
            print EXIT_MSG[sign]
        exit(sign)


def go_script_dir():
    os.chdir(os.path.dirname(os.path.realpath(__file__)))


def get_version():
    go_script_dir()
    key = "version"
    for i in open(CONFIG_PATH).readlines():
        if i.startswith(key):
            return i.split(":")[-1].strip(" ").lstrip("\"").rstrip("\"") + " " + get_version_type()
    return "Can't find version code."


def update():
    go_script_dir()
    if 0 != os.system("git reset --hard HEAD && git pull --rebase"):
        print "Can't update!"


def get_version_type(branch=None):
    if branch is None:
        out, err, code = run_task("git branch -v")
        if 0 == code:
            for line in out.split(os.linesep):
                if line.startswith("*"):
                    branch = line.split(" ")[1]
    for key in VERSION_TYPE.keys():
        if VERSION_TYPE.get(key) == branch:
            return key
    exit_with_msg(8)


def switch_stable_version(index):
    branch = None
    try:
        index = int(index)
        if index >= 0 and index < len(VERSION_TYPE_KEYS):
            branch = VERSION_TYPE.get(VERSION_TYPE_KEYS[int(index)])
        else:
            exit_with_msg(8)
    except:
        exit_with_msg(8)
    if branch:
        go_script_dir()
        if 0 != os.system("git checkout %s" % branch):
            print "Can't switch!"


def turn_on_screen():
    screen_id = ''
    for s in sys.argv[1:]:
        if s[:7] == 'screen=' and len(s) > 7:
            screen_id = s[7:]

    if not screen_id:
        print 'Error: need to specify screen serial'
        assert False

    cmd = ('adb -s %s shell dumpsys power | egrep "Display Power"'
           % screen_id)
    process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
    cmd_ret = process.stdout.read()
    screen_state = re.split(r'[s|=]', cmd_ret)[-1]
    if screen_state == 'OFF\n':
        wakeup = ('adb -s %s shell input keyevent POWER' % screen_id)
        subprocess.Popen(wakeup.split())


def main():
    """
    This program provide build & install Tinno ApeCamera features.
    Options include:
    --version       : Prints the version number
    --help          : Display this help
    --update        : Update this program
    --switch [0:stable 1:beta]   : switch this program to  stable/beta version

    -i [<apk_path>] : just install app, do not rebuild
    -d:             : install debug app
    """
    # log(sys.argv)

    run = True
    just_install = False
    install_debug = False
    if len(sys.argv) < 2:
        exit_with_msg(8)
    option = sys.argv[1]
    apk_path = None

    if option.startswith("--"):
        run = False
        if option == "--help":
            print main.__doc__
        elif option == "--version":
            print get_version()
        elif option == "--update":
            update()
        elif option == "--switch":
            log("start switch")
            switch_stable_version(sys.argv[2])
            log("end switch")
        elif option == "--test":
            test()
        else:
            exit_with_msg(8)
        exit_with_msg(0)

    elif option.startswith("-"):
        if "d" in option:
            install_debug = True
        if "i" in option:
            just_install = True
            if len(sys.argv) == 3:
                apk_path = sys.argv[2]

    else:
        exit_with_msg(8)

    if run:
        init_config()
        root_devices()
        remount_devices()
        if not just_install:
            clear_old_apk()
            log("start build")
            build_apk()
        install_apk(apk_path, install_debug)
        restart_app()
        log("end!")
        exit_with_msg(0)


def test():
    log(get_version_type())


if __name__ == '__main__':
    main()

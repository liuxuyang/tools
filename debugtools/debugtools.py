import os
import sys

CONFIG_PATH = "config"
GRADLE_PATH = os.environ['HOME'] + '/.gradle/wrapper/dists/'
APK_BUILD_PATH = "app/build/outputs/apk/"
APK_PUSH_PATH = "/system/priv-app/"
APP_NAME = "ApeCamera"
APP_NAME_BRANCH_CODE = "50"

INVALID_SIGN_MSG = "Internal error : invalid sign"
EXIT_MSG = [
    "Normal",  # 0
    "Devices need root",  # 1
    "Devices need remount",  # 2
    "Build fail",  # 3
    "Apk install fail",  # 4
    "Path error,please run this script on project root path",  # 5
    "",  # 6
    "",  # 7
    "Args invalid",  # 8
]

IS_DEBUG = True


def log(msg):
    if IS_DEBUG:
        print msg


def root_devices():
    if 0 != os.system('adb root'):
        exit_with_msg(1)


def remount_devices():
    if 0 != os.system('adb remount'):
        exit_with_msg(2)


def build_apk():
    if 0 != os.system(find_gradle_path() + " build"):
        exit_with_msg(3)


def install_apk():
    apk_path = 'app/build/outputs/apk/ApeCamera50-debug.apk'
    push_path = '/system/priv-app/ApeCamera45/ApeCamera45.apk'
    cmd = 'adb push ' + apk_path + " " + push_path
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


def get_version():
    key = "version:"
    for i in open(CONFIG_PATH).readlines():
        if i.startswith(key):
            return i[len(key):]
    return "Can't find version code."


def update():
    if 0 != os.system("git pull --rebase"):
        print "Can't update!"


def main():
    """
    This program provide build & install Tinno ApeCamera features.
    Options include:
    --version : Prints the version number
    --help    : Display this help
    --update  : Update this program
    """
    log(sys.argv)

    run = True

    for argv in sys.argv[1:]:
        if argv.startswith("--"):
            run = False
            option = argv[2:]
            if option == "help":
                print main.__doc__
            elif option == "version":
                print get_version()
            elif option == "update":
                update()
            else:
                exit_with_msg(8)
            exit_with_msg(0)

        elif argv.startswith("-"):
            pass
        else:
            exit_with_msg(8)

    if run:
        root_devices()
        remount_devices()
        build_apk()
        install_apk()
        restart_app()
        exit_with_msg(0)


if __name__ == '__main__':
    main()

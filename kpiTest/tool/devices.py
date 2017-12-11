import json
import os
import re
import subprocess
import time
from config import Config
from error import Error
from util import log
import sys
import unittest

pkg_name = Config.get_pkg_name()
CAMERA_STATE_CLOSED = 0
CAMERA_STATE_OPENED = 1 << 0
CAMERA_STATE_VISIBLE = 1 << 1

PLATFORM_QCOM = "qcom"
PLATFORM_MTK = "mtk"
PLATFORM_UNKNOWN = "UNKNOWN"


def run_adb_task(command):
    proc = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output, error = proc.communicate()
    return output, error


def get_device_id():
    """ Return the ID of the device that the test is running on.

    Return the device ID provided in the command line if it's connected. If no
    device ID is provided in the command line and there is only one device
    connected, return the device ID by parsing the result of "adb devices".
    Also, if the environment variable ANDROID_SERIAL is set, use it as device
    id. When both ANDROID_SERIAL and device argument present, device argument
    takes priority.

    Raise an exception if no device is connected; or the device ID provided in
    the command line is not connected; or no device ID is provided in the
    command line or environment variable and there are more than 1 device
    connected.

    Returns:
        Device ID string.
    """
    device_id = None

    # Check if device id is set in env
    if "ANDROID_SERIAL" in os.environ:
        device_id = os.environ["ANDROID_SERIAL"]

    for s in sys.argv[1:]:
        if s[:7] == "device=" and len(s) > 7:
            device_id = str(s[7:])

    # Get a list of connected devices
    devices = []
    command = "adb devices"
    output, error = run_adb_task(command)
    for line in output.split(os.linesep):
        device_info = line.split()
        if len(device_info) == 2 and device_info[1] == "device":
            devices.append(device_info[0])

    if len(devices) == 0:
        raise Error("No device is connected!")
    elif device_id is not None and device_id not in devices:
        raise Error(device_id + " is not connected!")
    elif device_id is None and len(devices) >= 2:
        raise Error("More than 1 device are connected. " +
                    "Use device=<device_id> to specify a device to test.")
    elif len(devices) == 1:
        device_id = devices[0]

    return device_id


def get_platform():
    command = "adb shell getprop ro.board.platform"
    output, error = run_adb_task(command)
    if output.startswith("msm"):
        return PLATFORM_QCOM
    elif output.startswith("mt"):
        return PLATFORM_MTK
    else:
        return PLATFORM_UNKNOWN


def get_sdk_version():
    command = "adb shell getprop ro.build.version.sdk"
    output, error = run_adb_task(command)
    return int(output)


def get_system_custom_build_version():
    command = "adb shell getprop ro.custom.build.version"
    output, error = run_adb_task(command)
    return output.strip()


def get_app_version():
    command = "adb shell pm dump %s | grep versionName" % pkg_name
    output, error = run_adb_task(command)
    if len(output.strip().split(os.linesep)) == 1:
        return output.split("=")[-1].strip()
    else:
        raise Error("get app version fail")


def get_hal_pid(sdk_version):
    if sdk_version >= 26:
        filter_tag = "android.hardware.camera.provider"
    else:
        filter_tag = "cameraserver"
    command = "adb shell ps | grep %s" % filter_tag
    output, error = run_adb_task(command)
    if len(output.strip().split(os.linesep)) == 1:
        split_pattern = re.compile(r"\s+")
        return split_pattern.split(output)[1]
    else:
        raise Error("get app pid fail")


def get_app_pid():
    command = "adb shell ps | grep %s" % pkg_name
    output, error = run_adb_task(command)
    if len(output.strip().split(os.linesep)) == 1:
        split_pattern = re.compile(r"\s+")
        return split_pattern.split(output)[1]
    else:
        raise Error("get app pid fail")


def root_device():
    command = "adb root"
    output, error = run_adb_task(command)
    if "adbd is already running as root" in output:
        log("root success!")
    else:
        raise Error(output)


def remount_device():
    command = "adb remount"
    output, error = run_adb_task(command)
    if "remount succeeded" in output:
        log("remount success!")
    else:
        raise BaseException(output)


def reboot_device():
    command = "adb reboot"
    run_adb_task(command)


def is_screen_on():
    command = 'adb shell dumpsys power | egrep "Display Power"'
    output, error = run_adb_task(command)
    screen_state = re.split(r'[s|=]', output)[-1]
    if screen_state == 'ON\n':
        return True
    elif screen_state == 'OFF\n':
        return False
    raise Error("get screen state error!")


def turn_screen(on):
    if not isinstance(on, bool):
        raise Error("turn screen argument invalid!")
    if is_screen_on() ^ on:
        wakeup = 'adb shell input keyevent POWER'
        subprocess.Popen(wakeup.split())


def open_screen_lock():
    pass


def get_camera_state():
    result = 0
    command = 'adb shell am stack list | grep "taskId=[0-9]\{0,9\}: %s"' % pkg_name
    output, error = run_adb_task(command)
    if output:
        result = CAMERA_STATE_OPENED
        m = re.compile(r'visible=(true|false)').search(output)
        if m and len(m.group()) > 8 and m.group()[8:] == "true":
            result |= CAMERA_STATE_VISIBLE
    return result


def close_camera_force():
    if get_camera_state() & CAMERA_STATE_OPENED == CAMERA_STATE_OPENED:
        command = "adb shell am force-stop %s" % pkg_name
        run_adb_task(command)
    else:
        print("%s is already closed.")


def put_camera_to_background():
    if is_screen_on():
        camera_state = get_camera_state()
        if camera_state & CAMERA_STATE_OPENED == CAMERA_STATE_OPENED \
                and camera_state & CAMERA_STATE_VISIBLE == CAMERA_STATE_VISIBLE:
            command = "adb shell input keyevent 3"  # 3 -->  "KEYCODE_HOME"
            run_adb_task(command)
        else:
            print("%s is closed.please open it." % pkg_name)
    else:
        print("screen is off")


def open_camera_cold():
    if not is_screen_on():
        turn_screen(True)
    camera_state = get_camera_state()
    if camera_state & CAMERA_STATE_OPENED == CAMERA_STATE_OPENED:
        close_camera_force()

    command = "adb shell am start -a android.intent.action.MAIN -c android.intent.category.LAUNCHER -n " \
              "%s/%s.activity.CameraActivity" % (pkg_name, pkg_name)
    run_adb_task(command)


def open_camera_warm():
    if is_screen_on():
        camera_state = get_camera_state()
        if camera_state & CAMERA_STATE_OPENED == CAMERA_STATE_OPENED:
            command = "adb shell am start -a android.intent.action.MAIN -c android.intent.category.LAUNCHER -n " \
                      "%s/%s.activity.CameraActivity" % (pkg_name, pkg_name)
            run_adb_task(command)
        else:
            print("%s is closed. please open it and put it to background." % pkg_name)
    else:
        print("screen is off")


def take_picture(count=1, delay=1000):
    if is_screen_on():
        log("take_picture %s" % count)
        camera_state = get_camera_state()
        if camera_state & CAMERA_STATE_OPENED == CAMERA_STATE_OPENED \
                and camera_state & CAMERA_STATE_VISIBLE == CAMERA_STATE_VISIBLE:
            for i in xrange(count):
                command = "adb shell input keyevent 24"  # 24 -->  "KEYCODE_VOLUME_UP"
                run_adb_task(command)
                time.sleep(delay / 1000)
        else:
            print("%s is closed.please open it." % pkg_name)
    else:
        print("screen is off")


def start_recording():
    pass


def burst(count):
    """
    burst {count} captures
    """
    pass


def switch_pv_camera():
    """
    switch photo/video camera
    """
    pass


def switch_bf_camera():
    """
    switch front/back camera
    """
    pass


def init_logcat(app_pid, hal_app, app_log, hal_log):
    clear_command = "adb logcat -c"
    app_command = "adb logcat --pid=%s" % app_pid
    hal_command = "adb logcat --pid=%s" % hal_app
    log(app_command)
    log(hal_command)
    os.system(clear_command)
    app_proc = subprocess.Popen(app_command.split(), stdout=app_log)
    hal_proc = subprocess.Popen(hal_command.split(), stdout=hal_log)
    return app_proc, hal_proc


LOG_TYPE_APP = 0
LOG_TYPE_HAL = 1


def get_result_file(type):
    cur_time = time.strftime('%Y_%m_%d_%H_%M_%S', time.localtime(time.time()))
    home_path = os.environ['HOME']
    log_path = ".KpiLog"
    if type == LOG_TYPE_APP:
        log_name = "app_log_%s.log" % cur_time
    elif type == LOG_TYPE_HAL:
        log_name = "hal_log_%s.log" % cur_time
    else:
        log_name = "temp.log"
    full_path = os.path.join(home_path, log_path)
    if not os.path.exists(full_path):
        os.makedirs(full_path)
    return os.path.join(full_path, log_name)


class Device:
    def __init__(self):
        try:
            if get_device_id():
                self.platform = get_platform()
                self.system_version = get_system_custom_build_version()
                self.sdk_version = get_sdk_version()
                self.app_version = get_app_version()
                open_camera_cold()
                self.app_pid = get_app_pid()
                self.hal_pid = get_hal_pid(self.sdk_version)
                log(self.__str__())
        except Error, e:
            print(e.message)

    def decode(self, msg):
        msg_data = json.loads(msg)
        self.platform = msg_data["platform"]
        self.system_version = msg_data["system_version"]
        self.sdk_version = msg_data["sdk_version"]
        self.app_version = msg_data["app_version"]
        self.app_pid = msg_data["app_pid"]
        self.hal_pid = msg_data["hal_pid"]
        log(self.__str__())

    def __str__(self):
        return '{"platform":"%s","system_version":"%s","sdk_version":"%s","app_version":"%s","app_pid":"%s",' \
               '"hal_pid":"%s"}' % (self.platform, self.system_version, self.sdk_version, self.app_version,
                                    self.app_pid, self.hal_pid)

    def auto_test(self, number=10):
        app_log = get_result_file(LOG_TYPE_APP)
        hal_log = get_result_file(LOG_TYPE_HAL)
        app_file = open(app_log, 'w')
        hal_file = open(hal_log, 'w')
        p1, p2 = init_logcat(self.app_pid, self.hal_pid, app_file, hal_file)
        for i in xrange(int(number)):
            log(i)
            # test camera cold warm
            put_camera_to_background()
            time.sleep(5)
            open_camera_warm()
            # test take picture
            time.sleep(5)
            take_picture(3, 5000)
        p1.kill()
        p2.kill()
        app_file.close()
        hal_file.close()
        return app_log, hal_log


class __UnitTest(unittest.TestCase):
    """
    Run a suite of unit tests on this module.
    """

    # def test_get_device_id(self):
    #     device_id = get_device_id()
    #     print("device_id : " + device_id)
    #
    # def test_root_remount_device(self):
    #     root_device()
    #     remount_device()
    #
    # def test_turn_on_screen(self):
    #     turn_screen(True)
    #
    # def test_turn_off_screen(self):
    #     turn_screen(False)
    #
    # def test_get_camera_state(self):
    #     print(get_camera_state())
    #
    # def test_close_camera(self):
    #     close_camera_force()
    #
    # def test_input_home(self):
    #     put_camera_to_background()
    #
    # def test_open_camera_cold(self):
    #     open_camera_cold()

    # def test_open_camera_warm(self):
    #     open_camera_warm()

    # def test_take_picture(self):
    #     take_picture(10)

    def test_get_app_version(self):
        log(get_hal_pid(get_sdk_version()))


if __name__ == "__main__":
    unittest.main()

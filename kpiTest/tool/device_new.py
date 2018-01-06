import re
import subprocess

import os

from error import Error


def _run_task(cmd):
    return subprocess.Popen(cmd.split(), stdout=subprocess.PIPE).communicate()


def _call_task(cmd):
    return os.system(cmd)


class Devices2:

    def __init__(self):
        self.device_id = None
        self.propertys = {}

        # Check if device id is set in env
        if "ANDROID_SERIAL" in os.environ:
            self.device_id = os.environ["ANDROID_SERIAL"]
        devices = []
        command = "adb devices"
        output, error = _run_task(command)
        for line in output.split(os.linesep):
            device_info = line.split()
            if len(device_info) == 2 and device_info[1] == "device":
                devices.append(device_info[0])

        if len(devices) == 0:
            raise Error("No device is connected!")
        elif self.device_id is not None and self.device_id not in devices:
            raise Error(self.device_id + " is not connected!")
        elif self.device_id is None and len(devices) >= 2:
            raise Error("More than 1 device are connected. " +
                        "Use device=<device_id> to specify a device to test.")
        elif len(devices) == 1:
            self.device_id = devices[0]

        if self.device_id:
            output, error = self.shell("getprop")
            pattern = re.compile(r"\[[\S\s]+]")
            for line in output.split(os.linesep):
                split_index = line.find(":")
                key_match = pattern.search(line[:split_index].strip())
                val_match = pattern.search(line[split_index + 1:].strip())
                if key_match and val_match:
                    key = key_match.group()[1:-1]
                    val = val_match.group()[1:-1]
                    self.propertys[key] = val

    def reboot(self):
        self.shell("reboot")

    def wake(self):
        pass

    def get_property(self, key, default):
        if self.propertys:
            val = self.propertys[key]
            if val:
                return val
        return default

    def get_system_property(self, key, default):
        if self.propertys:
            val = self.propertys[key]
            if val:
                return val
        return default

    def install_package(self, path):
        self.shell("install %s" % path)

    def remove_package(self, package):
        self.shell("uninstall %s" % package)

    def start_activity(self, package, activity, **kwargs):
        cmd = "am start %s -n %s/%s.%s" % ("%s", package, package, activity)
        key_action = "action"
        key_category = "category"
        if kwargs:
            if key_action in kwargs.keys():
                cmd = cmd % ("-a %s %s" % (kwargs.get(key_action), "%s"))
            if key_category in kwargs.keys():
                cmd = cmd % ("-c %s %s" % (kwargs.get(key_category), "%s"))
        cmd = cmd % ""
        print("start_activity : %s" % cmd)
        self.shell(cmd)

    def broadcast_intent(self, package, activity, **kwargs):
        cmd = "am broadcast %s %s/%s.%s" % ("%s", package, package, activity)
        key_action = "action"
        key_category = "category"
        if kwargs:
            if key_action in kwargs.keys():
                cmd = cmd % "-a %s %s" % kwargs.get(key_action)
            if key_category in kwargs.keys():
                cmd = cmd % "-c %s %s" % kwargs.get(key_category)
        cmd = cmd % ""
        print("start_activity : %s" % cmd)
        self.shell(cmd)

    def drag(self, start, end, duration, steps):
        pass

    def press(self, name, mtype):
        pass

    def touch(self, x, y, mtype):
        pass

    def shell(self, cmd):
        if not self.device_id:
            raise Error("can't call shell,device id is None!")
        command = "adb -s %s shell %s" % (self.device_id, cmd)
        output, error = _run_task(command)
        return output, error

    def call_adb(self, cmd):
        command = "adb -s %s %s" % (self.device_id, cmd)
        output, error = _run_task(command)
        return output, error


if __name__ == "__main__":
    pkg = "com.myos.camera"
    dev = Devices2()
    dev.start_activity(pkg, "activity.CameraActivity", action="android.myos.action.PANORAMACAMERA")

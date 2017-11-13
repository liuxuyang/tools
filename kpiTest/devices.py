import os
import subprocess
from util import log
import sys


def prepare_device():
    """
    root & remount device
    :return:
    """
    cmd = "adb root && adb remount"


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
    log(command.split())
    proc = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output, error = proc.communicate()
    for line in output.split(os.linesep):
        device_info = line.split()
        if len(device_info) == 2 and device_info[1] == "device":
            devices.append(device_info[0])

    if len(devices) == 0:
        raise log("No device is connected!")
    elif device_id is not None and device_id not in devices:
        raise log(device_id + " is not connected!")
    elif device_id is None and len(devices) >= 2:
        raise log("More than 1 device are connected. " +
                  "Use device=<device_id> to specify a device to test.")
    elif len(devices) == 1:
        device_id = devices[0]

    return device_id

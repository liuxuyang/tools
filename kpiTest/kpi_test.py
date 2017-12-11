import time

import os

from data.app_log import app_log_test
from tool.devices import Device
from tool.util import log
import sys
from data.log_interpreter import LogInterpreter
from tool.target import Excel

__version__ = "1.0.0"


def main():
    """
        These are common kpi_test commands used in various situations.
        Options include:
        -v,--version   : Prints the program version info.
        -h,--help      : Display this help
        --update    : Update this program
        -a,--analyze <log_path> [<result_path>] : Analyze the specified log and save the result.
        -t,--test [<number>] [<result_path>]: Auto test a specified number of times.
    """
    if len(sys.argv) <= 1:
        exit_with_msg(1)
    option = sys.argv[1]
    if option.startswith("--") or option.startswith("-"):
        if option in ["-h", "--help"]:
            output_help()
        elif option in ["-v", "--version"]:
            output_version()
        elif option == "--update":
            update()
        elif option in ["-t", "--test"]:
            test_number = None
            save_path = None
            if len(sys.argv) >= 4:
                save_path = sys.argv[3]
            if len(sys.argv) >= 3:
                test_number = sys.argv[2]
            auto_test(test_number, save_path)
        else:
            print("Invalid arguments")
    else:
        print("Invalid arguments")


def output_version():
    print(__version__)
    exit_with_msg(0)


def output_help():
    print(main.__doc__)
    exit_with_msg(0)


def update():
    log("update is not supported yet.")
    exit_with_msg(0)


def exit_with_msg(index):
    # print(get_exit_msg(index))
    sys.exit(index)


def get_exit_msg(index):
    pass


def test():
    app_log_test()


def auto_test(number, save_path):
    # device = Device()
    # app_log, hal_log = device.auto_test(number)
    # log(app_log)
    # log(hal_log)
    # interpreter = LogInterpreter(device)
    # interpreter.read_log(app_log)
    # interpreter.read_log(hal_log)
    # interpreter.analysis_hal_log()
    # interpreter.analysis_app_log()
    #
    # xlsx = Excel()
    # if save_path:
    #     xlsx.open(save_path)
    # else:
    #     xlsx.open()
    # cur_time = time.strftime('%Y_%m_%d_%H_%M_%S', time.localtime(time.time()))
    # xlsx.write_data(data=interpreter.get_result(), title=cur_time, device=device)
    # xlsx.close()

    device_msg = '{"platform":"qcom","system_version":"UFEEL-Daily_V01.15_2.ORG.10-[Oreo-8.0]-C800AE",' \
                 '"sdk_version":"26","app_version":"8.0.50.05","app_pid":"9328","hal_pid":"494"} '
    device = Device()
    device.decode(device_msg)
    app_log = "/home/liuxuyang/.KpiLog/app_log_2017_12_01_18_20_38.log"
    hal_log = "/home/liuxuyang/.KpiLog/hal_log_2017_12_01_18_20_38.log"
    interpreter = LogInterpreter(device)
    interpreter.read_log(app_log)
    interpreter.read_log(hal_log)
    interpreter.analysis_app_log()
    interpreter.analysis_hal_log()
    xlsx = Excel()
    if save_path:
        xlsx.open(save_path)
    else:
        xlsx.open()
    cur_time = time.strftime('%Y_%m_%d_%H_%M_%S', time.localtime(time.time()))
    xlsx.write_data(data=interpreter.get_result(), title=cur_time, device=device)
    xlsx.close()


if __name__ == "__main__":
    main()
    #test()

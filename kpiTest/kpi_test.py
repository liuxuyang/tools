import time

from tool.devices import Device
from tool.util import log, generate_result_file_path, check_int
import sys
from data.log_interpreter import LogInterpreter
from tool.target import Excel

__version__ = "1.0.2"


def main():
    """
        These are common kpi_test commands used in various situations.

        log will cache in [home_path]/Kpi/log/
        result will cache in [home_path]/Kpi/result/

        Options include:

        -v,--version   : Prints the program version info.

        -h,--help      : Display this help

        --update    : Update this program

        -a,--analyze <log_path> <TYPE> [<result_path>] : Analyze the specified log and save the result.
            TYPE:
                app : this is a app log
                hal : this is a hal log

        -t,--test <OPTION> [<number>] [<result_path>]: Auto test a specified number of times.
            OPTION:
                c:test capture
                o:open and close camera
                s:switch camera

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
        elif option in ["-a", "--analyze"]:
            filename = "temp"
            if len(sys.argv) >= 5:
                filename = sys.argv[4]
            if len(sys.argv) >= 4:
                log_type = sys.argv[3]
            else:
                print("Invalid arguments")
                return
            log_path = sys.argv[2]
            analyze_log(log_path, log_type, filename)
        elif option in ["-t", "--test"]:
            test_number = 10
            filename = "temp"
            if len(sys.argv) >= 5:
                test_number = sys.argv[3]
                filename = sys.argv[4]
            elif len(sys.argv) >= 4:
                if sys.argv[3].isdigit():
                    test_number = sys.argv[3]
                else:
                    filename = sys.argv[3]
            else:
                print("Invalid arguments")
                return
            test_option = sys.argv[2]
            test_number = check_int(test_number)
            if "c" == test_option:
                test_capture(filename)
            elif "o" == test_option:
                test_open_close(test_number, filename)
            elif "s" == test_option:
                test_switch_camera(test_number, filename)
            else:
                auto_test(test_number, filename)
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


def analyze_log(log_path, log_type, filename):
    pass


def write_data(interpreter, save_path, device):
    xlsx = Excel()
    if save_path:
        xlsx.open(save_path)
    else:
        xlsx.open()
    cur_time = time.strftime('%Y_%m_%d_%H_%M_%S', time.localtime(time.time()))
    xlsx.write_data(data=interpreter.get_result(), title=cur_time, device=device)
    xlsx.close()


def test_capture(filename):
    save_path = generate_result_file_path(filename)
    log("test capture and save to %s" % save_path)

    device = Device()
    interpreter = LogInterpreter(device)

    app_log_path, hal_log_path = device.test_capture()
    print("app log : %s" % app_log_path)
    print("hal log : %s" % hal_log_path)

    interpreter.read_log(app_log_path)
    interpreter.analysis_app_log()

    interpreter.read_log(hal_log_path)
    interpreter.analysis_hal_log()

    write_data(interpreter, save_path, device)


def test_open_close(test_number, filename):
    save_path = generate_result_file_path(filename)
    log("test open&close camera and save to %s" % save_path)
    device = Device()
    interpreter = LogInterpreter(device)

    log_path = device.test_open_close(test_number)
    print("log : %s" % log_path)
    if log_path:
        interpreter.read_log(log_path)
        interpreter.analysis_app_log()

        write_data(interpreter, save_path, device)


def test_switch_camera(test_number, filename):
    save_path = generate_result_file_path(filename)
    log("test switch camera and save to %s" % save_path)
    device = Device()
    interpreter = LogInterpreter(device)

    log_path = device.test_switch_camera(test_number)
    print("log : %s" % log_path)

    interpreter.read_log(log_path)
    interpreter.analysis_app_log()

    write_data(interpreter, save_path, device)


def auto_test(number, filename):
    save_path = generate_result_file_path(filename)
    log("auto test %s and save to %s" % (number, save_path))
    device = Device()
    app_log, hal_log = device.auto_test(number)
    log(app_log)
    log(hal_log)
    interpreter = LogInterpreter(device)
    interpreter.read_log(app_log)
    interpreter.read_log(hal_log)
    interpreter.analysis_hal_log()
    interpreter.analysis_app_log()

    write_data(interpreter, save_path, device)


if __name__ == "__main__":
    main()

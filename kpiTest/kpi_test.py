from util import log
import sys
from data.log_interpreter import LogInterpreter
from target import Excel

__version__ = "1.0.0"


def main():
    """
        These are common kpi_test commands used in various situations.
        Options include:
        -v,--version   : Prints the program version info.
        -h,--help      : Display this help
        --update    : Update this program
        -a,--analyze <log_path> [<result_path>] : analyze the specified log and save the result.
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
        elif option in ["-a", "analyze"]:
            log_path = None
            save_path = None
            if len(sys.argv) >= 4:
                save_path = sys.argv[3]
            if len(sys.argv) >= 3:
                log_path = sys.argv[2]
            analyze(log_path, save_path)
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


def analyze(log_path, save_path):
    try:
        if log_path:
            log_data = LogInterpreter()
            log_data.read_log(log_path)
            log_data.analysis_hal_log()

            xlsx = Excel()
            if save_path:
                xlsx.open(save_path)
            else:
                xlsx.open()
            xlsx.write_data(data=log_data.get_result(), title="test")
            xlsx.close()
        else:
            log("log path is invalid!")
    except Exception(), e:
        log(e)


if __name__ == "__main__":
    main()

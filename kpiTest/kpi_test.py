from util import log
import sys
from data.log_interpreter import LogInterpreter
from target import Excel


def main():
    log_path = None
    save_path = None

    if len(sys.argv) > 1:
        log_path = sys.argv[1]
    if len(sys.argv) > 2:
        save_path = sys.argv[2]
    if log_path:
        log_data = LogInterpreter()
        log_data.read_log(log_path)
        log_data.analysis_hal_log()
        log(log_data.get_result())

        xlsx = Excel()
        if save_path:
            xlsx.open(save_path)
        else:
            xlsx.open()
        xlsx.write_data(data=log_data.get_result(), title="test")
        xlsx.close()
    else:
        log("log path is invalid!")


if __name__ == "__main__":
    main()

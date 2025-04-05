from throughput_log_analyzer.consts import RESULTS, MODE, TEST_NAME, PING_PACKET_SIZES, TYPES_OF_LOGS, PATH_TO_LOGS_RESULTS
from throughput_log_analyzer.log_analyzer import LogAnalyzer
from throughput_log_analyzer.utils import organize_file_structure


def main():
    log_file_structure = organize_file_structure(RESULTS, MODE, TEST_NAME, PING_PACKET_SIZES, TYPES_OF_LOGS, PATH_TO_LOGS_RESULTS)
    print(log_file_structure)
    log_analyzer = LogAnalyzer(log_file_structure=log_file_structure)
    log_analyzer.run()


if __name__ == "__main__":
    main()

from log_analyzer.consts import RESULTS, BASE_STATION, TEST_NAME, SIDE, PING_PACKET_SIZES, TYPES_OF_LOGS, LOGS
from log_analyzer.log_analyzer import LogAnalyzer
from log_analyzer.utils import organize_file_structure


def main():
    log_file_structure = organize_file_structure(RESULTS, BASE_STATION, TEST_NAME, LOGS, SIDE, PING_PACKET_SIZES,TYPES_OF_LOGS)
    print(log_file_structure)
    log_analyzer = LogAnalyzer(log_file_structure=log_file_structure)
    log_analyzer.run()


if __name__ == "__main__":
    main()

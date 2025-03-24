from scripts.log_analyzer.consts import RESULTS, BASE_STATION, TEST_NAME, SIDE, PING_PACKET_SIZES, TYPES_OF_LOGS, LOGS
from scripts.log_analyzer.log_analyzer import LogAnalyzer
from scripts.log_analyzer.log_structure_format import LOG_FILE_STRUCTURE_INITIAL_CUT, \
    LOG_FILE_STRUCTURE_INITIAL_CUT_COMPLEMENT, LOG_FILE_STRUCTURE_FULL, LOG_FILE_STRUCTURE_REPEAT_FULL, \
    LOG_FILE_STRUCTURE_INITIAL_CUT_TEST_RX_GAIN_50, LOG_FILE_STRUCTURE_FULL_TEST_RX_GAIN_50
from scripts.log_analyzer.utils import organize_file_structure


def main():
    log_file_structure = organize_file_structure(RESULTS, BASE_STATION, TEST_NAME, LOGS, SIDE, PING_PACKET_SIZES,TYPES_OF_LOGS)
    print(log_file_structure)
    log_analyzer = LogAnalyzer(log_file_structure=log_file_structure)
    log_analyzer.run()


if __name__ == "__main__":
    main()

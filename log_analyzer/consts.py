RESULTS = 'results'
MODE = "ping_only" # also "throughput_only" or "ping_and_throughput"
TEST_NAME = "20250404-071509_first_full"
# LOGS = 'logs'
# SIDE = ["client", "server"]
PING_PACKET_SIZES = ["56B"]
TYPES_OF_LOGS = ["ping_logs"] # pcaps also?

PATH_TO_LOGS_RESULTS = ["..", RESULTS, MODE, TEST_NAME]

BOXPLOT_FOLDER_NAME = "../analysis/boxplots/20250404-071509_first_full"
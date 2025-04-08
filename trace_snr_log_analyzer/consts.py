RESULTS = 'results_trace'
MODE = "ping_only"
TEST_NAME = "20250404-071509_ping_only_full_test"
# LOGS = 'logs'
# SIDE = ["client", "server"]
PING_PACKET_SIZES = ["56B"]
TYPES_OF_LOGS = ["rep_1", "rep_2", "rep_3", "rep_4", "rep_5", "rep_6", "rep_7", "rep_8", "rep_9", "rep_10", "rep_11", "rep_12", "rep_13", "rep_14", "rep_15", "rep_16", "rep_17", "rep_18", "rep_19", "rep_20", "rep_21", "rep_22", "rep_23", "rep_24", "rep_25", "rep_26", "rep_27", "rep_28", "rep_29", "rep_30"]

PATH_TO_LOGS_RESULTS = ["..", RESULTS, MODE, TEST_NAME]

BOXPLOT_FOLDER_NAME = f"../analysis/boxplots/{MODE}/trace_snr_{TEST_NAME}"
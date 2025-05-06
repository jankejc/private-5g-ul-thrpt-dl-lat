RESULTS = 'results'
MODE = "ping_thrpt"
STAGE = "Stage II"
TEST_NAME = "second_try_second_stage_less_demanding"
# LOGS = 'logs'
# SIDE = ["client", "server"]
PING_PACKET_SIZES = ["16B", "512B", "1436B"]
# PING_PACKET_SIZES = ["56B"]
TYPES_OF_LOGS = ["ping_logs"]

PATH_TO_LOGS_RESULTS = ["..", RESULTS, MODE, TEST_NAME]

BOXPLOT_FOLDER_NAME = f"../analysis/{STAGE}/{MODE}/{TEST_NAME}/ping/boxplots"
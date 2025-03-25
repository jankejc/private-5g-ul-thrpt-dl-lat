The consts file has in it parts of the folder structure contating logs.
Change varaiables there for parametrizing tests

This repository contains a set of Python scripts that work together to analyze log files and visualize the results in the form of boxplots. The main script log_analyzer.py processes logs, extracts relevant data (such as RTT values), and generates graphical representations (boxplots) for analysis. The utility functions help with folder structure parsing and error messaging.
Files

    log_analyzer.py

        This file contains the core LogAnalyzer class that handles the processing of log files and the generation of graphs (boxplots).

    utils.py

        Contains utility functions for parsing the folder structure of the log files and displaying messages with color formatting.

    consts.py

        Stores constant values like folder names, log structure details, and default configurations for the analysis.

    main.py

        The entry point of the script. It initializes the log file structure and runs the LogAnalyzer to perform the analysis.

Requirements

    Python 3.x

    Dependencies:

        matplotlib: For generating boxplots.

        colorama: For colored terminal output.

To install dependencies, run:

pip install -r requirements.txt

Usage

    Folder Structure

    The organize_file_structure function will organize the log files from a directory structure, and LogAnalyzer will use this organized structure to parse log files, extract the necessary data, and generate the plots.

    Running the Script

    To run the analysis, simply execute the main.py file.

    python main.py

    This will:

        Parse the folder structure for log files.

        Extract relevant data such as RTT values from ping logs.

        Generate and save boxplots for various test configurations (e.g., different attenuations and bandwidths).

    Configuration

    In the consts.py file, you can customize the following parameters:

        RESULTS: The directory containing the test results.

        BASE_STATION: The base station used in the tests.

        TEST_NAME: The name of the test.

        LOGS: The folder containing the log files.

        SIDE: The test sides (client or server).

        PING_PACKET_SIZES: The sizes of the ping packets used in the tests.

        TYPES_OF_LOGS: Types of logs to process (e.g., iperf_logs, ping_logs).

        BOXPLOT_FOLDER_NAME: The folder name where the boxplot images will be saved.

    Generated Output

        The script generates boxplots for each configuration and saves them in the results/testing_boxplots_script_2 directory.

        The plots visualize the Round-Trip Time (RTT) distributions for different configurations, packet sizes, attenuations, and bandwidths.

Code Breakdown
LogAnalyzer Class

The main class for log analysis, which includes several methods:

    setup(): Initializes the configuration and prepares necessary folders.

    extract_avg_rtt(ping_log): Extracts the average RTT from a ping log.

    parse_folder_structure(): Traverses the folder structure recursively and processes log files.

    plot_boxplots_for_tests(): Generates boxplots for RTT values.

    calculate_mean_value(): Calculates the mean of RTT values.

utils.py

    parse_folder_structure(directory): Recursively parses the folder structure under the given directory and ensures no duplicates.

    organize_file_structure(...): Organizes the parsed folder structure into a format suitable for LogAnalyzer.

    print_success(message): Prints a success message in green.

    print_error(message): Prints an error message in red.

main.py

    The entry point where the file structure is organized and the LogAnalyzer class is run.

consts.py

    Contains static configurations used across the script such as RESULTS, BASE_STATION, TEST_NAME, SIDE, PING_PACKET_SIZES, and TYPES_OF_LOGS.

Example Folder Structure

The folder structure for the logs should look something like this:

results/
└── amarisoft_classic/
    └── full_tests_rx_gain_50/
        └── logs/
            └── config_1/
                └── attenuation_10/
                    └── bandwidth_100M/
                        └── client/
                        └── server/
                            └── ping_log_16.log
                            └── ping_log_512.log
                            └── ping_log_1436.log

The script will parse through the folder structure, find relevant log files, and generate the necessary analysis based on the configuration and data found.
Notes

    Ensure that the folder structure and log files follow the expected naming convention for the analysis to work correctly.

    The boxplots will be saved in the folder defined by BOXPLOT_FOLDER_NAME in consts.py.

    Error and success messages are printed in color in the terminal using the colorama library..
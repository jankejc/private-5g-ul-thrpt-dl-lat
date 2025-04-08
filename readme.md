```SCRIPT```
In script there is run test script that saves data in `test_run` directory on lenovo.
The script is run at lenovo. This data are then download here to results, but no throughput only - these are too big.
Trace results are saved on amarisoft `.../websockets/test....` then downloaded here to `trace_results`. 

```LOG_ANALYZER```
Analyzer for ping only results. Is saves boxplots and csv stats in `analysis` directory.

```THROUGHPUT_LOG_ANALYZER```
Analyzer for throughput only results. Is saves raw csv stats in where you want - it is run where lidar pcaps are.
These csv has multiple rows instead of avg... These csv we download manually here to analysis `throughput only`.
If the run was split we need to merge these csv and use `plot_throughput_only_stats.py` to get good `aggregated_boxplot_stats.csv`
and boxplots.

```TRACE_LOG_ANALYZER```
Analyzer for traces from Amarisoft - TODO

```SIDE_SCRIPTS```
Directory with useful scripts.
Important:
 - `plot_throughput_only_stats.py` makes csv and boxplots from "throughput only results raw csv"
 - `rtt_tp_plt.py` makes graph rtt against throughput


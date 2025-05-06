import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.lines import Line2D
import numpy as np

# ===== CONFIG NAME MAPPING FUNCTION =====
def config_name_mapping():
    return {
        "pb-178-tdd-low-latency-rx-to-tx-lat-1.cfg": "LL: Rx to Tx Latency = 1",
        "pb-178-tdd-low-latency-rx-to-tx-lat-2.cfg": "LL: Rx to Tx Latency = 2",
        "pb-178-tdd-low-latency.cfg": "Low Latency (LL)",
        "pb-178-ul-highTp-defCSI-sr-per-1.cfg": "DefCSI: SR Period = 1",
        "pb-178-ul-highTp-defCSI-prach-128.cfg": "DefCSI: PRACH = 1",
        "pb-178-ul-highTp-autoCSI-TRSonSSB-rx-to-tx-lat-2.cfg": "AutoCSI: Rx to Tx = 2",
        "pb-178-tdd-low-latency-rx-to-tx-lat-4.cfg": "LL: Rx to Tx = 4",
        "pb-178-tdd-low-latency-sr-per-1.cfg": "LL: SR Period = 1",
        "pb-178-ul-highTp-defCSI-no-trs.cfg": "DefCSI: No TRS",
        "pb-178-tdd-low-latency-prach-160.cfg": "LL: PRACH = 160",
        "pb-178-ul-highTp-autoCSI-noTRS-prach-128.cfg": "AutoCSI: No TRS, PRACH = 128",
        "pb-178-ul-highTp-autoCSI-noTRS.cfg": "AutoCSI: No TRS",
        "pb-178-ul-highTp-autoCSI-TRSonSSB-20.cfg": "AutoCsiTRSonSSB: Bandwidth = 20 MHz",
        "pb-178-ul-highTp-autoCSI-TRSonSSB-prach-128.cfg": "AutoCsiTRSonSSB: PRACH = 128",
        "pb-178-tdd-low-latency-no-rx-to-tx-lat.cfg": "LL: No Rx to Tx Latency",
        "pb-178-ul-highTp-autoCSI-TRSonSSB-sr-per-1.cfg": "AutoCsiTRSonSSB: SR Period = 1",
        "pb-178-ul-highTp-autoCSI-noTRS-sr-per-1.cfg": "AutoCSI: No TRS, SR Period = 1",
        "pb-178-ul-highTp-autoCSI-TRSonSSB.cfg": "AutoCsiTRSonSSB",
        "pb-178-ul-highTp-defCSI-rx-to-tx-lat-4.cfg": "DefCSI: Rx to TX Latency = 4",
        "pb-178-ul-highTp-autoCSI-TRSonSSB-sr-per-1-uss.cfg": "AutoCsiTRSonSSB: SR Period = 1, USS",
        "pb-178-tdd-low-latency-20.cfg": "LL: Bandwidth = 20 MHz",
        "pb-178-ul-highTp-defCSI-rx-to-tx-lat-2.cfg": "DefCSI: Rx to Tx Latency = 2",
        "pb-178-ul-highTp-defCSI-20.cfg": "DefCSI: Bandwidth = 20 MHz",
        "pb-178-ul-highTp-autoCSI-noTRS-20.cfg": "AutoCSI: No TRS, Bandwidth = 20 MHz",
        "pb-178-ul-highTp-defCSI.cfg": "DefCSI"
    }

# ===== LOAD DATA =====
throughput_df = pd.read_csv(
    '../analysis/Stage II/ping_thrpt/second_try_second_stage_less_demanding/graphs/averaged_throughput_by_configuration.csv')
rtt_df = pd.read_csv('../analysis/Stage II/ping_thrpt/second_try_second_stage_less_demanding/graphs/ping_raw_stats.csv')

mapping = config_name_mapping()
throughput_df['configuration'] = throughput_df['configuration'].map(mapping).fillna(throughput_df['configuration'])
rtt_df['configuration'] = rtt_df['configuration'].map(mapping).fillna(rtt_df['configuration'])

throughput_df['attenuation (dB)'] = pd.to_numeric(throughput_df['attenuation (dB)'], errors='coerce')
rtt_df['attenuation (dB)'] = pd.to_numeric(rtt_df['attenuation (dB)'], errors='coerce')

# ===== AGGREGATE DATA =====
tp_avg = throughput_df.groupby(['configuration', 'attenuation (dB)'])[['mean (Mibps)', 'std (Mibps)']].mean().reset_index()
tp_avg.columns = ['configuration', 'attenuation (dB)', 'avg_throughput', 'std_throughput']

rtt_avg = rtt_df.groupby(['configuration', 'attenuation (dB)'])[['mean (ms)', 'std (ms)']].mean().reset_index()
rtt_avg.columns = ['configuration', 'attenuation (dB)', 'avg_rtt', 'std_rtt']

merged_df = pd.merge(tp_avg, rtt_avg, on=['configuration', 'attenuation (dB)'])
# ===== EXPORT CSV (all data, even high RTTs) =====
merged_df.to_csv("export_throughput_rtt_with_stds.csv", index=False)

# ===== FILTER FOR PLOTTING ONLY =====
plot_df = merged_df[merged_df['avg_rtt'] <= 700].copy()

# ===== CONFIG COLORS AND ATTENUATION MARKERS =====
unique_configs = merged_df['configuration'].unique()
config_color_map = dict(zip(unique_configs, sns.color_palette("Paired", len(unique_configs))))
attenuations = sorted(merged_df['attenuation (dB)'].unique())
markers = ['o', 's', '^', 'D', 'v', 'P', 'X', '*']
attn_marker_map = dict(zip(attenuations, markers))

# ===== PLOT =====
fig, ax = plt.subplots(figsize=(16, 12))
np.random.seed(42)

for _, row in plot_df.iterrows():
    config = row['configuration']
    attn = row['attenuation (dB)']
    color = config_color_map[config]
    marker = attn_marker_map[attn]
    x = row['avg_throughput'] + np.random.normal(0, 0.1)
    y = row['avg_rtt'] + np.random.normal(0, 0.1)
    ax.scatter(x, y, color=color, marker=marker, edgecolor='black', linewidth=1, s=300)

# ===== LEGENDS =====
attn_legend_handles = [
    Line2D([], [], marker=attn_marker_map[attn], color='k', label=f"{attn} dB",
           markerfacecolor='k', markersize=14, linestyle='None')
    for attn in attenuations
]

config_legend_handles = [
    Line2D([], [], marker='o', color='w', label=name,
           markerfacecolor=color, markeredgecolor='black', markersize=14)
    for name, color in config_color_map.items()
]

# Combine legends in one block at bottom
all_handles = attn_legend_handles + config_legend_handles
all_labels = [h.get_label() for h in all_handles]
ax.legend(all_handles, all_labels,
          title="Legend",
          loc='upper center', bbox_to_anchor=(0.5, -0.1),
          ncol=3, fontsize=17, title_fontsize=17, frameon=False)

# ===== LABELS =====
ax.set_xlabel("Average Throughput [Mibps]", fontsize=20, weight='bold')
ax.set_ylabel("Average RTT [ms]", fontsize=20, weight='bold')
ax.set_title("Throughput vs RTT by Configuration and Attenuation", fontsize=20)
ax.tick_params(axis='x', labelsize=17)
ax.tick_params(axis='y', labelsize=17)
ax.grid(True)

plt.tight_layout(rect=[0, 0, 1, 1])
plt.savefig("throughput_vs_rtt_color_and_marker.png")
plt.show()

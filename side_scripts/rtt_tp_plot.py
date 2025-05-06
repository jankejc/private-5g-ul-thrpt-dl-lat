import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from adjustText import adjust_text
from matplotlib.cm import get_cmap
from matplotlib.lines import Line2D


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


# === Main Script ===
throughput_df = pd.read_csv(
    '../analysis/Stage II/ping_thrpt/second_try_second_stage_less_demanding/graphs/averaged_throughput_by_configuration.csv')
rtt_df = pd.read_csv('../analysis/Stage II/ping_thrpt/second_try_second_stage_less_demanding/graphs/ping_raw_stats.csv')

mapping = config_name_mapping()
throughput_df['configuration'] = throughput_df['configuration'].map(mapping).fillna(throughput_df['configuration'])
rtt_df['configuration'] = rtt_df['configuration'].map(mapping).fillna(rtt_df['configuration'])

# Rename for merge clarity
throughput_df = throughput_df.rename(columns={
    'mean (Mibps)': 'avg_throughput',
    'std (Mibps)': 'std_throughput'
})
rtt_df = rtt_df.rename(columns={
    'mean (ms)': 'avg_rtt',
    'std (ms)': 'std_rtt'
})

# Merge
merged_df = pd.merge(throughput_df[['configuration', 'avg_throughput', 'std_throughput']],
                     rtt_df[['configuration', 'avg_rtt', 'std_rtt']],
                     on='configuration')

# Filter for selected configs
EXPORT_CONFIGS = [
    "AutoCsiTRSonSSB",
    "AutoCsiTRSonSSB: PRACH = 128",
    "AutoCsiTRSonSSB: SR Period = 1, USS",
    "DefCSI: No TRS, SR Period = 1",
    "LL: Rx to Tx = 4",
    "LL: SR Period = 1"
]

export_df = merged_df[merged_df['configuration'].isin(EXPORT_CONFIGS)]
export_df.to_csv("exported_config_stats.csv", index=False)
print("✅ Exported selected configurations to 'exported_config_stats.csv'.")

# === PLOT ===
fig, ax = plt.subplots(figsize=(16, 12))

config_names = merged_df['configuration'].unique()
cmap = get_cmap('tab20')
color_map = {name: cmap(i % cmap.N) for i, name in enumerate(config_names)}

configurations = {}
np.random.seed(42)

for name, row in merged_df.set_index('configuration').iterrows():
    jitter_x = row['avg_throughput'] + np.random.normal(0, 0.2)
    jitter_y = row['avg_rtt'] + np.random.normal(0, 0.2)
    configurations[name] = {'x': jitter_x, 'y': jitter_y}

texts = []
for index, (name, coords) in enumerate(configurations.items()):
    color = color_map[name]
    ax.scatter(coords['x'], coords['y'], label=f"{index+1}. {name}",
               s=300, alpha=0.8, color=color)
    texts.append(ax.text(coords['x'], coords['y'],
                         f"{index+1}", fontsize=14,
                         ha='center', va='center', color='black', weight='bold'))

adjust_text(texts, arrowprops=dict(arrowstyle='-', color='gray', lw=0.5))

ax.set_xlabel('Average Throughput [Mibps]', fontsize=22, weight='bold')
ax.set_ylabel('Average RTT [ms]', fontsize=22, weight='bold')
ax.set_title('Throughput vs RTT per Configuration', fontsize=24)
ax.tick_params(axis='x', labelsize=20)
ax.tick_params(axis='y', labelsize=20)
ax.grid(True)

# Legend below plot
handles, labels = ax.get_legend_handles_labels()
ax.legend(handles, labels,
          title="Configurations",
          loc='upper center',
          bbox_to_anchor=(0.5, -0.1),
          ncol=3,
          fontsize=14,
          title_fontsize=16,
          frameon=False)

plt.tight_layout(rect=[0, 0, 1, 1])
plt.savefig("throughput_vs_rtt_colorful_renamed.png", bbox_inches='tight')
plt.show()

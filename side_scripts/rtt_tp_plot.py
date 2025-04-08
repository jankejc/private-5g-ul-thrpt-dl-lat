import pandas as pd
import matplotlib.pyplot as plt

# Load the CSV files
throughput_df = pd.read_csv('../analysis/graphs/throughput_only_merged_stats.csv')
rtt_df = pd.read_csv('../analysis/graphs/boxplot_stats.csv')

# Compute average throughput and RTT per config
avg_throughput = throughput_df.groupby('configuration')['mean (Mibps)'].mean().reset_index()
avg_throughput.columns = ['configuration', 'avg_throughput']

avg_rtt = rtt_df.groupby('configuration')['mean (ms)'].mean().reset_index()
avg_rtt.columns = ['configuration', 'avg_rtt']

# Merge both into one DataFrame
merged_df = pd.merge(avg_throughput, avg_rtt, on='configuration')

# Plot
fig, ax = plt.subplots(figsize=(16, 10))

# Create mapping from config names to numbered points
configurations = {
    name: {'throughput': row['avg_throughput'], 'average_latency': row['avg_rtt']}
    for name, row in merged_df.set_index('configuration').iterrows()
}

for index, (name, info) in enumerate(configurations.items()):
    # Big scatter dot
    ax.scatter(info['throughput'], info['average_latency'], label=f"{index + 1}. {name}", s=100, color='tab:blue')
    # White number inside the dot
    ax.annotate(f"{index + 1}", (info['throughput'], info['average_latency']),
                textcoords="offset points", xytext=(0, -12),
                ha='center', size=10, color='black')

# Labels
ax.set_xlabel('Throughput [Mibps]', fontsize=16)
ax.set_ylabel('RTT [ms]', fontsize=16)
ax.set_title('Throughput vs RTT per Configuration', fontsize=18)
ax.grid(True)

# Legend with config names
ax.legend(title="Configurations", bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)

plt.tight_layout()
plt.show()

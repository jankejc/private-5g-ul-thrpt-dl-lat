import pandas as pd
import matplotlib.pyplot as plt
import os

csv_path = "raw_boxplot_stats_merged.csv"
output_dir = "./boxplots_stats"

df = pd.read_csv(csv_path)

# Group by config, attn, size
grouped = df.groupby(["configuration", "attenuation (dB)", "packet size (B)"])

# Prepare new CSV for aggregated results
os.makedirs(output_dir, exist_ok=True)
output_csv_path = os.path.join(output_dir, "aggregated_boxplot_stats.csv")
with open(output_csv_path, "w", newline="") as f:
    f.write("configuration,attenuation (dB),packet size (B),mean (Mibps),median (Mibps),std (Mibps),min (Mibps),max (Mibps),q1 (Mibps),q3 (Mibps)\n")

    for (cfg, attn, size), group in grouped:
        values = group["mean (Mibps)"].values

        mean_val = round(values.mean(), 3)
        median_val = round(pd.Series(values).median(), 3)
        std_val = round(pd.Series(values).std(), 3)
        min_val = round(values.min(), 3)
        max_val = round(values.max(), 3)
        q1 = round(pd.Series(values).quantile(0.25), 3)
        q3 = round(pd.Series(values).quantile(0.75), 3)

        # Save to CSV
        f.write(f"{cfg},{attn},{size},{mean_val},{median_val},{std_val},{min_val},{max_val},{q1},{q3}\n")

# Now plot
for (cfg, attn), sub_df in df.groupby(["configuration", "attenuation (dB)"]):
    grouped_data = sub_df.groupby("packet size (B)")["mean (Mibps)"].apply(list)

    if grouped_data.empty:
        continue

    data = list(grouped_data.values)
    labels = list(grouped_data.index.astype(str))

    plt.figure(figsize=(6, 7))
    plt.boxplot(data, labels=labels, patch_artist=False, showmeans=True)
    plt.title(f"Throughput for\n{cfg}\n(Attenuation: {attn} dB)", fontsize=18)
    plt.xlabel("Packet Size [B]", fontsize=16)
    plt.ylabel("Throughput [Mibps]", fontsize=16)
    plt.xticks(rotation=45, ha="right", fontsize=14)
    plt.yticks(fontsize=14)
    plt.tight_layout()

    filename = f"{cfg.replace('.cfg','')}_{attn}dB_boxplot.png".replace("/", "_")
    plt.savefig(os.path.join(output_dir, filename))
    plt.close()

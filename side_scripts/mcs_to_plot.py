import pandas as pd
import matplotlib.pyplot as plt

# ===== CONFIGURATION =====
ATTENUATION_FILTER = 30  # <- Change this to the attenuation (in dB) you want to plot
CSV_FILE = "boxplot_stats.csv"
OUTPUT_PNG = f"avg_mcs_per_config_{ATTENUATION_FILTER}dB.png"

# ===== LOAD DATA =====
df = pd.read_csv(CSV_FILE)

# ===== FILTER AND GROUP =====
df["attenuation (dB)"] = pd.to_numeric(df["attenuation (dB)"], errors="coerce")
df_filtered = df[df["attenuation (dB)"] == ATTENUATION_FILTER]
avg_mcs_per_config = df_filtered.groupby("configuration")["mean"].mean().reset_index()

# ===== PLOTTING =====
plt.figure(figsize=(16, 10))
plt.barh(avg_mcs_per_config["configuration"], avg_mcs_per_config["mean"], color="skyblue")
plt.xlabel("Average MCS", fontsize=14)
plt.title(f"Average MCS per Configuration (Attenuation: {ATTENUATION_FILTER} dB)", fontsize=16)
plt.grid(True, axis='x', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig(OUTPUT_PNG)
print(f"Saved plot to {OUTPUT_PNG}")

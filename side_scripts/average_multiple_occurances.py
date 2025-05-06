import pandas as pd

# === File paths ===
input_file = "../analysis/Stage II/ping_thrpt/second_try_second_stage_less_demanding/throughput/throughput_merged_raw_stats.csv"
output_file = "../analysis/Stage II/ping_thrpt/second_try_second_stage_less_demanding/throughput/averaged_throughput_by_configuration.csv"

# === Load data ===
df = pd.read_csv(input_file)

# === Identify grouping columns (first 3 columns) ===
group_cols = df.columns[:3].tolist()

# === Define aggregation function on 'mean (Mibps)' ===
def summarize(group):
    series = group['mean (Mibps)']
    return pd.Series({
        "mean (Mibps)": series.mean(),
        "std (Mibps)": series.std(),
        "min (Mibps)": series.min(),
        "max (Mibps)": series.max(),
        "q1 (Mibps)": series.quantile(0.25),
        "median (Mibps)": series.median(),
        "q3 (Mibps)": series.quantile(0.75),
    })

# === Apply groupby and aggregation ===
grouped = df.groupby(group_cols).apply(summarize).reset_index()

# === Save output ===
grouped.to_csv(output_file, index=False)
print(f"✅ Grouped throughput statistics saved to: {output_file}")

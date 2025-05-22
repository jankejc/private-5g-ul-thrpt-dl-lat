import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import matplotlib.ticker as ticker

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
        "pb-178-ul-highTp-autoCSI-TRSonSSB.cfg": "Auto CSI, TRS, SSB",
        "pb-178-ul-highTp-defCSI-rx-to-tx-lat-4.cfg": "DefCSI: Rx to TX Latency = 4",
        "pb-178-ul-highTp-autoCSI-TRSonSSB-sr-per-1-uss.cfg": "Auto CSI, TRS, SSB: SR Period = 1, USS",
        "pb-178-tdd-low-latency-20.cfg": "LL: Bandwidth = 20 MHz",
        "pb-178-ul-highTp-defCSI-rx-to-tx-lat-2.cfg": "DefCSI: Rx to Tx Latency = 2",
        "pb-178-ul-highTp-defCSI-20.cfg": "DefCSI: Bandwidth = 20 MHz",
        "pb-178-ul-highTp-autoCSI-noTRS-20.cfg": "AutoCSI: No TRS, Bandwidth = 20 MHz",
        "pb-178-ul-highTp-defCSI.cfg": "DefCSI"
    }

def attn_mapping(attn_raw):
    return attn_raw.replace("attn_", "") + " dB"

# === ŚCIEŻKI I OUTPUT ===
results_dir = Path('/Users/jan/Moje/PG/Magisterka/private-5g-ul-thrpt-dl-lat/results/one-way-tests/20250430-084824_ping_pcap_one_way/')
output_stats_csv = './analyzed_results/20250430-084824_ping_pcap_one_way/owd_histogram_stats.csv'
output_plot_png = './analyzed_results/20250430-084824_ping_pcap_one_way/owd_histogram_grid.png'
output_plot_filtered_png = output_plot_png.replace(".png", "_no_low_latency.png")
latex_output_file = './analyzed_results/20250430-084824_ping_pcap_one_way/owd_histogram_stats_table.tex'

# === ZBIERANIE DANYCH ===
mapping = config_name_mapping()
histogram_data = {}
all_stats = []

for stats_file in results_dir.rglob('*/attn_*/**/results/**/icmp_analysis_stats.csv'):
    try:
        parts = stats_file.parts
        cfg_file = next(p for p in parts if p.endswith('.cfg'))
        attn_raw = next(p for p in parts if p.startswith('attn_'))

        cfg = mapping.get(cfg_file, cfg_file)
        attn = attn_mapping(attn_raw)

        df = pd.read_csv(stats_file)
        val = df['average_owd_ms'].values[0]

        if pd.notnull(val):
            key = (cfg, attn)
            histogram_data.setdefault(key, []).append(val)
    except Exception as e:
        print(f"⚠️ Error processing {stats_file}: {e}")

# === KONFIGURACJE I TLENIE ===
cfgs = sorted(set(cfg for cfg, _ in histogram_data))
attns = sorted(set(attn for _, attn in histogram_data))
if not cfgs or not attns:
    print("⚠️ No valid data found for plotting.")
    exit()

# === RYSOWANIE HISTOGRAMÓW ===
def draw_histogram_grid(cfgs_subset, filename, nrows=4, ncols=2):
    if nrows is None or ncols is None:
        nrows = len(cfgs_subset)
        ncols = len(attns)

    fig, axes = plt.subplots(nrows, ncols, figsize=(5 * ncols, 4 * nrows))

    # Spłaszcz tablicę axes dla łatwego iterowania
    if nrows == 1 or ncols == 1:
        axes = axes.flatten()
    else:
        axes = [ax for row in axes for ax in row]

    fig.suptitle("OWD Histograms", fontsize=18)

    for idx, (cfg, attn) in enumerate(sorted(histogram_data)):
        if cfg not in cfgs_subset:
            continue
        values = histogram_data.get((cfg, attn), [])
        if idx >= len(axes):
            break
        ax = axes[idx]
        sns.histplot(values, kde=False, bins=15, ax=ax, color='skyblue', edgecolor='black', stat="probability")
        ax.set_title(f"{cfg}\n{attn}", fontsize=14)
        ax.set_xlabel("Average OWD (ms)", fontsize=14)
        ax.set_ylabel("Density", fontsize=14)
        ax.xaxis.set_major_formatter(ticker.FormatStrFormatter('%.2f'))
        ax.tick_params(axis='both', labelsize=12)

    plt.tight_layout()
    plt.savefig(filename)
    plt.close()
    print(f"✅ Histogram grid saved to {filename}")

# === STATYSTYKI
for (cfg, attn), values in histogram_data.items():
    if values:
        series = pd.Series(values)
        all_stats.append({
            'configuration': cfg,
            'attenuation': attn,
            'count': len(values),
            'avg': round(series.mean(), 2),
            'q1': round(series.quantile(0.25), 2),
            'q3': round(series.quantile(0.75), 2),
            'std': round(series.std(), 2),
            'min': round(series.min(), 2),
            'max': round(series.max(), 2),
        })

df_stats = pd.DataFrame(all_stats)
df_stats.to_csv(output_stats_csv, index=False)

draw_histogram_grid(cfgs, output_plot_png)

cfgs_no_ll = [cfg for cfg in cfgs if "LL:" not in cfg and "Low Latency" not in cfg]
if cfgs_no_ll:
    draw_histogram_grid(cfgs_no_ll, output_plot_filtered_png)

# === TABELA LATEX ===
def format_latex_table(stats_df: pd.DataFrame, output_path: str):
    grouped = stats_df.sort_values(['configuration', 'attenuation'])
    latex_lines = [
        r"\begin{table}[H]",
        r"  \caption{\textcolor{ForestGreen}{Average one-way delay (OWD) and standard deviation under varying configurations and attenuations. All configurations were evaluated under the more demanding LiDAR profile.}}",
        r"  \label{table-owd-stats}",
        r"  \color{ForestGreen}",
        r"  \begin{tabularx}{\textwidth}{p{6cm}>{\centering\arraybackslash}p{2.8cm}C}",
        r"    \toprule",
        r"    \textbf{Configuration} & \textbf{Attenuation (dB)} & \makecell{\textbf{Average OWD} \\ \textbf{(ms / SD)}} \\",
        r"    \midrule"
    ]

    current_cfg = None
    for _, row in grouped.iterrows():
        cfg = row['configuration']
        attn = row['attenuation']
        avg = f"{row['avg']:.2f}"
        std = f"{row['std']:.2f}"
        cell = r"\makecell{" + f"{avg} \\textcolor{{gray}}{{/ {std}}}" + "}"

        if cfg != current_cfg:
            if current_cfg is not None:
                latex_lines.append(r"    \midrule")
            current_cfg = cfg
            cfg_latex = f"\\multirow{{1}}{{*}}{{{cfg}}}"
        else:
            cfg_latex = ""

        latex_lines.append(f"    {cfg_latex} & {attn} & {cell} \\\\")

    latex_lines += [
        r"    \bottomrule",
        r"  \end{tabularx}",
        r"\end{table}"
    ]

    with open(output_path, 'w') as f:
        f.write('\n'.join(latex_lines))
    print(f"✅ LaTeX table saved to {output_path}")

format_latex_table(df_stats, latex_output_file)

import pandas as pd
from collections import Counter

def escape_latex(text):
    return text.replace('_', r'\_') if isinstance(text, str) else text

def break_long_config(label):
    parts = label.split(" ")
    if len(parts) > 1 and len(parts[0]) > 30:
        return parts[0] + r"\\" + " ".join(parts[1:])
    return label

def config_name_mapping():
    return {
        "pb-178-tdd-low-latency-rx-to-tx-lat-1.cfg": "LL$^{(a)}$ Rx to Tx Latency = 1",
        "pb-178-tdd-low-latency-rx-to-tx-lat-2.cfg": "LL$^{(a)}$ Rx to Tx Latency = 2",
        "pb-178-tdd-low-latency.cfg": "LL$^{(a)}$ 1",
        "pb-178-ul-highTp-defCSI-sr-per-1.cfg": "HighTpDefCsi$^{(b)}$ SR Period = 1",
        "pb-178-ul-highTp-defCSI-prach-128.cfg": "HighTpDefCsi$^{(b)}$ PRACH = 1",
        "pb-178-ul-highTp-autoCSI-TRSonSSB-rx-to-tx-lat-2.cfg": "HighTpAutoCsi$^{(c)}$ Rx to Tx = 2",
        "pb-178-tdd-low-latency-rx-to-tx-lat-4.cfg": "LL$^{(a)}$ Rx to Tx = 4",
        "pb-178-tdd-low-latency-sr-per-1.cfg": "LL$^{(a)}$ SR Period = 1",
        "pb-178-ul-highTp-defCSI-no-trs.cfg": "HighTpDefCsi$^{(b)}$ No TRS",
        "pb-178-tdd-low-latency-prach-160.cfg": "LL$^{(a)}$ PRACH = 160",
        "pb-178-ul-highTp-autoCSI-noTRS-prach-128.cfg": "HighTpAutoCsi$^{(c)}$ No TRS, PRACH = 128",
        "pb-178-ul-highTp-autoCSI-noTRS.cfg": "HighTpAutoCsi$^{(c)}$ No TRS",
        "pb-178-ul-highTp-autoCSI-TRSonSSB-20.cfg": "HighTpAutoCsiTRSonSSB$^{(d)}$ Bandwidth = 20 MHz",
        "pb-178-ul-highTp-autoCSI-TRSonSSB-prach-128.cfg": "HighTpAutoCsiTRSonSSB$^{(d)}$ PRACH = 128",
        "pb-178-tdd-low-latency-no-rx-to-tx-lat.cfg": "LL$^{(a)}$ No Rx to Tx Latency",
        "pb-178-ul-highTp-autoCSI-TRSonSSB-sr-per-1.cfg": "HighTpAutoCsiTRSonSSB$^{(d)}$ SR Period = 1",
        "pb-178-ul-highTp-autoCSI-noTRS-sr-per-1.cfg": "HighTpDefCsi$^{(b)}$ No TRS, SR Period = 1",
        "pb-178-ul-highTp-autoCSI-TRSonSSB.cfg": "HighTpAutoCsiTRSonSSB$^{(d)}$",
        "pb-178-ul-highTp-defCSI-rx-to-tx-lat-4.cfg": "HighTpDefCsi$^{(b)}$ Rx to TX Latency = 4",
        "pb-178-ul-highTp-autoCSI-TRSonSSB-sr-per-1-uss.cfg": "HighTpAutoCsiTRSonSSB$^{(d)}$ SR Period = 1, USS",
        "pb-178-tdd-low-latency-20.cfg": "LL$^{(a)}$ Bandwidth = 20 MHz",
        "pb-178-ul-highTp-defCSI-rx-to-tx-lat-2.cfg": "HighTpDefCsi$^{(b)}$ Rx to Tx Latency = 2",
        "pb-178-ul-highTp-defCSI-20.cfg": "HighTpDefCsi$^{(b)}$ Bandwidth = 20 MHz",
        "pb-178-ul-highTp-autoCSI-noTRS-20.cfg": "HighTpAutoCsi$^{(c)}$ No TRS, Bandwidth = 20 MHz",
        "pb-178-ul-highTp-defCSI.cfg": "HighTpDefCsi$^{(b)}$"
    }

# Read CSV and rename columns to remove units for easier handling
df = pd.read_csv("boxplot_stats.csv")
df.columns = [
    "configuration",
    "attenuation",
    "packet_size",
    "mean",
    "median",
    "q1",
    "q3"
]

# Sort to ensure configurations are grouped
df = df.sort_values(by=["configuration", "attenuation", "packet_size"])

# Count occurrences of each configuration
config_counts = Counter(df["configuration"])

# Begin LaTeX table manually
header = "\\begin{tabular}{p{3cm} r r r r r r}\n\\toprule\n"
header += "Configuration & Attenuation (dB) & Packet Size (B) & Mean (ms) & Median (ms) & Q1 (ms) & Q3 (ms) \\\\ \n"
header += "\\midrule\n"

rows = []
last_config = None
config_row_tracker = Counter()
mapping = config_name_mapping()

for _, row in df.iterrows():
    config = row["configuration"]
    config_row_tracker[config] += 1

    if config != last_config and last_config is not None:
        rows.append("\\midrule")

    if config_row_tracker[config] == 1:
        display_config = mapping.get(config, escape_latex(config))
        display_config = break_long_config(display_config)
        multirow = f"\\multirow{{{config_counts[config]}}}{{=}}{{\\makecell{{{display_config}}}}}"

    else:
        multirow = ""

    line = f"{multirow} & {escape_latex(str(row['attenuation']))} & {int(row['packet_size'])} & " \
           f"{row['mean']} & {row['median']} & {row['q1']} & {row['q3']} \\\\"
    rows.append(line)
    last_config = config

footer = "\n\\bottomrule\n\\end{tabular}"

# Join everything and print
latex_table = header + '\n'.join(rows) + footer
print(latex_table)
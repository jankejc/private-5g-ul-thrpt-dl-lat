import pandas as pd

def escape_latex(text):
    return text.replace('_', r'\_') if isinstance(text, str) else text

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

# Begin LaTeX table manually (table wrapper)
header = "\\begin{table}\n"
header += "    \\caption{Initial ping only results}\n"
header += "    \\begin{adjustwidth}{-\\extralength}{0cm}\n"
header += "        \\begin{tabular}{p{3cm} c c c c c c}\n"
header += "            \\toprule\n"
header += "            Configuration & Attenuation (dB) & Packet Size (B) & Mean (ms) & Median (ms) & Q1 (ms) & Q3 (ms) \\\\\n"
header += "            \\midrule\n"

rows = []
last_config = None

for _, row in df.iterrows():
    config = row["configuration"]
    show_config = config != last_config
    last_config = config

    if show_config and rows:
        rows.append("            \\midrule")

    config_display = escape_latex(config) if show_config else ""

    line = f"            {config_display} & {escape_latex(str(row['attenuation']))} & {int(row['packet_size'])} & " \
           f"{row['mean']} & {row['median']} & {row['q1']} & {row['q3']} \\\\"
    rows.append(line)

# Finish LaTeX table
footer = "            \\bottomrule\n"
footer += "        \\end{tabular}\n"
footer += "    \\end{adjustwidth}\n"
footer += "\\end{table}"

# Join everything and print
latex_table = header + '\n'.join(rows) + '\n' + footer
print(latex_table)

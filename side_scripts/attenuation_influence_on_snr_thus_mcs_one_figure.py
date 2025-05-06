import pandas as pd
import matplotlib.pyplot as plt

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
        "pb-178-ul-highTp-autoCSI-noTRS-sr-per-1.cfg": "DefCSI: No TRS, SR Period = 1",
        "pb-178-ul-highTp-autoCSI-TRSonSSB.cfg": "AutoCsiTRSonSSB",
        "pb-178-ul-highTp-defCSI-rx-to-tx-lat-4.cfg": "DefCSI: Rx to TX Latency = 4",
        "pb-178-ul-highTp-autoCSI-TRSonSSB-sr-per-1-uss.cfg": "AutoCsiTRSonSSB: SR Period = 1, USS",
        "pb-178-tdd-low-latency-20.cfg": "LL: Bandwidth = 20 MHz",
        "pb-178-ul-highTp-defCSI-rx-to-tx-lat-2.cfg": "DefCSI: Rx to Tx Latency = 2",
        "pb-178-ul-highTp-defCSI-20.cfg": "DefCSI: Bandwidth = 20 MHz",
        "pb-178-ul-highTp-autoCSI-noTRS-20.cfg": "AutoCSI: No TRS, Bandwidth = 20 MHz",
        "pb-178-ul-highTp-defCSI.cfg": "DefCSI"
    }

def plot_snr_and_mcs_one_plot_for_config(config_name):
    # ===== FILE PATHS =====
    snr_file = "snr_boxplot_stats.csv"
    mcs_file = "mcs_boxplot_stats.csv"

    # ===== LOAD DATA =====
    df_snr = pd.read_csv(snr_file)
    df_mcs = pd.read_csv(mcs_file)

    # Convert attenuation to numeric if needed
    df_snr["attenuation (dB)"] = pd.to_numeric(df_snr["attenuation (dB)"], errors="coerce")
    df_mcs["attenuation (dB)"] = pd.to_numeric(df_mcs["attenuation (dB)"], errors="coerce")

    # ===== FILTER BY CONFIGURATION =====
    df_snr = df_snr[df_snr["configuration"] == config_name]
    df_mcs = df_mcs[df_mcs["configuration"] == config_name]

    # ===== GROUP AND AVERAGE =====
    snr_by_attn = df_snr.groupby("attenuation (dB)")["mean (dB)"].mean().reset_index()
    snr_by_attn.columns = ["attenuation", "avg_snr"]

    mcs_by_attn = df_mcs.groupby("attenuation (dB)")["mean"].mean().reset_index()
    mcs_by_attn.columns = ["attenuation", "avg_mcs"]

    # ===== MERGE ON ATTENUATION =====
    merged = pd.merge(snr_by_attn, mcs_by_attn, on="attenuation", how="inner")
    merged = merged.sort_values("attenuation")

    # ===== PLOT =====
    fig, ax_snr = plt.subplots(figsize=(10, 6))

    ax_snr.plot(merged["attenuation"], merged["avg_snr"], marker='o', label="SNR (dB)", color="tab:blue")
    ax_snr.set_xlabel("Attenuation (dB)", fontsize=16, weight='bold')
    ax_snr.set_ylabel("SNR [dB]", color="tab:blue", fontsize=16, weight='bold')
    ax_snr.tick_params(axis='y', labelcolor="tab:blue")
    ax_snr.grid(True)

    ax_mcs = ax_snr.twinx()
    ax_mcs.plot(merged["attenuation"], merged["avg_mcs"], marker='s', label="MCS", color="tab:red")
    ax_mcs.set_ylabel("MCS", color="tab:red", fontsize=16, weight='bold')
    ax_mcs.tick_params(axis='both', which='major', labelsize=14)
    ax_snr.tick_params(axis='both', which='major', labelsize=14)

    # === Get renamed config name for title ===
    mapping = config_name_mapping()
    renamed_title = mapping.get(config_name, config_name)

    plt.title(f"SNR and MCS vs. Attenuation for {renamed_title}", fontsize=18)

    plt.tight_layout()
    filename = f"snr_mcs_{config_name.replace(' ', '_').replace(':', '')}.png"
    plt.savefig(filename)
    print(f"Plot saved to {filename}")
    plt.show()


if __name__ == "__main__":
    # Replace with your specific configuration name
    plot_snr_and_mcs_one_plot_for_config("pb-178-ul-highTp-autoCSI-TRSonSSB.cfg")

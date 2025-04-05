from scapy.all import PcapReader
import pandas as pd
import numpy as np
import time
import multiprocessing
import os

# Konfiguracja użytkownika
PCAP_FILES = ["512_10_90_nir8.pcap", "1024_10_90_nir8.pcap", "2048_10_90_nir8.pcap", "512_20_90_nir8.pcap", "1024_20_90_nir8.pcap",
              "512_10_180_nir8.pcap", "1024_10_180_nir8.pcap", "2048_10_180_nir8.pcap", "512_20_180_nir8.pcap", "1024_20_180_nir8.pcap",
              "512_10_270_nir8.pcap", "1024_10_270_nir8.pcap", "2048_10_270_nir8.pcap", "512_20_270_nir8.pcap", "1024_20_270_nir8.pcap",
              "512_10_360_nir8.pcap", "1024_10_360_nir8.pcap", "2048_10_360_nir8.pcap", "512_20_360_nir8.pcap", "1024_20_360_nir8.pcap"]  # Lista plików do przetworzenia
TARGET_IP = "169.254.34.10"
NUM_PROCESSES = 20  # Liczba rdzeni do wykorzystania

def process_pcap(pcap_file):
    start_time = time.time()
    print(f"[PID {os.getpid()}] Przetwarzanie pliku {pcap_file} w locie...")
    
    timestamps = []
    sizes = []
    
    with PcapReader(pcap_file) as pcap:
        for pkt in pcap:
            if pkt.haslayer("IP"):  # Sprawdź, czy pakiet ma warstwę IP
                ip_layer = pkt["IP"]
                if ip_layer.src == TARGET_IP or ip_layer.dst == TARGET_IP:
                    timestamps.append(pkt.time)
                    sizes.append(len(pkt))  # Pobierz długość pakietu w bajtach
    
    print(f"[PID {os.getpid()}] Znaleziono {len(timestamps)} pakietów związanych z {TARGET_IP}.")
    
    # Tworzymy DataFrame
    df = pd.DataFrame({"time": timestamps, "size": sizes})
    df["time"] = df["time"] - df["time"].min()  # Normalizujemy czas od 0 sekundy

    # Analiza przepustowości (przepustowość w Mebibitach na sekundę - Mibps)
    start_time_interval = 5
    end_time_interval = 605
    interval = 60
    results = []
    throughput_means = []

    print(f"[PID {os.getpid()}] Obliczanie przepustowości dla {pcap_file}...")
    total_intervals = (end_time_interval - start_time_interval) // interval
    for i, t in enumerate(range(start_time_interval, end_time_interval, interval)):
        mask = (df["time"] >= t) & (df["time"] < t + interval)
        total_bits = df.loc[mask, "size"].sum() * 8  # Zamiana bajtów na bity
        throughput_mean = total_bits / interval / (1024 * 1024)  # Mibps (Mebibity/s)
        throughput_means.append(throughput_mean)
        
        # Obliczenie chwilowej przepustowości na sekundę w danej minucie
        per_second = []
        for sec in range(t, t + interval):
            sec_mask = (df["time"] >= sec) & (df["time"] < sec + 1)
            sec_bits = df.loc[sec_mask, "size"].sum() * 8
            per_second.append(sec_bits / (1024 * 1024))  # Mibps

        # Obliczenie odchylenia standardowego chwilowej przepustowości w danej minucie
        throughput_std = np.std(per_second) if per_second else 0

        results.append([pcap_file, t, throughput_mean, throughput_std])
        print(f"[PID {os.getpid()}] {pcap_file}: Przetworzono {i+1}/{total_intervals} minut.")
    
    # Obliczenie średniej z 10 minut oraz jej odchylenia standardowego
    if throughput_means:
        mean_10min = np.mean(throughput_means)
        std_10min = np.std(throughput_means)
        results.append([pcap_file, "10min_avg", mean_10min, std_10min])
        print(f"[PID {os.getpid()}] {pcap_file}: Średnia z 10 minut: {mean_10min:.7f} Mibps, Odchylenie standardowe: {std_10min:.7f} Mibps")
    
    # Zapis wyników do pliku CSV
    output_file = f"results_{os.path.splitext(pcap_file)[0]}.csv"
    df_results = pd.DataFrame(results, columns=["pcap_file", "interval_start", "throughput_mibps", "std_mibps"])
    df_results.to_csv(output_file, index=False)
    print(f"[PID {os.getpid()}] Wyniki zapisano do {output_file}.")
    
    end_time = time.time()
    print(f"[PID {os.getpid()}] Czas przetwarzania {pcap_file}: {end_time - start_time:.2f} sekund.")

if __name__ == "__main__":
    start_time_script = time.time()
    
    with multiprocessing.Pool(NUM_PROCESSES) as pool:
        pool.map(process_pcap, PCAP_FILES)
    
    end_time_script = time.time()
    print(f"Całkowity czas wykonania skryptu: {end_time_script - start_time_script:.2f} sekund.")

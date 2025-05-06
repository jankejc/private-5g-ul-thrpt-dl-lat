import pyshark
import os
import pandas as pd
from collections import defaultdict

# ===== PARAMETERS =====
PCAP_FILE = "./pcaps/rep-req-req-1.pcap"
REQ_SRC_IP = "192.168.123.1"
REPLY_SRC_IP = "192.168.123.2"
MIRROR_SRC_IP = "192.168.124.2"

# ===== CAPTURE ICMP & UDP PACKETS =====
print("Loading PCAP file...")
cap = pyshark.FileCapture(PCAP_FILE, display_filter="icmp or udp")

packets_by_seq = defaultdict(lambda: {'requests': [], 'reply': None})

for pkt in cap:
    try:
        ts = float(pkt.sniff_timestamp)
        src_ip = pkt.ip.src

        if "ICMP" in pkt:
            icmp = pkt.icmp
            seq = int(icmp.seq)
            if src_ip == REQ_SRC_IP or src_ip == MIRROR_SRC_IP:
                packets_by_seq[seq]['requests'].append(ts)
            elif src_ip == REPLY_SRC_IP:
                packets_by_seq[seq]['reply'] = ts

    except Exception:
        continue

cap.close()

# ===== PROCESS DATA =====
data = []
loss_count = 0
rtt_sum = 0
owd_sum = 0
rtt_count = 0
owd_count = 0

for seq, pkt in packets_by_seq.items():
    row = {'seq': seq}
    reqs = pkt['requests']
    reply = pkt['reply']

    if len(reqs) >= 2:
        owd = (reqs[1] - reqs[0]) * 1000  # convert to ms
        row['req1_ts'] = reqs[0]
        row['req2_ts'] = reqs[1]
        row['owd_ms'] = owd
        owd_sum += owd
        owd_count += 1
    else:
        row['owd_ms'] = None

    if reply and reqs:
        rtt = (reply - reqs[0]) * 1000  # convert to ms
        row['reply_ts'] = reply
        row['rtt_ms'] = rtt
        rtt_sum += rtt
        rtt_count += 1
    else:
        row['rtt_ms'] = None
        loss_count += 1

    data.append(row)

# ===== SAVE OUTPUT =====
filename_without_ext = os.path.splitext(os.path.basename(PCAP_FILE))[0]
output_dir = f"./results/{filename_without_ext}"
os.makedirs(output_dir, exist_ok=True)

df = pd.DataFrame(data)
df.to_csv(f"{output_dir}/icmp_pair_timings.csv", index=False)

stats = {
    'total_icmp_packets': sum(len(pkt['requests']) + (1 if pkt['reply'] else 0) for pkt in packets_by_seq.values()),
    'total_seqs': len(packets_by_seq),
    'total_req1': sum(1 for pkt in packets_by_seq.values() if len(pkt['requests']) >= 1),
    'total_req2': sum(1 for pkt in packets_by_seq.values() if len(pkt['requests']) >= 2),
    'total_replies': sum(1 for pkt in packets_by_seq.values() if pkt['reply']),
    'total_loss': loss_count,
    'average_owd_ms': (owd_sum / owd_count) if owd_count else None,
    'average_rtt_ms': (rtt_sum / rtt_count) if rtt_count else None,
    'loss_percentage': (loss_count / len(packets_by_seq)) * 100
}

stats_df = pd.DataFrame([stats])
stats_df.to_csv(f"{output_dir}/icmp_analysis_stats.csv", index=False)
print(f"Analysis complete. Results saved to {output_dir}")

import pyshark
from pyshark.capture.capture import TSharkCrashException
import os
import gzip
import shutil
import tempfile
import pandas as pd
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# ===== PARAMETERS =====
REQ_SRC_IP = "192.168.123.1"
REPLY_SRC_IP = "192.168.123.2"
MIRROR_SRC_IP = "192.168.124.2"
MAX_WORKERS = 2


def extract_gz_to_temp(gz_path):
    """ Extract .gz file to a temporary location and return the temp file path. """
    temp_dir = tempfile.mkdtemp()
    temp_file_path = os.path.join(temp_dir, os.path.basename(gz_path).replace('.gz', ''))

    with gzip.open(gz_path, 'rb') as gz_file, open(temp_file_path, 'wb') as temp_file:
        shutil.copyfileobj(gz_file, temp_file)

    return temp_file_path


def process_pcap_file(pcap_file):
    """ Process a single PCAP or PCAP.GZ file. """
    print(f"Processing {pcap_file}...")
    packets_by_seq = defaultdict(lambda: {'requests': [], 'reply': None})
    current_group = 0
    last_seq = -1

    # Extract .gz files to temporary files
    is_temp_file = False
    if str(pcap_file).endswith(".gz"):
        try:
            pcap_file = extract_gz_to_temp(pcap_file)
            is_temp_file = True
        except Exception as e:
            print(f"Error extracting {pcap_file}: {e}")
            return

    try:
        cap = pyshark.FileCapture(str(pcap_file), display_filter="icmp or udp")

        for pkt in cap:
            try:
                ts = float(pkt.sniff_timestamp)
                src_ip = pkt.ip.src

                # Ensure ICMP layer and check type
                if hasattr(pkt, 'icmp'):
                    icmp = pkt.icmp
                    seq = int(icmp.seq)
                    icmp_type = icmp.type

                    # Detect sequence number reset
                    if last_seq != -1 and seq < last_seq:
                        current_group += 1

                    last_seq = seq
                    seq_key = (current_group, seq)

                    # Echo request (type 8)
                    if icmp_type == '8' and (src_ip == REQ_SRC_IP or src_ip == MIRROR_SRC_IP):
                        packets_by_seq[seq_key]['requests'].append(ts)

                    # Echo reply (type 0)
                    elif icmp_type == '0' and src_ip == REPLY_SRC_IP:
                        packets_by_seq[seq_key]['reply'] = ts

            except Exception:
                continue

    except TSharkCrashException as e:
        print(f"⚠️ TShark crashed while processing {pcap_file}: {e}")
    finally:
        if 'cap' in locals():
            try:
                cap.close()
            except Exception:
                pass

        # Clean up temporary files
        if is_temp_file:
            os.remove(pcap_file)

    # Process and save results
    process_data_and_save(pcap_file, packets_by_seq)


def process_data_and_save(pcap_file, packets_by_seq):
    """ Process data and save output to CSV. """
    data = []
    loss_count = 0
    rtt_sum = 0
    owd_sum = 0
    rtt_count = 0
    owd_count = 0

    for (group_id, seq), pkt in packets_by_seq.items():
        row = {'group_id': group_id, 'seq': seq}
        reqs = pkt['requests']
        reply = pkt['reply']

        # One-way delay
        if len(reqs) >= 2:
            owd = (reqs[1] - reqs[0]) * 1000  # ms
            row['req1_ts'] = reqs[0]
            row['req2_ts'] = reqs[1]
            row['owd_ms'] = owd
            owd_sum += owd
            owd_count += 1
        else:
            row['owd_ms'] = None

        # RTT
        if reply is not None and reqs:
            rtt = (reply - reqs[0]) * 1000  # ms
            row['reply_ts'] = reply
            row['rtt_ms'] = rtt
            rtt_sum += rtt
            rtt_count += 1
        else:
            row['rtt_ms'] = None
            loss_count += 1

        data.append(row)

    # Save individual results
    filename_without_ext = os.path.splitext(os.path.basename(pcap_file))[0]
    output_dir = Path(f"./results/{filename_without_ext}")
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(data)
    df.to_csv(output_dir / "icmp_pair_timings.csv", index=False)

    # Save statistics
    stats = {
        'total_icmp_packets': sum(len(pkt['requests']) + (1 if pkt['reply'] else 0) for pkt in packets_by_seq.values()),
        'total_seqs': len(packets_by_seq),
        'total_req1': sum(1 for pkt in packets_by_seq.values() if len(pkt['requests']) >= 1),
        'total_req2': sum(1 for pkt in packets_by_seq.values() if len(pkt['requests']) >= 2),
        'total_replies': sum(1 for pkt in packets_by_seq.values() if pkt['reply']),
        'total_loss': loss_count,
        'average_owd_ms': (owd_sum / owd_count) if owd_count else None,
        'average_rtt_ms': (rtt_sum / rtt_count) if rtt_count else None,
        'loss_percentage': (loss_count / len(packets_by_seq) * 100) if packets_by_seq else 0
    }

    stats_df = pd.DataFrame([stats])
    stats_df.to_csv(output_dir / "icmp_analysis_stats.csv", index=False)
    print(f"Completed {pcap_file}")


def aggregate_results():
    """ Aggregate results across all processed files. """
    result_files = list(Path('../results/one-way-tests/results').rglob('icmp_analysis_stats.csv'))

    if not result_files:
        print("No result files found for aggregation.")
        return

    dfs = [pd.read_csv(file) for file in result_files]
    combined_df = pd.concat(dfs, ignore_index=True)

    # Calculate aggregated statistics
    agg_stats = {
        'total_icmp_packets': combined_df['total_icmp_packets'].sum(),
        'total_seqs': combined_df['total_seqs'].sum(),
        'total_req1': combined_df['total_req1'].sum(),
        'total_req2': combined_df['total_req2'].sum(),
        'total_replies': combined_df['total_replies'].sum(),
        'total_loss': combined_df['total_loss'].sum(),
        'average_owd_ms': combined_df['average_owd_ms'].mean(),
        'average_rtt_ms': combined_df['average_rtt_ms'].mean(),
        'loss_percentage': combined_df['loss_percentage'].mean()
    }

    output_path = Path('../results/one-way-tests/results/aggregated_icmp_stats.csv')
    pd.DataFrame([agg_stats]).to_csv(output_path, index=False)
    print(f"Aggregated results saved to {output_path}")


def main():
    """ Main function to handle multithreading and file processing. """
    pcap_files = list(Path('../results/one-way-tests/pcaps-tests').glob('*.pcap*'))
    print(f"Found {len(pcap_files)} PCAP and PCAP.GZ files")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_pcap_file, pcap_file): pcap_file for pcap_file in pcap_files}

        for future in as_completed(futures):
            pcap_file = futures[future]
            try:
                future.result()
            except Exception as e:
                print(f"Error processing {pcap_file}: {e}")

    # Aggregate results after processing all files
    aggregate_results()


if __name__ == "__main__":
    main()

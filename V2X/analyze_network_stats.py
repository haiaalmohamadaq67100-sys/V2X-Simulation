import pandas as pd
import numpy as np
import argparse


# -------------------------------------------------------
# Network scenario identification
# -------------------------------------------------------

def identify_network_quality(loss, avg_delay):

    if loss == 0 and avg_delay < 20:
        return "IDEAL NETWORK"

    if loss < 2 and avg_delay < 50:
        return "GOOD NETWORK"

    if loss < 10 and avg_delay < 150:
        return "MODERATE NETWORK"

    return "POOR NETWORK"


# -------------------------------------------------------
# Latency distribution
# -------------------------------------------------------

def latency_percentiles(delays):

    if len(delays) == 0:
        return None

    return {
        "p50": np.percentile(delays, 50),
        "p95": np.percentile(delays, 95),
        "p99": np.percentile(delays, 99)
    }


# -------------------------------------------------------
# Message statistics
# -------------------------------------------------------

def compute_stats(df, msg_type):

    subset = df[df["message_type"] == msg_type]

    sent = len(subset)
    dropped = subset["dropped"].sum()
    rx = sent - dropped

    loss = (dropped / sent * 100) if sent > 0 else 0

    delays = subset[subset["dropped"] == False]["delay_ms"]

    avg_delay = delays.mean() if len(delays) else None
    min_delay = delays.min() if len(delays) else None
    max_delay = delays.max() if len(delays) else None
    std_delay = delays.std() if len(delays) else None

    percentiles = latency_percentiles(delays)

    

    return {
        "sent": sent,
        "dropped": dropped,
        "rx": rx,
        "loss": loss,
        "avg_delay": avg_delay,
        "min_delay": min_delay,
        "max_delay": max_delay,
        "std_delay": std_delay,
        "percentiles": percentiles,
     
    }


# -------------------------------------------------------
# Print report
# -------------------------------------------------------

def print_report(name, stats):

    print(f"\n===== {name} ANALYSIS =====")

    print("Sent packets :", stats["sent"])
    print("Dropped      :", stats["dropped"])
    print("Received     :", stats["rx"])
    print("Loss         : {:.2f}%".format(stats["loss"]))

    if stats["avg_delay"] is not None:

        print("\nLatency statistics")

        print("Average delay :", round(stats["avg_delay"],2),"ms")
        print("Min delay     :", round(stats["min_delay"],2),"ms")
        print("Max delay     :", round(stats["max_delay"],2),"ms")
        print("Jitter (std)  :", round(stats["std_delay"],2),"ms")

        p = stats["percentiles"]

        if p:
            print("\nLatency percentiles")
            print("P50 :", round(p["p50"],2),"ms")
            print("P95 :", round(p["p95"],2),"ms")
            print("P99 :", round(p["p99"],2),"ms")




# -------------------------------------------------------
# Main
# -------------------------------------------------------

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("--messages", required=True)
    

    args = parser.parse_args()

    msg_df = pd.read_csv(args.messages)
    

    print("\n========== NETWORK PERFORMANCE REPORT ==========\n")

    cam_stats = compute_stats(msg_df, "cam")

    print_report("CAM", cam_stats)

    scenario = identify_network_quality(
        cam_stats["loss"],
        cam_stats["avg_delay"] if cam_stats["avg_delay"] else 0
    )

    print("\nDetected network quality :", scenario)

    req_stats = compute_stats(msg_df, "mcm_request")
    print_report("MCM REQUEST", req_stats)

    resp_stats = compute_stats(msg_df, "mcm_response")
    print_report("MCM RESPONSE", resp_stats)

    term_stats = compute_stats(msg_df, "mcm_termination")
    print_report("MCM TERMINATION", term_stats)

   # print("\n========== SESSION ANALYSIS ==========")

    #completed = sess_df[sess_df["completed"] == True]

   # if len(completed):

    #    print("Completed sessions :", len(completed))

     #   print("Average session duration :",
      #        round(completed["duration_sim"].mean(),3),"s")

       # print("Min session duration :",
        #      round(completed["duration_sim"].min(),3),"s")

       # print("Max session duration :",
        #      round(completed["duration_sim"].max(),3),"s")

   # else:

    #    print("No completed sessions detected")


if __name__ == "__main__":
    main()

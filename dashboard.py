import streamlit as st
import pandas as pd
from datetime import datetime
import subprocess
import sys
from pathlib import Path
import os  # Import os to check for file existence

# ---- Configs ----
GATEWAY_URL = "http://127.0.0.1:8000/vitals-db"
# FIX: Point to the 'log.txt' file in the root, where gateway.py writes to it
LOG_PATH = Path("log.txt")
REFRESH_MS = 10000  # milliseconds (2 seconds)

# ---- Auto-refresh ----
# This is a common way to handle auto-refresh in Streamlit
st.markdown(f'<meta http-equiv="refresh" content="{REFRESH_MS / 1000}">', unsafe_allow_html=True)

# ---- Static UI ----
st.set_page_config(page_title="Zero Trust IoT Dashboard", layout="wide")
st.title("Zero Trust IoT Dashboard")
st.write("This is our real-time security monitor.")

# --- Current Time Placeholder (high up) ---
time_placeholder = st.empty()

# Attack button (static)
st.subheader("Simulate Attacks")
colA, _ = st.columns(2)

# We need an 'attack_simulator.py' file for this button to work.
# Let's assume it's in the same directory.
attack_script_path = "attack_simulator.py"

if colA.button("Sim Spoofing Attack)"):
    if os.path.exists(attack_script_path):
        # We pass GATEWAY_URL as an argument to the script
        subprocess.Popen([sys.executable, attack_script_path, GATEWAY_URL])
        st.success("Attack simulator started! Sending spoofed requests to gateway!")
    else:
        st.error(f"Error: '{attack_script_path}' not found.")

st.markdown("---")

# ---- Static headers ----
st.subheader("Summary Metrics")

# Static column titles
col1, col2, col3 = st.columns(3)
col1.write("**GRANTED**")
col2.write("**Policy Denials**")
col3.write("**Spoofing Denials**")

# Dynamic placeholders for numbers
granted_placeholder = col1.empty()
policy_denied_placeholder = col2.empty()
spoofing_denied_placeholder = col3.empty()

st.subheader("Live Security Logs (Most Recent First)")
logs_placeholder = st.empty()


# ---- Helper functions ----
def load_logs(path: Path) -> pd.DataFrame:
    """
    Robustly loads the log file, handling commas in the message field.
    """
    if not path.exists():
        return pd.DataFrame(columns=["timestamp", "device", "role", "target", "status", "message"])

    data = []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    # Split on the first 5 commas ONLY.
                    # Everything else (including more commas) goes into the 'message' field.
                    parts = line.strip().split(',', 5)

                    if len(parts) == 6:
                        data.append(parts)
                    else:
                        # Handle lines that have fewer than 6 fields by padding with None
                        padded_parts = parts + [None] * (6 - len(parts))
                        data.append(padded_parts)
                except Exception as e:
                    # This will catch any truly malformed lines that can't be split
                    print(f"Skipping malformed log line: {line.strip()} - Error: {e}")

        df = pd.DataFrame(data, columns=["timestamp", "device", "role", "target", "status", "message"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        # Sort to show most recent first
        df = df.sort_values(by="timestamp", ascending=False).reset_index(drop=True)
        return df

    except pd.errors.EmptyDataError:
        # This is normal if the file was just created
        return pd.DataFrame(columns=["timestamp", "device", "role", "target", "status", "message"])
    except Exception as e:
        st.warning(f"Error reading log file: {e}")
        return pd.DataFrame(columns=["timestamp", "device", "role", "target", "status", "message"])


def highlight_row(row):
    """Applies color styling to the DataFrame rows based on status."""
    color = "background-color: transparent"
    status = str(row.get("status", ""))

    if status == "DENIED_SPOOFING":
        color = "background-color: #a63232; color: white"  # Red for spoofing
    elif status == "DENIED_POLICY":
        color = "background-color: #f0e68c; color: #333"  # Yellow for policy
    elif status == "GRANTED":
        color = "background-color: #32a65a; color: white"  # Green for granted

    return [color] * len(row)


# ---- Refresh dynamic data ----
df = load_logs(LOG_PATH)

# Update metrics
# Using your metric split, which is great!
granted_count = df[df["status"] == "GRANTED"].shape[0]
policy_denied_count = df[df["status"] == "DENIED_POLICY"].shape[0]
spoofing_denied_count = df[df["status"] == "DENIED_SPOOFING"].shape[0]

# --- FIX for Streamlit warnings ---
# Provide a label, but hide it, as recommended by the warning.
granted_placeholder.metric(label="Granted", value=f"{granted_count}", label_visibility="hidden")
policy_denied_placeholder.metric(label="Policy Denials", value=f"{policy_denied_count}", label_visibility="hidden")
spoofing_denied_placeholder.metric(label="Spoofing Denials", value=f"{spoofing_denied_count}",
                                   label_visibility="hidden")

# Update log table
if df.empty:
    logs_placeholder.info("No log file found or file is empty. Run 'run_simulator.py' to generate events.")
else:
    # Apply styling and display the dataframe
    logs_placeholder.dataframe(
        df.style.apply(highlight_row, axis=1),
        height=400,
        use_container_width=True
    )

# Update current time dynamically
time_placeholder.markdown(f"**Last Refresh:** {datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}")
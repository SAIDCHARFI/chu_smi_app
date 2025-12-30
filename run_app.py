import subprocess
import webbrowser
import socket
import time
import os
import sys

# run_app.py
import streamlit as st
import pandas as pd
import numpy as np
# import any other libraries you used in main.py

# --- Streamlit app starts here ---
st.set_page_config(page_title="My App", layout="wide")

st.title("My Streamlit App")

# Example: move any Streamlit code from main.py here
# For instance, if main.py had:
# df = pd.read_csv("data.csv")
# st.write(df)

# --- Example content ---
st.write("Hello! Your app is now ready for Streamlit Cloud.")

PORT = 8501
URL = f"http://127.0.0.1:{PORT}"
MAIN_FILE = os.path.abspath("main.py")

def is_port_in_use(port):
    """Check if a port is currently in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0

def start_streamlit():
    """Start Streamlit in a subprocess."""
    return subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", MAIN_FILE,
         "--server.port", str(PORT),
         "--server.headless", "true",
         "--browser.gatherUsageStats", "false"],
        stdout=None,
        stderr=None
    )

def wait_for_streamlit(timeout=60):
    """Wait until Streamlit is ready on the port."""
    start_time = time.time()
    while not is_port_in_use(PORT):
        if time.time() - start_time > timeout:
            raise RuntimeError("Streamlit failed to start in time.")
        time.sleep(0.5)

if __name__ == "__main__":
    # If Streamlit is already running, just open browser
    if is_port_in_use(PORT):
        webbrowser.open(URL)
        sys.exit(0)

    # Start Streamlit
    st_process = start_streamlit()

    try:
        wait_for_streamlit()  # Wait until server is ready
        webbrowser.open(URL)   # Open in default browser
        st_process.wait()      # Keep launcher alive while Streamlit runs
    except KeyboardInterrupt:
        st_process.terminate()
        st_process.wait()
    except Exception as e:
        print(f"Error: {e}")
        st_process.terminate()
        st_process.wait()
        sys.exit(1)

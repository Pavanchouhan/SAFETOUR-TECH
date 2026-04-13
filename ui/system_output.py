import streamlit as st
import os


LOG_FILE = "logs/runtime_output.log"


# =====================================================
# WRITE LOG
# =====================================================
def log_output(message):

    os.makedirs("logs", exist_ok=True)

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(message + "\n")


# =====================================================
# VIEW LOG
# =====================================================
def render():

    st.subheader("📟 System Runtime Output")

    if not os.path.exists(LOG_FILE):
        st.info("No logs yet.")
        return

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()[-80:]

    log_text = "".join(lines)

    st.text_area(
        "Runtime Logs",
        log_text,
        height=300
    )
# ui/blockchain_view.py
import streamlit as st
import json, os

def render():
    st.subheader("⛓ Blockchain Logs")

    chain_file = "logs/blockchain_chain.json"

    if os.path.exists(chain_file):
        with open(chain_file) as f:
            data = [json.loads(l) for l in f.readlines()[-30:]]
        st.json(data)
    else:
        st.info("No blockchain logs yet")

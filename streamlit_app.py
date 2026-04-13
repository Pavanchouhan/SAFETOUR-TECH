import streamlit as st
from ui.auth import render_auth
from ui.live_dashboard import live_dashboard


# =========================================================
# SESSION INIT
# =========================================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False


# =========================================================
# MAIN APP
# =========================================================
def main():

    st.set_page_config(
        page_title="SafeTourTech",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Global UI Theme
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg,#0f2027,#203a43,#2c5364);
        color:white;
    }
    #MainMenu {visibility:hidden;}
    footer {visibility:hidden;}
    </style>
    """, unsafe_allow_html=True)

    # AUTH
    logged_in = render_auth()

    if logged_in:
        st.session_state.logged_in = True

    # DASHBOARD / WELCOME
    if st.session_state.logged_in:
        live_dashboard()
    else:
        st.markdown("""
        <div style="
            padding:50px;
            border-radius:25px;
            background: rgba(255,255,255,0.05);
            backdrop-filter: blur(12px);
            box-shadow:0 0 35px rgba(0,230,255,0.25);
            margin-top:80px;
        ">
        <h1 style="color:#00e6ff;">🧭 Welcome to SafeTourTech</h1>
        <h3>Smart AI-Based Safety Monitoring System</h3>
        <hr>
        <p>
        SafeTour helps users evaluate real-time area safety
        using hybrid geo-intelligence and AI risk scoring.
        </p>
        <p>🔐 Login from sidebar to continue.</p>
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
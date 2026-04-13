import streamlit as st
import folium
from streamlit_folium import st_folium
from streamlit_geolocation import streamlit_geolocation
from core.india_safety_engine import detect_zone_india as detect_zone
from core.blockchain_logger import add_block
from ui.system_output import log_output, render as system_output_view
import requests
import time


# =========================================================
# REMOVE GEOLOCATION STRIP + HEADER GAP
# =========================================================
st.markdown("""
<style>

iframe[title="streamlit_geolocation.streamlit_geolocation"] {
    display:none !important;
}

div:has(iframe[title="streamlit_geolocation.streamlit_geolocation"]) {
    display:none !important;
}

[data-testid="stVerticalBlock"]:has(iframe) {
    display:none !important;
}

header {
    display:none !important;
}

.block-container {
    padding-top: 1rem;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# BLINK ICON
# =========================================================
BLINK_ICON = """
<div style="
background:red;
width:20px;
height:20px;
border-radius:50%;
box-shadow:0 0 20px red;
animation:blink 1s infinite;"></div>

<style>
@keyframes blink {
0%{opacity:1;}
50%{opacity:0.2;}
100%{opacity:1;}
}
</style>
"""


# =========================================================
# DASHBOARD
# =========================================================
def live_dashboard():

    st.title("🛡️ SafeTour Live Safety Map")

    # SESSION STATE
    if "location_locked" not in st.session_state:
        st.session_state.location_locked = False

    if "lat" not in st.session_state:
        st.session_state.lat = None
        st.session_state.lon = None

    if "last_zone" not in st.session_state:
        st.session_state.last_zone = None

    # =====================================================
    # GPS FETCH
    # =====================================================
    if not st.session_state.location_locked:

        loc = streamlit_geolocation()

        if loc and loc["latitude"]:

            st.session_state.lat = loc["latitude"]
            st.session_state.lon = loc["longitude"]

        else:
            st.warning("Allow GPS permission")
            return

    lat = st.session_state.lat
    lon = st.session_state.lon

    # =====================================================
    # SEARCH
    # =====================================================
    st.subheader("🔎 Search Location")

    search = st.text_input("Enter place")

    if st.button("Search") and search:

        url = f"https://nominatim.openstreetmap.org/search?q={search}&format=json"

        res = requests.get(
            url,
            headers={"User-Agent": "SafeTour"},
            timeout=5
        ).json()

        if res:

            st.session_state.lat = float(res[0]["lat"])
            st.session_state.lon = float(res[0]["lon"])
            st.session_state.location_locked = True
            st.rerun()

    if st.button("📍 Back to My Live Location"):

        st.session_state.location_locked = False
        st.rerun()

    # =====================================================
    # ZONE DETECTION
    # =====================================================
    zone = detect_zone((lat, lon))

    # =====================================================
    # 🔗 BLOCKCHAIN + SYSTEM OUTPUT CONNECTION
    # =====================================================
    if zone != st.session_state.last_zone:

        # System Output Log
        log_output(
            f"[ZONE] {zone} detected at ({lat}, {lon})"
        )

        # Blockchain Entry
        add_block(
            "ZONE_DETECTION",
            f"{zone} zone detected",
            {
                "latitude": lat,
                "longitude": lon,
                "zone": zone,
                "timestamp": time.time()
            }
        )

        st.session_state.last_zone = zone

    # =====================================================
    # MAP
    # =====================================================
    color_map = {
        "SAFE": "green",
        "CAUTION": "orange",
        "DANGER": "red"
    }

    m = folium.Map(
        location=[lat, lon],
        zoom_start=14
    )

    if zone == "DANGER":

        folium.Marker(
            [lat, lon],
            icon=folium.DivIcon(html=BLINK_ICON)
        ).add_to(m)

    else:

        folium.Marker(
            [lat, lon],
            icon=folium.Icon(color=color_map[zone])
        ).add_to(m)

    folium.Circle(
        [lat, lon],
        radius=400,
        color=color_map[zone],
        fill=True,
        fill_opacity=0.3
    ).add_to(m)

    map_data = st_folium(
        m,
        use_container_width=True,
        height=650,
        returned_objects=["last_clicked"]
    )

    # CLICK HANDLER
    if map_data and map_data.get("last_clicked"):

        st.session_state.lat = map_data["last_clicked"]["lat"]
        st.session_state.lon = map_data["last_clicked"]["lng"]
        st.session_state.location_locked = True
        st.rerun()

    # =====================================================
    # STATUS
    # =====================================================
    st.subheader("📊 Area Status")

    if zone == "SAFE":
        st.success("SAFE ZONE ✅")

    elif zone == "CAUTION":
        st.warning("RISK ZONE ⚠️")

    else:
        st.error("DANGER ZONE ❌")

    # =====================================================
    # SYSTEM OUTPUT VIEWER
    # =====================================================
    st.markdown("---")
    system_output_view()
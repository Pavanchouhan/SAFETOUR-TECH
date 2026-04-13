# =========================================================
# 🇮🇳 SAFETOUR — HYBRID INDIA SAFETY ENGINE
# ML + ENVIRONMENT + RANDOM FOREST MODEL II
# =========================================================

import pandas as pd
import numpy as np
from sklearn.neighbors import BallTree
from datetime import datetime
import requests
from geopy.distance import geodesic
import joblib
import os


# =========================================================
# 📊 LOAD CRIME DATASET
# =========================================================

df = pd.read_csv("core/crime_dataset_features.csv")

coords = df[["Latitude", "Longitude"]].values

tree = BallTree(
    np.radians(coords),
    metric="haversine"
)


# =========================================================
# 🤖 LOAD MODEL II (OPTIONAL)
# =========================================================

try:

    MODEL_PATH = os.path.join(
        "models",
        "best_model_random_forest_balanced.joblib"
    )

    ENCODER_PATH = os.path.join(
        "models",
        "label_encoder.pkl"
    )

    zone_model = joblib.load(MODEL_PATH)
    zone_encoder = joblib.load(ENCODER_PATH)

    MODEL2_AVAILABLE = True

except:

    zone_model = None
    zone_encoder = None
    MODEL2_AVAILABLE = False


# =========================================================
# 🌙 NIGHT FACTOR
# =========================================================

def get_night_factor():

    hour = datetime.now().hour

    if hour >= 20 or hour <= 5:
        return 1

    return 0


# =========================================================
# 🌍 LAND TYPE DETECTION
# =========================================================

def get_land_type(lat, lon):

    url = (
        f"https://nominatim.openstreetmap.org/"
        f"reverse?format=json&lat={lat}&lon={lon}"
    )

    try:

        data = requests.get(
            url,
            headers={"User-Agent": "SafeTourAI"},
            timeout=5
        ).json()

        display = data.get(
            "display_name",
            ""
        ).lower()

        if "forest" in display or "wood" in display:
            return "forest"

        elif "highway" in display:
            return "highway"

        elif "industrial" in display:
            return "industrial"

        elif "residential" in display:
            return "residential"

        else:
            return "commercial"

    except:

        return "unknown"


# =========================================================
# 🚔 POLICE DISTANCE
# =========================================================

def get_police_distance(lat, lon):

    query = f"""
    [out:json];
    node["amenity"="police"](around:5000,{lat},{lon});
    out;
    """

    try:

        res = requests.post(
            "https://overpass-api.de/api/interpreter",
            data=query,
            timeout=8
        ).json()

        if not res["elements"]:
            return 5

        distances = []

        for e in res["elements"]:

            police_loc = (
                e["lat"],
                e["lon"]
            )

            user_loc = (lat, lon)

            distances.append(
                geodesic(
                    user_loc,
                    police_loc
                ).km
            )

        return min(distances)

    except:

        return 5


# =========================================================
# 📈 CRIME DENSITY
# =========================================================

def get_crime_density(lat, lon):

    point = np.radians([[lat, lon]])

    radius = 1 / 6371

    density = tree.query_radius(
        point,
        r=radius,
        count_only=True
    )[0]

    return density


# =========================================================
# 🤖 MODEL II ZONE PREDICTION
# =========================================================

def model2_zone_prediction(lat, lon):

    if not MODEL2_AVAILABLE:
        return "unknown"

    try:

        features = [[lat, lon]]

        pred = zone_model.predict(features)

        zone = zone_encoder.inverse_transform(pred)[0]

        return zone

    except:

        return "unknown"


# =========================================================
# 🧠 FINAL HYBRID SAFETY DETECTOR
# =========================================================

def detect_zone_india(location_tuple):

    lat, lon = location_tuple

    night = get_night_factor()
    land_type = get_land_type(lat, lon)
    police_dist = get_police_distance(lat, lon)
    density = get_crime_density(lat, lon)

    model2_zone = model2_zone_prediction(lat, lon)

    # Population proxy
    population_map = {
        "residential": 1.0,
        "commercial": 0.8,
        "industrial": 0.6,
        "highway": 0.5,
        "forest": 0.2,
        "unknown": 0.5
    }

    population = population_map.get(land_type, 0.5)

    # Model II risk
    model2_map = {
        "residential": 0.2,
        "farmland": 0.5,
        "forest": 0.7,
        "industrial": 0.6,
        "greenfield": 0.4,
        "unknown": 0.5
    }

    model2_risk = model2_map.get(model2_zone, 0.5)

    # =====================================================
    # HYBRID RISK SCORE
    # =====================================================

    risk_score = (

        density * 0.7 +          # increased crime weight

        night * 1.5 +

        (1 - population) * 1.5 +

        (police_dist / 5) * 1.2 +

        model2_risk * 1.2
    )

    # =====================================================
    # SAFETY CLASSIFICATION
    # =====================================================

    if risk_score < 1.2:

        zone = "SAFE"

    elif 1.2 <= risk_score < 2.5:

        zone = "CAUTION"

    else:

        zone = "DANGER"


    # =====================================================
    # DEBUG OUTPUT
    # =====================================================

    print("\n====== SAFETOUR HYBRID ANALYSIS ======")
    print("Location:", lat, lon)
    print("Crime Density:", density)
    print("Land Type:", land_type)
    print("Night Factor:", night)
    print("Police Distance:", round(police_dist, 2), "km")
    print("Model II Zone:", model2_zone)
    print("Risk Score:", round(risk_score, 2))
    print("Predicted Zone:", zone)
    print("======================================\n")

    return zone
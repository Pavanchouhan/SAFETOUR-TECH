import joblib
import os

MODEL_PATH = os.path.join("models","best_model_random_forest_balanced.joblib")
ENCODER_PATH = os.path.join("models","label_encoder.pkl")

model = joblib.load(MODEL_PATH)
encoder = joblib.load(ENCODER_PATH)

def predict_zone(features):

    prediction = model.predict([features])
    zone = encoder.inverse_transform(prediction)[0]

    return zone
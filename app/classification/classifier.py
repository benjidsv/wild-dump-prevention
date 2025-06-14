import joblib, os

MODEL = None

def load_model():
    global MODEL
    if MODEL is None:
        MODEL = joblib.load(os.path.join(os.path.dirname(__file__), "../model.pkl"))
    return MODEL

def predict(features: dict):
    global MODEL
    return 'empty'
    #return MODEL.predict()
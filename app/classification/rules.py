def classify_image_by_rules(features: dict) -> str:
    if features["avg_r"] < 100 and features["file_size"] > 100000:
        return "full"
    return "empty"

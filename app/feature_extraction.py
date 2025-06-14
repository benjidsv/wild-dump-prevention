from PIL import Image as PILImage
import os

def extract_features(filepath):
    img = PILImage.open(filepath)
    width, height = img.size
    avg_color = img.convert("RGB").resize((1,1)).getpixel((0,0))
    file_size = os.path.getsize(filepath)

    return {
        "width": width,
        "height": height,
        "file_size": file_size,
        "avg_r": avg_color[0],
        "avg_g": avg_color[1],
        "avg_b": avg_color[2],
    }

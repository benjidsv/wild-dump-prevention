import cv2
import numpy as np
from PIL import Image
import os
from dataclasses import dataclass, asdict
from app.classification.rules_store import get_rules

@dataclass
class BinRules:
    edge_density      : float = 0.05
    texture_variance  : float = 500
    color_diversity   : int   = 800
    contour_count     : int   = 20
    brightness_low    : int   = 80
    brightness_high   : int   = 180
    saturation        : int   = 100
    file_size         : int   = 100_000
    full_score_thresh : int   = 4        # decision boundary


def classify_image_by_rules(image_path: str) -> str:
    rules_dict = get_rules()
    filtered = {k: rules_dict[k] for k in BinRules.__annotations__ if k in rules_dict}
    rules = BinRules(**filtered)

    try:
        # Load image using OpenCV
        img = cv2.imread(image_path)
        if img is None:
            return "empty"

        # Convert to RGB for PIL compatibility
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Load with PIL for additional processing
        pil_img = Image.open(image_path)

        # Get image dimensions
        height, width = img.shape[:2]

        # Convert to different color spaces for analysis
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Calculate various features
        features = {}

        # 1. Color analysis
        features['avg_brightness'] = np.mean(gray)
        features['brightness_std'] = np.std(gray)

        # 2. Edge detection (more edges might indicate clutter/fullness)
        edges = cv2.Canny(gray, 50, 150)
        features['edge_density'] = np.sum(edges > 0) / (height * width)

        # 3. Texture analysis using local binary patterns approximation
        features['texture_variance'] = cv2.Laplacian(gray, cv2.CV_64F).var()

        # 4. Color diversity (more colors might indicate more items)
        # Reduce colors to count unique combinations
        img_small = cv2.resize(img_rgb, (50, 50))
        unique_colors = len(np.unique(img_small.reshape(-1, 3), axis=0))
        features['color_diversity'] = unique_colors

        # 5. Saturation analysis (trash might have varied saturation)
        features['avg_saturation'] = np.mean(hsv[:, :, 1])

        # 6. Contour analysis (more contours might indicate more objects)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        features['contour_count'] = len(contours)

        # 7. File size as additional feature
        features['file_size'] = os.path.getsize(image_path)

        # Classification rules based on empirical analysis
        full_score = 0

        # High edge density suggests clutter
        if features['edge_density'] > rules.edge_density:
            full_score += 2

        # High texture variance suggests complex surfaces
        if features['texture_variance'] > rules.texture_variance:
            full_score += 2

        # High color diversity suggests multiple objects
        if features['color_diversity'] > rules.color_diversity:
            full_score += 1

        # Many contours suggest multiple objects
        if features['contour_count'] > rules.contour_count:
            full_score += 1

        # Medium brightness might indicate partially filled bins
        if rules.brightness_low < features['avg_brightness'] < rules.brightness_high:
            full_score += 1

        # High saturation might indicate colorful trash
        if features['avg_saturation'] > rules.saturation:
            full_score += 1

        # Large file size might indicate detailed/complex images
        if features['file_size'] > rules.file_size:
            full_score += 1

        # Classification decision
        if full_score >= rules.full_score_thresh:
            return "full"
        else:
            return "empty"

    except Exception as e:
        print(f"Error processing image {image_path}: {e}")
        return "empty"
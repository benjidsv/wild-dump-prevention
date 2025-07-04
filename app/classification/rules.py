import cv2
import numpy as np
from PIL import Image
import os


def classify_image_by_rules(image_path: str) -> str:
    """
    Classify trash bin as full or empty using OpenCV and PIL image processing.

    Args:
        image_path (str): Path to the image file

    Returns:
        str: "full" or "empty"
    """
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
        if features['edge_density'] > 0.05:
            full_score += 2

        # High texture variance suggests complex surfaces
        if features['texture_variance'] > 500:
            full_score += 2

        # High color diversity suggests multiple objects
        if features['color_diversity'] > 800:
            full_score += 1

        # Many contours suggest multiple objects
        if features['contour_count'] > 20:
            full_score += 1

        # Medium brightness might indicate partially filled bins
        if 80 < features['avg_brightness'] < 180:
            full_score += 1

        # High saturation might indicate colorful trash
        if features['avg_saturation'] > 100:
            full_score += 1

        # Large file size might indicate detailed/complex images
        if features['file_size'] > 100000:
            full_score += 1

        # Classification decision
        if full_score >= 4:
            return "full"
        else:
            return "empty"

    except Exception as e:
        print(f"Error processing image {image_path}: {e}")
        return "empty"
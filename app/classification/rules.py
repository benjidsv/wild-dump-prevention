import cv2
import numpy as np
from dataclasses import dataclass
from app.classification.rules_store import get_rules

@dataclass
class BinRules:
    dark_ratio       : float = 0.12
    edge_density     : float = 0.056
    contour_count    : int   = 8
    color_diversity  : int   = 120
    avg_saturation   : float = 0.50
    bright_ratio     : float = 0.01
    std_intensity    : float = 0.35
    entropy          : float = 7.00
    color_clusters   : int   = 3
    aspect_dev       : float = 0.40
    fill_ratio       : float = 0.85
    full_score_thresh: int   = 4

def extract_features(image_path: str):
    img = cv2.imread(image_path)
    if img is None:
        return None
    h, w = img.shape[:2]
    area = h * w

    # 1) HSV segment
    hsv       = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask_g    = cv2.inRange(hsv, (35,50,50), (85,255,255))
    mask_gray = cv2.inRange(hsv, (0,0,50),   (180,40,200))
    mask      = cv2.bitwise_or(mask_g, mask_gray)

    # 2) Clean up
    kern = cv2.getStructuringElement(cv2.MORPH_RECT, (15,15))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kern)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  kern)

    # 3) Find bin contour
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None
    bin_cnt = max(cnts, key=cv2.contourArea)
    if cv2.contourArea(bin_cnt) < 0.02 * area:
        return None

    # 4) Crop ROI + mask
    x,y,bw,bh = cv2.boundingRect(bin_cnt)
    roi       = img[y:y+bh, x:x+bw]
    roi_mask  = mask[y:y+bh, x:x+bw]
    if roi.size == 0:
        return None

    # 5) Grayscale & edges
    gray  = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50,150)
    a2    = gray.shape[0] * gray.shape[1]

    # base features
    dark_ratio    = np.sum(gray < 80) / a2
    edge_density  = np.sum(edges > 0) / a2
    cnts2, _      = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contour_count = len(cnts2)
    small         = cv2.resize(roi, (50,50))
    color_div     = int(len(np.unique(small.reshape(-1,3), axis=0)))

    # new features
    hsv_roi       = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    avg_sat       = float(np.mean(hsv_roi[:,:,1]))/255.0
    bright_ratio  = float(np.sum(gray>180))/a2
    std_int       = float(np.std(gray))/255.0

    # entropy
    hist          = cv2.calcHist([gray],[0],None,[256],[0,256]).ravel()
    hn            = hist/(hist.sum()+1e-6)
    entropy       = -float(np.sum(hn*np.log2(hn+1e-6)))

    # color clusters (k=3)
    pix           = roi.reshape(-1,3).astype(np.float32)
    term_crit     = (cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_MAX_ITER, 10,1.0)
    _,labels,_    = cv2.kmeans(pix,3,None,term_crit,1,cv2.KMEANS_RANDOM_CENTERS)
    counts        = np.bincount(labels.flatten(),minlength=3)/pix.shape[0]
    color_clusters= int(np.sum(counts>0.05))

    # aspect deviation (empty AR≈1)
    aspect_dev    = abs((bw/float(bh)) - 1.0)

    # fill ratio
    fill_ratio    = float(np.sum((roi_mask>0)&(gray<250))) / (np.sum(roi_mask>0)+1e-6)

    return {
      "dark_ratio":      dark_ratio,
      "edge_density":    edge_density,
      "contour_count":   contour_count,
      "color_diversity": color_div,
      "avg_saturation":  avg_sat,
      "bright_ratio":    bright_ratio,
      "std_intensity":   std_int,
      "entropy":         entropy,
      "color_clusters":  color_clusters,
      "aspect_dev":      aspect_dev,
      "fill_ratio":      fill_ratio,
    }

def classify_image_by_rules(image_path: str) -> (str, dict):
    # load thresholds
    rules_dict = get_rules()
    # filter to only fields we need
    init = {k: rules_dict[k] for k in BinRules.__annotations__ if k in rules_dict}
    rules = BinRules(**init)

    feat = extract_features(image_path)
    if feat is None:
        return "empty"

    score = 0
    score += 2 if feat["dark_ratio"]      > rules.dark_ratio       else 0
    score += 1 if feat["edge_density"]    > rules.edge_density     else 0
    score += 1 if feat["contour_count"]   > rules.contour_count    else 0
    score += 1 if feat["color_diversity"] > rules.color_diversity  else 0
    score += 1 if feat["avg_saturation"]  > rules.avg_saturation   else 0
    score += 1 if feat["bright_ratio"]    < rules.bright_ratio     else 0
    score += 1 if feat["std_intensity"]   > rules.std_intensity    else 0
    score += 1 if feat["entropy"]         > rules.entropy          else 0
    score += 1 if feat["color_clusters"]  >= rules.color_clusters  else 0
    score += 1 if feat["aspect_dev"]      > rules.aspect_dev       else 0
    score += 1 if feat["fill_ratio"]      < rules.fill_ratio       else 0

    return ("full" if score >= rules.full_score_thresh else "empty"), feat

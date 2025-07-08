"""
Central place to load / save the bin-classification thresholds.
No other code, so nothing here depends on Flask routes.
"""
import json, pathlib, threading
from typing import Dict, Any

RULES_PATH   = pathlib.Path(__file__).with_name("rules.json")
_lock        = threading.RLock()
_cache: Dict[str, Any] | None = None
_mtime: float | None = None

DEFAULTS = {
    "dark_ratio"       : 0.12,
    "edge_density"     : 0.056,
    "contour_count"    : 8,
    "color_diversity"  : 120,
    "avg_saturation"   : 0.50,
    "bright_ratio"     : 0.01,
    "std_intensity"    : 0.35,
    "entropy"          : 7.00,
    "color_clusters"   : 3,
    "aspect_dev"       : 0.40,
    "fill_ratio"       : 0.85,
    "full_score_thresh": 4
}

def _touch_file_with_defaults() -> None:
    RULES_PATH.write_text(json.dumps(DEFAULTS, indent=2))

def get_rules() -> Dict[str, Any]:
    """Return the latest rules, auto-reloading when the file changes."""
    global _cache, _mtime
    with _lock:
        if not RULES_PATH.exists():
            _touch_file_with_defaults()

        mtime = RULES_PATH.stat().st_mtime
        if _cache is None or mtime != _mtime:
            _cache = json.loads(RULES_PATH.read_text())
            _mtime = mtime
        return _cache

def save_rules(new_rules: Dict[str, Any]) -> None:
    with _lock:
        RULES_PATH.write_text(json.dumps(new_rules, indent=2))
        # force reload on next get_rules()
        global _cache, _mtime
        _cache, _mtime = None, None

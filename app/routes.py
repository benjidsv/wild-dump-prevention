import time
import uuid

import cv2
from flask import Blueprint, render_template, request, redirect, url_for, current_app, flash, session, abort, jsonify
from geopy.exc import GeocoderServiceError, GeocoderTimedOut
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename
import os
from app.classification.rules import classify_image_by_rules
from app.classification.rules_store import get_rules, save_rules
from app.db.models import Image, User, Location
from app.extensions import database
from datetime import datetime
from PIL import Image as PILImage
from PIL.ExifTags import TAGS, GPSTAGS
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from geopy.geocoders import Nominatim

import json, pathlib, threading
from typing import Dict, Any

RULES_PATH   = pathlib.Path(__file__).with_name("rules.json")
_rules_lock  = threading.RLock()
_rules_cache: Dict[str, Any] | None = None
_rules_mtime: float | None = None

def _reload_rules_if_needed() -> Dict[str, Any]:
    """Return latest rules; reload from disk if file changed or first call."""
    global _rules_cache, _rules_mtime
    with _rules_lock:
        try:
            mtime = RULES_PATH.stat().st_mtime
        except FileNotFoundError:
            # Create file with sensible defaults the first time
            defaults = {
                "edge_density"      : 0.05,
                "texture_variance"  : 500,
                "color_diversity"   : 800,
                "contour_count"     : 20,
                "brightness_low"    : 80,
                "brightness_high"   : 180,
                "avg_saturation"    : 100,
                "file_size"         : 100_000,
                "full_score_thresh" : 4
            }
            RULES_PATH.write_text(json.dumps(defaults, indent=2))
            _rules_cache, _rules_mtime = defaults, RULES_PATH.stat().st_mtime
            return defaults

        if _rules_cache is None or mtime != _rules_mtime:
            _rules_cache  = json.loads(RULES_PATH.read_text())
            _rules_mtime  = mtime
        return _rules_cache

def str_to_bool(val: str | None) -> bool:
    return (val or "").lower() == "true"

def extract_exif_location(image_path):
    img = PILImage.open(image_path)
    exif_data = img._getexif()
    if not exif_data:
        return None

    gps_info = {}
    for tag, value in exif_data.items():
        tagname = TAGS.get(tag)
        if tagname == "GPSInfo":
            for key in value:
                gps_info[GPSTAGS.get(key)] = value[key]

    if gps_info.get("GPSLatitude") and gps_info.get("GPSLongitude"):
        # convert GPS coordinates to decimal degrees
        def dms_to_dd(dms, ref):
            degrees, minutes, seconds = dms
            dd = degrees + minutes / 60 + seconds / 3600
            return dd if ref in ["N", "E"] else -dd

        lat = dms_to_dd(gps_info["GPSLatitude"], gps_info["GPSLatitudeRef"])
        lon = dms_to_dd(gps_info["GPSLongitude"], gps_info["GPSLongitudeRef"])
        return f"{lat:.6f},{lon:.6f}"

    return None

def extract_exif_timestamp(image_path):
        img = PILImage.open(image_path)
        exif = img._getexif()
        if not exif:
            return None

        for tag, value in exif.items():
            decoded = TAGS.get(tag)
            if decoded == "DateTimeOriginal":
                return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")

        return None

def add_image_to_db(filename, address, timestamp_str, label, label_manual, timestamp_manual, address_manual, features, address_is_location = False):
    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M")

    if address_is_location:
        location = address
    else:
        # If the location is already in the db, no need to recreate
        location = (
            Location.query.filter_by(address=address).first()
            if address else None
        )

        # Else geocode it
        if not location and address:
            geolocator = Nominatim(user_agent="wdp/1.0", timeout=5)
            try:
                # Nominatim courtesy delay: 1 req/sec max from one client
                time.sleep(1.1)
                loc = geolocator.geocode(address, exactly_one=True)
            except GeocoderServiceError:
                print("GeocoderServiceError")
                loc = None

            lat = float(loc.latitude) if loc else None
            lon = float(loc.longitude) if loc else None

            location = Location(address=address, latitude=lat, longitude=lon)

    database.session.add(location)
    database.session.flush()

    for key in features:
        features[key] = float(features[key])

    img = Image(
        path=os.path.join(current_app.config["UPLOAD_FOLDER"], filename),
        label=label,
        timestamp=timestamp,
        location=location,
        user_id=session.get("user_id"),
        label_manual=label_manual,
        timestamp_manual=timestamp_manual,
        location_manual=address_manual,

        dark_ratio=features["dark_ratio"],
        edge_density=features["edge_density"],
        contour_count=features["contour_count"],
        color_diversity=features["color_diversity"],
        avg_saturation=features["avg_saturation"],
        bright_ratio=features["bright_ratio"],
        std_intensity=features["std_intensity"],
        entropy=features["entropy"],
        color_clusters=features["color_clusters"],
        aspect_dev=features["aspect_dev"],
        fill_ratio=features["fill_ratio"],
    )
    database.session.add(img)
    database.session.commit()

# --------- Décorateur pour accès admin ---------
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            flash("Veuillez vous connecter pour accéder à cette page.", "warning")
            return redirect(url_for("main.login"))

        user = User.query.get(user_id)
        if not user or not user.is_admin:
            # Page dédiée d'accès refusé avec redirection automatique
            return render_template("unauthorized.html"), 403

        return f(*args, **kwargs)

    return decorated_function

def superadmin_required(f):
    @wraps(f)
    def decorated_function(*a, **kw):
        user_id = session.get("user_id")
        if not user_id:
            flash("Veuillez vous connecter pour accéder à cette page.", "warning")
            return redirect(url_for("main.login"))

        user = User.query.get(user_id)
        if not user or not user.is_superadmin:
            return render_template("unauthorized.html"), 403

        return f(*a, **kw)

    return decorated_function

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            flash("Veuillez vous connecter pour accéder à cette page.", "warning")
            return redirect(url_for("main.login"))

        user = User.query.get(user_id)
        if not user:
            return render_template("unauthorized.html"), 403

        return f(*args, **kwargs)

    return decorated_function

main = Blueprint('main', __name__)
@main.app_context_processor
def inject_current_user():
    uid = session.get("user_id")
    return {"current_user": User.query.get(uid) if uid else None}

@main.app_context_processor
def inject_image_count():
    id = session.get("user_id")
    if id:
        image_count = (
            database.session.query(func.count(Image.id))
            .filter(Image.user_id == id)
            .scalar()
        )
    else:
        image_count = 0
    return dict(image_count=image_count)

@main.route("/")
def index():
    return redirect(url_for("main.dashboard"))

@main.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    print("post upload")
    user = User.query.get(session["user_id"])  # we know it exists

    # ------------------------ GET ------------------------ #
    if request.method == "GET":
        images = (
            Image.query.all()                              # admin sees everything
            if user.is_admin
            else Image.query.filter_by(user_id=user.id).all()  # regular user → only own photos
        )
        return render_template("upload.html", images=images)

    # ----------------------- POST ------------------------ #
    if not user.is_admin:
        # Block non-admin POST attempts (403 Forbidden)
        return render_template("unauthorized.html"), 403

    if 'images' in request.files:
        # We're uploading multiple images
        files = request.files.getlist('images')
        filenames = []
        labels = []
        timestamps = []
        locations = []
        feats = []
        for file in files:
            filename = secure_filename(file.filename)
            filenames.append(filename)
            filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)

            # Feature extraction
            label_auto, features = classify_image_by_rules(filepath)
            labels.append(label_auto)
            feats.append(features)
            exif_timestamp = extract_exif_timestamp(filepath)
            timestamp = exif_timestamp or datetime.utcnow()
            timestamps.append(timestamp.strftime("%Y-%m-%dT%H:%M"))
            location = extract_exif_location(filepath) or ""
            locations.append(location)

        # We render the confirm step for multiple images
        return render_template("confirm_upload_multiple.html",
        filenames=filenames,
        auto_labels=labels,
        auto_timestamps=timestamps,
        auto_locations=locations,
                               feats=feats
    )

    if 'video' in request.files:
        video_file = request.files["video"]
        if not video_file:
            flash("Aucun fichier", "danger")
            return redirect(request.url)

        filename = secure_filename(video_file.filename)
        filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        video_file.save(filepath)

        # On montre maintenant le lecteur vidéo
        return render_template(
            "select_timestamps.html",
            video_filename=filename
        )

    # We're uploading one image
    file = request.files["image"]
    filename = secure_filename(file.filename)
    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    # Feature extraction
    label_auto, features = classify_image_by_rules(filepath)
    exif_timestamp = extract_exif_timestamp(filepath)
    timestamp = exif_timestamp or datetime.utcnow()
    location = extract_exif_location(filepath) or ""

    # Render confirm step for one image
    return render_template("confirm_upload.html",
        filename=filename,
        auto_label=label_auto,
        default_timestamp=timestamp.strftime("%Y-%m-%dT%H:%M"),
        auto_location=location,
        features=features,
    )

@main.route("/confirm", methods=["POST"])
@admin_required
def confirm_upload():
    print("post confirm upload")
    filename = request.form.get("filename")
    label = request.form.get("label")
    timestamp_str = request.form.get("timestamp")
    address = request.form.get("location").strip()
    label_manual = str_to_bool(request.form.get("label_manual"))
    timestamp_manual = str_to_bool(request.form.get("timestamp_manual"))
    address_manual = str_to_bool(request.form.get("location_manual").strip())
    features = request.form.get("features")

    add_image_to_db(filename, address, timestamp_str, label, label_manual, timestamp_manual, address_manual, features)

    flash("Image enregistrée !", "success")

    return redirect(url_for("main.upload"))

@main.route("/confirm_multiple", methods=["POST"])
@admin_required
def confirm_upload_multiple():
    filenames = request.form.getlist("filenames")

    for idx, filename in enumerate(filenames):
        label          = request.form.get(f"label_{idx}")
        ts_str         = request.form.get(f"timestamp_{idx}") or ""
        address        = request.form.get(f"location_{idx}")  or ""
        features = request.form.get(f"features_{idx}")

        # --- convert provenance flags to real booleans -------------
        label_manual   = str_to_bool(request.form.get(f"label_manual_{idx}"))
        ts_manual      = str_to_bool(request.form.get(f"timestamp_manual_{idx}"))
        loc_manual     = str_to_bool(request.form.get(f"location_manual_{idx}"))

        add_image_to_db(filename, address, ts_str, label, label_manual, ts_manual, loc_manual, features)


    flash("Images enregistrées !", "success")
    return redirect(url_for("main.upload"))

@main.route("/user_upload")
@login_required          # or @admin_required if only admins can use it
def user_upload():
    return render_template("capture_upload.html")

def lat_lon_from_string(latlon_str):
    lat, lon = latlon_str.split(",")
    lat = float(lat)
    lon = float(lon)

    return lat, lon

@main.route("/quick_upload", methods=["POST"])
@login_required
def quick_upload():
    print("quick upload")
    file = request.files.get("image")
    print("got image")
    if not file:
        flash("Erreur : aucune image reçue.", "danger")
        return redirect(url_for("main.upload"))

    filename  = secure_filename(file.filename)
    filepath  = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)
    print("saved image")

    # Auto-label from rules
    label_auto, features = classify_image_by_rules(filepath)
    print("got label")

    # Values provided by the client (timestamp already ISO-ish)
    timestamp_str = request.form.get("timestamp")
    # The form passes a "lat, lon" string
    # --- 1. make the form field required, early exit if missing --------------
    location_raw = (request.form.get("location") or "").strip()
    if not location_raw:
        flash("Coordonnées manquantes 📍", "danger")
        return redirect(url_for("main.upload"))

    # --- 2. parse it *before* giving anything to geopy -----------------------
    try:
        lat, lon = map(float, location_raw.split(","))
    except ValueError:
        flash("Format attendu : latitude,longitude", "danger")
        return redirect(url_for("main.upload"))

    geolocator = Nominatim(user_agent="wdp/1.0", timeout=5)
    try:
        # supply a *tuple* so geopy never tries to re-parse a string
        geo = geolocator.reverse((lat, lon), exactly_one=True)
        address = geo.address if geo else "Adresse inconnue"
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        current_app.logger.warning(f"reverse-geocode failed: {e}")
        address = "Adresse inconnue"

    location = Location(address = address, latitude = lat, longitude = lon)

    add_image_to_db(filename, location, timestamp_str, label_auto, False, False, False, features, True)
    flash("Image enregistrée !", 'success')
    return redirect(url_for("main.upload"))


@main.route("/extract_from_video", methods=["POST"])
@admin_required
def extract_from_video():
    video_name = request.args.get("video")
    ts_list = [float(t) for t in request.form.getlist("timestamps")]

    video_path = os.path.join(current_app.config["UPLOAD_FOLDER"], video_name)
    cap = cv2.VideoCapture(video_path)
    saved_frames, labels, timestamps, locations = [], [], [], []

    for sec in ts_list:
        cap.set(cv2.CAP_PROP_POS_MSEC, sec * 1000)
        ok, frame = cap.read()
        if not ok:
            continue
        img_name = f"frame_{uuid.uuid4().hex}.jpg"
        img_path = os.path.join(current_app.config['UPLOAD_FOLDER'], img_name)
        cv2.imwrite(img_path, frame)
        saved_frames.append(img_name)

        # Auto-détection pour chaque frame
        labels.append(classify_image_by_rules(img_path))
        ts_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M")
        timestamps.append(ts_iso)
        locations.append("")   # ou ta fonction EXIF si besoin

    cap.release()

    # On réutilise ton template multiple
    return render_template(
        "confirm_upload_multiple.html",
        filenames=saved_frames,
        auto_labels=labels,
        auto_timestamps=timestamps,
        auto_locations=locations
    )

@main.route("/delete_image/<int:image_id>", methods=["POST"])
@login_required
def delete_image(image_id):
    img = Image.query.get_or_404(image_id)
    user = User.query.get(session["user_id"])

    # --- permission check ---
    if not (user.is_admin or img.user_id == user.id):
        return render_template("unauthorized.html"), 403

    # --- delete file from disk
    try:
        os.remove(img.path)
    except OSError:
        pass  # file already gone / cannot delete -> ignore

    # --- delete DB row ---
    database.session.delete(img)
    database.session.commit()

    flash("Image supprimée.",'success')
    return redirect(url_for("main.upload"))

@main.route("/edit_image/<int:image_id>")
@admin_required
def edit_image(image_id):
    img = Image.query.get_or_404(image_id)

    return render_template(
        "confirm_upload.html",        # same template!
        edit_mode=True,               # flag
        image_id=img.id,
        filename=img.path.split("/")[-1],  # for <img src>
        auto_label=img.label or "full",
        auto_timestamp=img.timestamp.strftime("%Y-%m-%dT%H:%M"),
        auto_location=img.location.address if img.location else "",
    )

@main.route("/update_image", methods=["POST"])
@admin_required
def update_image():
    img = Image.query.get_or_404(int(request.form["image_id"]))
    changed = False                     # track if anything actually modified

    # ---------- LABEL ----------
    new_label = request.form.get("label")
    if new_label and new_label != img.label:
        img.label = new_label
        img.label_manual = True
        changed = True

    # ---------- TIMESTAMP ----------
    ts_str = request.form.get("timestamp")
    if ts_str:
        try:
            ts = datetime.strptime(ts_str, "%Y-%m-%dT%H:%M")
            if ts != img.timestamp:
                img.timestamp = ts
                img.timestamp_manual = True
                changed = True
        except ValueError:
            flash("Horodatage invalide : modification ignorée.",'warning')

    # ---------- LOCATION ----------
    address = (request.form.get("location") or "").strip()
    if address and (not img.location or img.location.address != address):
        # reuse existing row if same addr already in DB
        loc = Location.query.filter_by(address=address).first()
        if not loc:
            geolocator = Nominatim(user_agent="wdp/1.0", timeout=5)
            try:
                geo = geolocator.geocode(address, exactly_one=True)
            except GeocoderServiceError:
                geo = None
            lat = geo.latitude if geo else None
            lon = geo.longitude if geo else None
            loc = Location(address=address, latitude=lat, longitude=lon)
            database.session.add(loc)
            database.session.flush()
        img.location = loc
        img.location_manual = True
        changed = True

    # ---------- COMMIT ----------
    if changed:
        database.session.commit()
        flash("Image mise à jour.", 'success')
    else:
        flash("Aucune modification détectée.", 'warning')

    return redirect(url_for("main.upload"))


@main.route("/dashboard")
def dashboard():
    start_date_str   = request.args.get("start_date")
    end_date_str     = request.args.get("end_date")
    location_filter  = request.args.get("location")

    # -------------------------------------------------- #
    # Base query (eager-load Location to avoid N+1)
    # -------------------------------------------------- #
    query = (
        Image.query
        .options(joinedload(Image.location))
        .filter(Image.location_id.isnot(None))          # only images with a location row
    )

    # ---------------- Date filter --------------------- #
    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            end_date   = datetime.strptime(end_date_str,   "%Y-%m-%d")
            query = query.filter(
                Image.timestamp.between(start_date, end_date)
            )
        except ValueError:
            pass  # silently ignore bad date format

    # ---------------- Address filter ------------------ #
    if location_filter:
        query = (
            query.join(Image.location)
                 .filter(Location.address.ilike(f"%{location_filter}%"))
        )

    # -------------- Pie-chart stats ------------------- #
    label_counts = (
        query.with_entities(Image.label, func.count(Image.id))
             .group_by(Image.label)
             .all()
    )
    stats = {"full": 0, "empty": 0}
    for label, count in label_counts:
        if label == "full":
            stats["full"]  = count
        elif label == "empty":
            stats["empty"] = count

    # ------------- Distinct addresses ----------------- #
    all_locations = (
        database.session.query(Location.address)
        .join(Image)
        .distinct()
        .order_by(Location.address)
        .all()
    )
    all_locations = [addr for (addr,) in all_locations]

    # ------------- Map markers ------------------------ #
    locations_coords = []
    for img in query:                          # already filtered & eager-loaded
        loc = img.location
        if loc and loc.latitude is not None and loc.longitude is not None:
            locations_coords.append({
                "lat":  float(loc.latitude),
                "lon":  float(loc.longitude),
                "label": img.label or "non défini"
            })

    from collections import defaultdict
    tile = lambda v: round(v, 2)  # 0.01° ≈ 1 km

    grid = defaultdict(lambda: {"full": 0, "total": 0, "lat": 0, "lon": 0})

    for loc in locations_coords:  # ← already filtered list
        lt, ln = tile(loc["lat"]), tile(loc["lon"])
        key = (lt, ln)
        bucket = grid[key]
        bucket["total"] += 1
        if loc["label"] == "full":
            bucket["full"] += 1
        bucket["lat"], bucket["lon"] = lt, ln  # keep centre

    # convert to list the template can "tojson"
    danger_zones = [
        {
            "lat": b["lat"],
            "lon": b["lon"],
            "ratio": b["full"] / b["total"]  # 0 → green, 1 → dark-red
        }
        for b in grid.values() if b["total"] >= 3  # ignore tiny samples
    ]

    return render_template(
        "dashboard.html",
        stats=stats,
        locations=all_locations,
        locations_coords=locations_coords,
        danger_zones=danger_zones,
    )
@main.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        # Hash du mot de passe
        hashed_password = generate_password_hash(password)

        # Vérifie d'abord l'adresse mail, puis le nom d'utilisateur pour fournir un message précis
        existing_email = User.query.filter_by(mail=email).first()
        if existing_email:
            error_msg = "Cette adresse mail est déjà utilisée."
            flash(error_msg, "danger")
            return render_template("register.html", error=error_msg, name=name, email=email)

        existing_username = User.query.filter_by(name=name).first()
        if existing_username:
            error_msg = "Ce nom d'utilisateur est déjà pris."
            flash(error_msg, 'danger')
            return render_template("register.html", error=error_msg, name=name, email=email)

        # Création de l'utilisateur
        user = User(name=name, mail=email, password=hashed_password, is_admin=False)
        database.session.add(user)
        database.session.commit()

        # Connexion automatique après création du compte
        session["user_id"] = user.id
        flash("Compte créé et connecté avec succès !", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("register.html")

@main.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # Priorité 1 : vérifier si l'adresse mail existe
        user = User.query.filter_by(mail=email).first()
        if not user:
            error_msg = "Adresse mail inconnue."
            flash(error_msg, 'danger')
            return render_template("login.html", error=error_msg, email=email)

        # Priorité 2 : vérifier le mot de passe si l'email est valide
        if not check_password_hash(user.password, password):
            error_msg = "Mot de passe incorrect."
            flash(error_msg,  'danger')
            return render_template("login.html", error=error_msg, email=email)

        # Succès
        session["user_id"] = user.id
        flash("Connexion réussie !", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("login.html")

@main.route("/logout")
def logout():
    session.pop("user_id", None)   # forget who was logged-in
    flash("Vous êtes maintenant déconnecté·e.", "success")
    return redirect(url_for("main.dashboard"))

@main.route("/admin/users")
@admin_required
def admin_dashboard():
    users = User.query.order_by(User.id).all()
    return render_template("admin_dashboard.html", users=users)

@main.route("/admin/users/<int:user_id>/toggle-admin", methods=["POST"])
@superadmin_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == session.get("user_id"):
        flash("Vous ne pouvez pas modifier votre propre rôle.", "warning")
    else:
        user.is_admin = not user.is_admin
        database.session.commit()
        flash("Rôle mis à jour.", "success")
    return redirect(url_for("main.admin_dashboard"))

@main.route("/admin/users/<int:user_id>/delete", methods=["POST"])
@superadmin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_superadmin:
        flash("Impossible de supprimer le super-admin.", "danger")
    else:
        database.session.delete(user)
        database.session.commit()
        flash("Compte supprimé.", "success")
    return redirect(url_for("main.admin_dashboard"))

@main.route("/rules", methods=["GET"])
@admin_required
def rules_get():
    return jsonify(get_rules()), 200

@main.route("/rules/edit", methods=["GET", "POST"])
@admin_required
def rules_edit():
    if request.method == "POST":
        incoming = request.form.to_dict()
        schema = {
          "DARK_RATIO_TH": float,
          "EDGE_DENSITY_TH": float,
          "CONTOUR_COUNT_TH": int,
          "COLOR_DIVERSITY_TH": int,
          "SAT_MEAN_TH": float,
          "BRIGHT_RATIO_TH": float,
          "STD_INTENSITY_TH": float,
          "ENTROPY_TH": float,
          "COLOR_CLUSTERS_TH": int,
          "ASPECT_DEV_TH": float,
          "FILL_RATIO_TH": float,
          "FULL_SCORE_THRESH": int
        }

        try:
            cleaned = {k: schema[k](incoming[k]) for k in schema}
        except Exception as e:
            flash(f"Champ invalide : {e}", "warning")
            return redirect(request.url)

        save_rules(cleaned)
        flash("Règles mises à jour !", "success")
        return redirect(url_for("main.rules_edit"))

    return render_template("rules_editor.html", rules=get_rules())

# --- POST séparé pour tester une image ------------------------------------
@main.route("/rules/test", methods=["POST"])
@admin_required
def rules_test():
    if 'test_image' not in request.files or request.files['test_image'].filename == '':
        flash("Choisissez un fichier à tester.", "warning")
        return redirect(url_for('main.rules_edit'))

    f = request.files['test_image']
    fname = secure_filename(f.filename)
    tmp   = os.path.join(current_app.config['UPLOAD_FOLDER'], 'tmp', f"{uuid.uuid4()}_{fname}")
    os.makedirs(os.path.dirname(tmp), exist_ok=True)
    f.save(tmp)

    result = classify_image_by_rules(tmp)   # ⇒ 'full' ou 'empty'
    os.remove(tmp)

    flash(f"Résultat : {result}", "success")
    return redirect(url_for('main.rules_edit', _anchor='result'))

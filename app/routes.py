import time
import uuid

import cv2
from flask import Blueprint, render_template, request, redirect, url_for, current_app, flash, session
from geopy.exc import GeocoderServiceError
from geopy.extra.rate_limiter import RateLimiter
from sqlalchemy import func
from werkzeug.utils import secure_filename
import os
from app.classification.rules import classify_image_by_rules
from app.db.models import Image, User, Location
from app.extensions import db
from datetime import datetime
from PIL import Image as PILImage
from PIL.ExifTags import TAGS, GPSTAGS
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from geopy.geocoders import Nominatim

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

def add_image_to_db(filename, address, timestamp_str, label, is_manual):
    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M")

    # If the location is already in the db, no need to recreate
    location = (
        Location.query.filter_by(address=address).first()
        if address else None
    )

    # Else geocode it
    if not location and address:
        geolocator = Nominatim(user_agent="wild-dump-prevention/1.0", timeout=5)
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
        db.session.add(location)
        db.session.flush()

    img = Image(
        path=os.path.join(current_app.config["UPLOAD_FOLDER"], filename),
        label=label,
        is_manual=is_manual,
        timestamp=timestamp,
        location=location,
        user_id=session.get("user_id")
    )
    db.session.add(img)
    db.session.commit()


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

main = Blueprint('main', __name__)
@main.route("/")
def index():
    return redirect(url_for("main.dashboard"))

@main.route("/upload", methods=["GET", "POST"])
@admin_required
def upload():
    if request.method == "POST":
        print("post upload")
        if 'images' in request.files:
            # We're uploading multiple images
            files = request.files.getlist('images')
            filenames = []
            labels = []
            timestamps = []
            locations = []
            for file in files:
                filename = secure_filename(file.filename)
                filenames.append(filename)
                filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
                file.save(filepath)

                # Feature extraction
                label_auto = classify_image_by_rules(filepath)
                labels.append(label_auto)
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
            auto_locations=locations
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
        label_auto = classify_image_by_rules(filepath)
        exif_timestamp = extract_exif_timestamp(filepath)
        timestamp = exif_timestamp or datetime.utcnow()
        location = extract_exif_location(filepath) or ""

        # Render confirm step for one image
        return render_template("confirm_upload.html",
            filename=filename,
            auto_label=label_auto,
            default_timestamp=timestamp.strftime("%Y-%m-%dT%H:%M"),
            auto_location=location
        )

    # GET: show upload form and list of saved images
    print("get upload")
    images = Image.query.all()
    return render_template("upload.html", images=images)

@main.route("/confirm", methods=["POST"])
@admin_required
def confirm_upload():
    print("post confirm upload")
    filename = request.form.get("filename")
    label = request.form.get("label")
    is_manual = request.form.get("is_manual") == "true"
    timestamp_str = request.form.get("timestamp")
    address = request.form.get("location").strip()

    add_image_to_db(filename, address, timestamp_str, label, is_manual)

    return redirect(url_for("main.upload"))

@main.route("/confirm_multiple", methods=["POST"])
@admin_required
def confirm_upload_multiple():
    print("post confirm upload multiple")

    filenames = request.form.getlist("filenames")
    for idx, filename in enumerate(filenames):
        # ---- form values ---------------------------------------------------
        label = request.form.get(f"label_{idx}")  # "full" / "empty"
        is_manual = request.form.get(f"is_manual_{idx}") == "true"
        timestamp_str = request.form.get(f"timestamp_{idx}") or ""  # may be ""
        address = request.form.get(f"location_{idx}") or ""

        add_image_to_db(filename, address, timestamp_str, label, is_manual)

    # 2) one commit for all rows
    db.session.commit()
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

@main.route("/annotate/<int:image_id>", methods=["GET", "POST"])
def annotate(image_id):
    from app.db.models import Image
    image = Image.query.get_or_404(image_id)

    if request.method == "POST":
        label = request.form["label"]
        image.label = label
        db.session.commit()
        return redirect(url_for("main.upload"))

    return render_template("annotate.html", image=image)

@main.route("/dashboard")
def dashboard():
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")
    location_filter = request.args.get("location")

    query = Image.query

    # Appliquer les filtres de date
    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
            query = query.filter(Image.timestamp >= start_date, Image.timestamp <= end_date)
        except ValueError:
            pass

    # Filtrer par localisation partielle (texte)
    if location_filter:
        query = query.filter(Image.location.ilike(f"%{location_filter}%"))

    # Calcul des stats pour le graphique camembert
    label_counts = (
        query.with_entities(Image.label, func.count(Image.id))
        .group_by(Image.label)
        .all()
    )

    stats = {"full": 0, "empty": 0}
    for label, count in label_counts:
        if label == "full":
            stats["full"] = count
        elif label == "empty":
            stats["empty"] = count

    # Liste distincte des localisations pour un éventuel filtre/déploiement UI
    all_locations = [r[0] for r in db.session.query(Image.location).distinct().all() if r[0]]

    # Récupérer les images filtrées avec localisation non nulle
    images_filtered = query.filter(Image.location is not None).all()

    locations_coords = []
    for img in images_filtered:
        if img.location:
            try:
                lat_str, lon_str = img.location.split(",")
                lat, lon = float(lat_str), float(lon_str)
                locations_coords.append({
                    "lat": lat,
                    "lon": lon,
                    "label": img.label or "non défini"
                })
            except Exception:
                # En cas d'erreur dans le format GPS, on ignore
                continue

    print(stats)
    print(all_locations)
    return render_template("dashboard.html", stats=stats, locations=all_locations, locations_coords=locations_coords)

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
            flash(error_msg, "danger")
            return render_template("register.html", error=error_msg, name=name, email=email)

        # Création de l'utilisateur
        user = User(name=name, mail=email, password=hashed_password, is_admin=True)
        db.session.add(user)
        db.session.commit()

        flash("Compte créé avec succès ! Veuillez vous connecter.", "success")
        return redirect(url_for("main.login"))

    return render_template("register.html")

@main.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(mail=email).first()
        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            flash("Connexion réussie !", "success")
            return redirect(url_for("main.dashboard"))

        error_msg = "Email ou mot de passe incorrect."
        flash(error_msg, "danger")
        return render_template("login.html", error=error_msg, email=email)

    return render_template("login.html")

import time
import uuid

import cv2
from flask import Blueprint, render_template, request, redirect, url_for, current_app, flash, session
from geopy.exc import GeocoderServiceError
from geopy.extra.rate_limiter import RateLimiter
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename
import os
from app.classification.rules import classify_image_by_rules
from app.db.models import Image, User, Location
from app.extensions import database
from datetime import datetime
from PIL import Image as PILImage
from PIL.ExifTags import TAGS, GPSTAGS
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from geopy.geocoders import Nominatim

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

def add_image_to_db(filename, address, timestamp_str, label, label_manual, timestamp_manual, address_manual, address_is_location = False):
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

    img = Image(
        path=os.path.join(current_app.config["UPLOAD_FOLDER"], filename),
        label=label,
        timestamp=timestamp,
        location=location,
        user_id=session.get("user_id"),
        label_manual=label_manual,
        timestamp_manual=timestamp_manual,
        location_manual=address_manual,
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

    add_image_to_db(filename, address, timestamp_str, label, label_manual, timestamp_manual, address_manual)

    return redirect(url_for("main.upload"))

@main.route("/confirm_multiple", methods=["POST"])
@admin_required
def confirm_upload_multiple():
    filenames = request.form.getlist("filenames")

    for idx, filename in enumerate(filenames):
        label          = request.form.get(f"label_{idx}")
        ts_str         = request.form.get(f"timestamp_{idx}") or ""
        address        = request.form.get(f"location_{idx}")  or ""

        # --- convert provenance flags to real booleans -------------
        label_manual   = str_to_bool(request.form.get(f"label_manual_{idx}"))
        ts_manual      = str_to_bool(request.form.get(f"timestamp_manual_{idx}"))
        loc_manual     = str_to_bool(request.form.get(f"location_manual_{idx}"))

        is_manual      = label_manual or ts_manual or loc_manual

        # ------------ resolve / build Location row -----------------
        location = None
        if address:
            location = Location.query.filter_by(address=address).first()
            if not location:
                try:
                    geo = Nominatim(user_agent="wdp/1.0", timeout=5).geocode(address, exactly_one=True)
                except GeocoderServiceError:
                    geo = None
                location = Location(
                    address   = address,
                    latitude  = geo.latitude  if geo else None,
                    longitude = geo.longitude if geo else None,
                )
                database.session.add(location)
                database.session.flush()

        # ------------- add Image -----------------------------------
        img = Image(
            path              = os.path.join(current_app.config['UPLOAD_FOLDER'], filename),
            label             = label,
            timestamp         = datetime.strptime(ts_str, "%Y-%m-%dT%H:%M"),
            user_id           = session['user_id'],
            label_manual      = label_manual,
            timestamp_manual  = ts_manual,
            location_manual   = loc_manual,
            location          = location,
        )
        database.session.add(img)

    database.session.commit()
    flash("Images enregistrées ✅", "success")
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
    file = request.files.get("image")
    if not file:
        flash("Erreur : aucune image reçue.", "danger")
        return redirect(url_for("main.upload"))

    filename  = secure_filename(file.filename)
    filepath  = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    # Auto-label from rules
    label_auto = classify_image_by_rules(filepath)

    # Values provided by the client (timestamp already ISO-ish)
    timestamp_str = request.form.get("timestamp")
    geolocator = Nominatim(user_agent="wdp/1.0", timeout=5)
    # The form passes a "lat, lon" string
    location_str = request.form.get("location").strip()
    location_geopy = geolocator.reverse(location_str, exactly_one=True)
    lat, lon = lat_lon_from_string(location_str)
    location = Location(address = location_geopy.address, latitude = lat, longitude = lon)

    add_image_to_db(filename, location, timestamp_str, label_auto, False, False, False, True)
    flash("Image enregistrée ✅", "success")
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

    flash("Image supprimée.", "success")
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
            flash("Horodatage invalide : modification ignorée.", "warning")

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
        flash("Image mise à jour ✅", "success")
    else:
        flash("Aucune modification détectée.", "info")

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

    return render_template(
        "dashboard.html",
        stats=stats,
        locations=all_locations,
        locations_coords=locations_coords
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
            flash(error_msg, "danger")
            return render_template("register.html", error=error_msg, name=name, email=email)

        # Création de l'utilisateur
        user = User(name=name, mail=email, password=hashed_password, is_admin=False)
        database.session.add(user)
        database.session.commit()

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

@main.route("/logout")
def logout():
    session.pop("user_id", None)   # forget who was logged-in
    flash("Vous êtes maintenant déconnecté·e.", "info")
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
        flash("Rôle mis à jour ✅", "success")
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
        flash("Compte supprimé ✅", "success")
    return redirect(url_for("main.admin_dashboard"))

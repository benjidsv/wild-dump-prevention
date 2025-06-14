from flask import Blueprint, render_template, request, redirect, url_for, current_app
from sqlalchemy import func
from werkzeug.utils import secure_filename
import os
from app.feature_extraction import extract_features
from app.rules import classify_image_by_rules
from app.db.models import Image, Feature
from app.extensions import db
from datetime import datetime
from PIL import Image as PILImage
from PIL.ExifTags import TAGS, GPSTAGS

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


main = Blueprint('main', __name__)
@main.route("/")
def index():
    return redirect(url_for("main.upload"))

@main.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        file = request.files["image"]
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        # Extract
        features = extract_features(filepath)
        label_auto = classify_image_by_rules(features)
        exif_timestamp = extract_exif_timestamp(filepath)
        timestamp = exif_timestamp or datetime.utcnow()
        location = extract_exif_location(filepath) or ""

        # Render confirm step
        return render_template("confirm_upload.html",
            filename=filename,
            auto_label=label_auto,
            default_timestamp=timestamp.strftime("%Y-%m-%dT%H:%M"),
            auto_location=location
        )

    # GET: show upload form and list of saved images
    images = Image.query.all()
    return render_template("index.html", images=images)

@main.route("/confirm", methods=["POST"])
def confirm_upload():
    filename = request.form.get("filename")
    label = request.form.get("label")
    is_manual = request.form.get("is_manual") == "true"
    timestamp_str = request.form.get("timestamp")
    location = request.form.get("location")

    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    features = extract_features(filepath)

    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M")

    img = Image(
        path=f"uploads/{filename}",
        label=label,
        is_manual=is_manual,
        timestamp=timestamp,
        location=location
    )
    db.session.add(img)
    db.session.commit()

    feat = Feature(image_id=img.id, **features)
    db.session.add(feat)
    db.session.commit()

    return redirect(url_for("main.upload"))

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

    # Filters
    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
            query = query.filter(Image.timestamp >= start_date, Image.timestamp <= end_date)
        except ValueError:
            pass

    if location_filter:
        query = query.filter(Image.location.ilike(f"%{location_filter}%"))

    # Pie chart data
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

    # For dropdown
    all_locations = [r[0] for r in db.session.query(Image.location).distinct().all() if r[0]]

    return render_template("dashboard.html", stats=stats, locations=all_locations)
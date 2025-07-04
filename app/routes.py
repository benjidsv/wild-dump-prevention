import uuid

import cv2
from flask import Blueprint, render_template, request, redirect, url_for, current_app, flash
from sqlalchemy import func
from werkzeug.utils import secure_filename
import os

from app.classification.rules import classify_image_by_rules
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
    return redirect(url_for("main.dashboard"))

@main.route("/upload", methods=["GET", "POST"])
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
def confirm_upload():
    print("post confirm upload")
    filename = request.form.get("filename")
    label = request.form.get("label")
    is_manual = request.form.get("is_manual") == "true"
    timestamp_str = request.form.get("timestamp")
    location = request.form.get("location")

    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)

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

    return redirect(url_for("main.upload"))

@main.route("/confirm_multiple", methods=["POST"])
def confirm_upload_multiple():
    print("post confirm upload multiple")

    filenames = request.form.getlist("filenames")

    for idx, filename in enumerate(filenames):
        # ---- form values ---------------------------------------------------
        label = request.form.get(f"label_{idx}")  # "full" / "empty"
        is_manual = request.form.get(f"is_manual_{idx}") == "true"
        ts_str = request.form.get(f"timestamp_{idx}") or ""  # may be ""
        location = request.form.get(f"location_{idx}") or ""

        # ---- timestamp parsing --------------------------------------------
        try:
            timestamp = datetime.strptime(ts_str, "%Y-%m-%dT%H:%M") if ts_str else datetime.utcnow()
        except ValueError:
            # Fallback if the browser sends an unexpected format
            timestamp = datetime.utcnow()

        # ---- file & feature extraction ------------------------------------
        filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)

        # ---- create DB rows -----------------------------------------------
        img = Image(
            path=f"uploads/{filename}",
            label=label,
            is_manual=is_manual,
            timestamp=timestamp,
            location=location
        )
        db.session.add(img)

    # 2) one commit for all rows
    db.session.commit()
    return redirect(url_for("main.upload"))

@main.route("/extract_from_video", methods=["POST"])
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
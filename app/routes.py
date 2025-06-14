from flask import Blueprint, render_template, request, redirect, url_for, current_app
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from PIL import Image as PILImage, ExifTags
from app.feature_extraction import extract_features
from app.rules import classify_image
from app.db.models import Image, Feature
from app.extensions import db

main = Blueprint('main', __name__)


def _read_exif_timestamp(path):
    """Extract DateTimeOriginal from image EXIF data."""
    try:
        img = PILImage.open(path)
        exif = img._getexif() or {}
        for tag_id, value in exif.items():
            tag = ExifTags.TAGS.get(tag_id)
            if tag == 'DateTimeOriginal':
                return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
    except Exception:
        pass
    return datetime.utcnow()

@main.route("/", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        file = request.files["image"]
        timestamp_str = request.form.get("timestamp")
        label_auto = request.form.get("label_auto", "true") == "true"
        manual_label = request.form.get("label")

        filename = secure_filename(file.filename)
        path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        file.save(path)

        # Determine timestamp
        if timestamp_str:
            img_timestamp = datetime.fromisoformat(timestamp_str)
        else:
            img_timestamp = _read_exif_timestamp(path)

        # Extract features and classify
        features = extract_features(path)
        predicted_label = classify_image(features)
        final_label = predicted_label if label_auto else manual_label

        # Save image record
        img = Image(path=path, label=final_label, timestamp=img_timestamp)
        db.session.add(img)
        db.session.commit()

        # Store features
        feat = Feature(image_id=img.id, **features)
        db.session.add(feat)
        db.session.commit()

        return redirect(url_for(".upload"))

    images = Image.query.all()
    return render_template("index.html", images=images)

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

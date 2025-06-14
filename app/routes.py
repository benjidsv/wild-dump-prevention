from flask import Blueprint, render_template, request, redirect, url_for, current_app
from sqlalchemy import func
from werkzeug.utils import secure_filename
import os
from app.feature_extraction import extract_features
from app.rules import classify_image_by_rules
from app.db.models import Image, Feature
from app.extensions import db
from datetime import datetime

main = Blueprint('main', __name__)

@main.route("/", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        file = request.files["image"]
        filename = secure_filename(file.filename)
        path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        file.save(path)

        # Save image record
        img = Image(path=path)
        db.session.add(img)
        db.session.commit()

        # Extract features
        features = extract_features(path)
        feat = Feature(image_id=img.id, **features)
        db.session.add(feat)
        db.session.commit()

        # Classify
        label_choice = request.form.get("label_choice")

        if label_choice == "auto":
            label = classify_image_by_rules(features)
            img.label = label
            img.is_manual = False
        else:
            img.label = label_choice
            img.is_manual = True
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

@main.route("/dashboard")
def dashboard():
    # Parse filters from query string
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")

    query = Image.query

    # Apply date filter if provided
    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
            query = query.filter(Image.timestamp >= start_date, Image.timestamp <= end_date)
        except ValueError:
            pass  # Ignore bad input, show all

    # Count full vs empty
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

    return render_template("dashboard.html", stats=stats)

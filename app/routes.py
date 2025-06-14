from flask import Blueprint, render_template, request, redirect, url_for, current_app
from werkzeug.utils import secure_filename
import os
from app.feature_extraction import extract_features
from app.rules import classify_image
from app.db.models import Image, Feature
from app.extensions import db

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
        label = classify_image(features)
        img.label = label
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

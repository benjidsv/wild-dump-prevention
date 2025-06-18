# 🗑️ Wild Dump Prevention Platform

**Smart Trash Monitoring by Image Upload – Efrei Data 2025**

## 📌 Project Overview

The Wild Dump Prevention (WDP) platform is a lightweight web application that helps monitor overflowing public trash bins by analyzing images. It enables citizens or agents to upload pictures, automatically extracts visual features, applies rule-based classification (full/empty), and visualizes trends to help prevent illegal dumps.

---

## 🚀 Features

- 📸 Upload images of trash bins
- 🏷️ Annotate as "Full" or "Empty" manually or via automated rules
- 📊 Extract visual features: size, average color, contrast, contours, etc.
- 🧠 Classify images based on configurable rule sets (no machine learning)
- 🗺️ Visualize statistics & risk zones with dynamic dashboard (Chart.js)

---

## 🚀 TODO
Features:
- "Secure mode" which forces the user to take the picture now ensuring the accuracy of the data (timestamp, location etc.)
- Batch upload for admins

Classification:

| Component               | Model/Tool               |
| ----------------------- | ------------------------ |
| **Classifier**          | EfficientNetB0/MobileNet |
| **Detector**            | YOLOv5s                  |
| **Explainability**      | Grad-CAM for classifier  |
| **Rule logic / hybrid** | Detector → decision      |
| **Flask backend**       | API + inference          |
| **Dashboard**           | Upload stats + map viz   |
| **Augmentation tool**   | Albumentations CLI       |


## ⚙️ Tech Stack

| Layer | Technology             |
|-------|------------------------|
| Backend | Python 3.11 + Flask    |
| Image Processing | Pillow, OpenCV         |
| Database | PostgreSQL             |
| Frontend | HTML/CSS, Bootstrap 5, Chart.js |
| Environment | Conda + Gunicorn (for deployment) |

---

## 📂 Project Structure
<pre>
wild-dump-prevention/
├── app/
│   ├── classification/    # Classification logic & models
│   ├── templates/         # HTML templates (Jinja2)
│   ├── db/models.py       # Database models
│   ├── static/            # CSS, JS, uploads
│   ├── routes.py          # Flask routes
│   ├── feature_extraction.py
├── uploads/               # Uploaded images (ignored by Git)
├── ml/
│   ├── classification/      # Binary classifier
│   │   ├── train.py
│   │   ├── dataset/         # Only for classifier
│   │   └── saved_models/
│   ├── detection/           # YOLO detector
│   │   ├── train.py
│   │   ├── runs/
│   │   └── dataset/         # Annotated YOLO data
│   ├── explainability/      # Grad-CAM / interpretability
├── data/                    # Raw images (clean/dirty)
│   ├── annotations/         # CSVs or YOLO label files
├── main.py                # Flask entrypoint (dev)
├── run.py                 # Gunicorn entrypoint (prod)
├── config.py              # Configurations (dev/prod)
├── requirements.txt       # Pip dependencies
├── .env, .envexample      # Environment variables
├── .gitignore
└── README.md
</pre>

---

## 📂 How to setup
1. **Install packages**
   ```bash
   pip install -r requirements.txt
   ```
2. **Configure PostgreSQL**
   - **For Unix-like systems (Linux/macOS)**, run in `psql`:
     ```sql
     CREATE DATABASE wdp_db;
     CREATE USER wdp_user WITH PASSWORD 'wdp_pass';
     GRANT ALL PRIVILEGES ON DATABASE wdp_db TO wdp_user;
     ```
   - **For Windows**, after creating the database and user as shown for Unix, you might need to grant additional privileges. First, connect to your database using `psql`:
     ```bash
     psql -U postgres -d wdp_db
     ```
     Then, execute the following commands inside the `psql` shell:
     ```sql
     GRANT ALL PRIVILEGES ON DATABASE wdp_db TO wdp_user;
     GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO wdp_user;
     GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO wdp_user;
     GRANT USAGE ON SCHEMA public TO wdp_user;
     ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO wdp_user;
     GRANT CREATE ON SCHEMA public TO wdp_user;
     ```
3. **Set environment variables**
   ```bash
   cp .envexample .env
   # Edit SECRET_KEY or DATABASE_URL if needed
   ```
4. **Run the application**
   ```bash
   python main.py        # development
   # or
   gunicorn -w 4 -b 0.0.0.0:8000 run:app
   ```

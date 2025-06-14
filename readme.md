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
- "Secure mode" which forces the user to take the picture now ensuring the accuracy of the data (timestamp, location etc.)
- Batch upload for admins

## ⚙️ Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11 + Flask |
| Image Processing | Pillow, OpenCV |
| Database | SQLite or PostgreSQL |
| Frontend | HTML/CSS, Bootstrap 5, Chart.js |
| Environment | Conda + Gunicorn (for deployment) |

---

## 📂 Project Structure

wild-dump-prevention/
├── app/
│   ├── templates/         # HTML templates (Jinja2)
│   ├── static/            # CSS, JS, uploads
│   ├── routes.py          # Flask routes
│   ├── feature_extraction.py
│   ├── rules.py           # Classification rules
│   └── db/models.py
├── uploads/               # Uploaded images (ignored by Git)
├── main.py                # Flask entrypoint (dev)
├── run.py                 # Gunicorn entrypoint (prod)
├── config.py              # Configurations (dev/prod)
├── requirements.txt       # Pip dependencies
├── environment.yml        # Conda environment (optional)
├── .gitignore
└── README.md

---

## 📂 How to setup (local)
log in psql
-- 1. Create the project database
CREATE DATABASE wdp_db;

-- 2. Create a dedicated user with password
CREATE USER wdp_user WITH PASSWORD 'wdp_pass';

-- 3. Grant privileges
GRANT ALL PRIVILEGES ON DATABASE wdp_db TO wdp_user;

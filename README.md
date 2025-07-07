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
- Secure user upload which forces the user to take the picture now ensuring the accuracy of the data (timestamp, location etc.)
- Batch admin upload
- Upload videos and select timestamps
- 

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
   cp .env.example .env
   # Edit SECRET_KEY or DATABASE_URL if needed
   ```

4. **Initialize the database in flask**
   ```bash
   flask --help
   flask create-db
   flask create-superuser
   ```
5. **Launch Nginx and create a certificate**
    ```bash
   mv wdp.conf {NGINX Path: macos:'/opt/homebrew/etc/nginx/servers@'}
   mkcert localhost 127.0.0.1 ::1 wilddump.local
    ```

6. **Run the application**
   ```bash
   flask run --host 127.0.0.1 --port 8000
   # or
    gunicorn "app:create_app()" --bind 127.0.0.1:8000 --workers 3
   ```
   

## 📂 How to set up the project locally

> **Prerequisites**  
> * Python 3.10 + (tested on 3.12)  
> * PostgreSQL ≥ 12  
> * `mkcert` (for a local TLS certificate)  
> * Nginx (Homebrew on macOS, apt/yum on Linux)  

---

# 🗑️ Wild-Dump-Prevention – Local Setup Guide

> **Prerequisites**  
> • Python ≥ 3.10 (tested on 3.12)  
> • PostgreSQL ≥ 12  
> • `mkcert` (**local HTTPS**)  
> • **Nginx** (via Homebrew on macOS / apt | yum on Linux)

---

## 1 · Clone & create a virtual-env

```bash
git clone https://github.com/your-org/wild-dump-prevention.git
cd wild-dump-prevention

python -m venv .venv
source .venv/bin/activate                # Windows → .venv\Scripts\activate
```

---

## 2 · Install Python packages

```bash
pip install -r requirements.txt
```

---

## 3 · PostgreSQL database

### 3.1 - UNIX
```sql
CREATE DATABASE wdp_db;
CREATE USER wdp_user WITH PASSWORD 'wdp_pass';
GRANT ALL PRIVILEGES ON DATABASE wdp_db TO wdp_user;
```

### 3.2 - Windows
```bash
psql -U postgres -d wdp_db
```
```sql
GRANT ALL PRIVILEGES ON DATABASE wdp_db TO wdp_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO wdp_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO wdp_user;
GRANT USAGE,CREATE ON SCHEMA public TO wdp_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO wdp_user;
```

---

## 4 · Environment variables

```bash
cp .env.example .env          # then edit if needed
```

---

## 5 · Initialise / reset the DB (custom Flask CLI)

```bash
flask create-db               # creates all tables
flask create-superuser        # interactive super-admin creation

# reset = DANGER ⚠️
flask drop-db --yes
```

---

## 6 · Static uploads directory

```bash
mkdir -p app/static/uploads
```

---

## 7 · Local HTTPS with mkcert + Nginx

```bash
# ① trusted local CA
mkcert -install

# ② issue cert for local hostnames
mkcert localhost 127.0.0.1 ::1 wilddump.local

# ③ move / link to Nginx cert path
sudo mkdir -p /opt/homebrew/etc/nginx/certs          # macOS path
sudo cp localhost+2.pem      /opt/homebrew/etc/nginx/certs/wdp.crt
sudo cp localhost+2-key.pem  /opt/homebrew/etc/nginx/certs/wdp.key
```

### Nginx v-host (`wdp.conf` → `/opt/homebrew/etc/nginx/servers/` or `/etc/nginx/conf.d/`)

```nginx
server {
    listen 443 ssl http2;
    server_name localhost wilddump.local;

    ssl_certificate     /opt/homebrew/etc/nginx/certs/wdp.crt;
    ssl_certificate_key /opt/homebrew/etc/nginx/certs/wdp.key;

    # --- static files ---
    location /static/ {
        alias /Users/<you>/wild-dump-prevention/app/static/;
    }

    # --- flask backend ---
    location / {
        proxy_pass         http://127.0.0.1:8000;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto https;
    }
}
```

```bash
sudo nginx -t && sudo nginx -s reload     # validate + reload
```

### 7 bis · Map the custom hostname to 127.0.0.1

| OS | File | Example line |
|----|------|--------------|
| **macOS / Linux** | `/etc/hosts` | ```127.0.0.1   wilddump.local``` |
| **Windows** | `C:\Windows\System32\drivers\etc\hosts` | `127.0.0.1   wilddump.local` |

> *⚠️ Requires admin / sudo privileges.*

After saving, your browser will send requests for **https://wilddump.local** to `127.0.0.1`, where Nginx terminates the TLS connection and proxies to Flask/Gunicorn.


---

## 8 · Run the application

### 8.1 - Dev
```bash
flask run --host 127.0.0.1 --port 8000
```
### 8.2 - Prod
```bash
pip install gunicorn
gunicorn "app:create_app()" --bind 127.0.0.1:8000 --workers 3
```

Open **https://localhost** (or **https://wilddump.local**) – you’re live 💫

---

## 9 · Troubleshooting

| Symptom | Quick check |
|---------|-------------|
| 404 from Nginx | `curl -v https://localhost/` |
| Flask not reachable | `curl -v http://127.0.0.1:8000/` |
| Cert errors | `openssl s_client -connect localhost:443` |
| Static path wrong | open `/static/logo.png` directly |
| DB connect fails | `psql $DATABASE_URL` |

---

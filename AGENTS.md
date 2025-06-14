# AGENTS.md

## 🧱 But
Ce guide permet à Codex (et aux environnements sandbox) de :
- Installer les dépendances (PostgreSQL, Python, etc.)
- Initialiser la base de données
- Exécuter les tests (`pytest`)
- Générer et valider du code automatiquement

---

## ⚙️ Environnement système

```bash
# Mise à jour et installation de PostgreSQL
apt-get update
apt-get install -y postgresql postgresql-contrib
service postgresql start

# Configuration de l’utilisateur et de la base de données
sudo -u postgres createuser --superuser $USER
sudo -u postgres createdb wdp_db

# Définition de la variable pour SQLAlchemy
export DATABASE_URL=postgresql://$USER@localhost:5432/wdp_db

# Installation des dépendances via pip
pip install -r requirements.txt

# Création des tables via Flask
flask shell -c "from app.extensions import db; db.create_all()"

pytest tests/
```
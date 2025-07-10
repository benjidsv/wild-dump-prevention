#!/usr/bin/env python3
"""
Script pour peupler la base de données avec des images de test
et des adresses parisiennes réalistes.
"""

import os
import random
import shutil
from datetime import datetime, timedelta
from app import create_app
from app.extensions import database
from app.db.models import Image, Location, User
from app.classification.rules import classify_image_by_rules
from ultralytics import YOLO
import json

import requests
import urllib.parse
import time

# Cache pour éviter les appels API répétés
address_cache = {}

def fetch_paris_addresses(query, limit=10):
    """Utilise l'API Adresse du gouvernement français pour récupérer des adresses parisiennes."""
    if query in address_cache:
        return address_cache[query]
    
    try:
        # Construire l'URL de l'API
        encoded_query = urllib.parse.quote(query)
        url = f"https://api-adresse.data.gouv.fr/search/?q={encoded_query}&limit={limit}&citycode=75101,75102,75103,75104,75105,75106,75107,75108,75109,75110,75111,75112,75113,75114,75115,75116,75117,75118,75119,75120"
        
        # Faire l'appel API
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Extraire les résultats
        results = []
        for feature in data.get('features', []):
            properties = feature.get('properties', {})
            geometry = feature.get('geometry', {})
            
            if geometry.get('type') == 'Point':
                coordinates = geometry.get('coordinates', [])
                if len(coordinates) >= 2:
                    results.append({
                        'address': properties.get('label', ''),
                        'lat': coordinates[1],  # Latitude
                        'lon': coordinates[0]   # Longitude
                    })
        
        # Mettre en cache
        address_cache[query] = results
        
        # Respecter les limites de l'API (pause entre requêtes)
        time.sleep(0.1)
        
        return results
        
    except Exception as e:
        print(f"⚠️  Erreur API Adresse: {e}")
        return []

def get_unique_paris_address(used_addresses):
    """Génère une adresse parisienne unique en utilisant l'API Adresse."""
    
    # Termes de recherche pour diversifier les résultats
    search_terms = [
        "rue paris",
        "avenue paris", 
        "boulevard paris",
        "place paris",
        "quai paris",
        "rue de la",
        "avenue de la",
        "boulevard de la",
        "place de la",
        "rue des",
        "avenue des",
        "boulevard des",
        "place des",
        "rue du",
        "avenue du",
        "boulevard du",
        "place du"
    ]
    
    max_attempts = 20
    
    for _ in range(max_attempts):
        # Choisir un terme de recherche aléatoire
        search_term = random.choice(search_terms)
        
        # Récupérer des adresses de l'API
        addresses = fetch_paris_addresses(search_term, limit=20)
        
        if addresses:
            # Mélanger les résultats
            random.shuffle(addresses)
            
            # Chercher une adresse unique
            for addr_data in addresses:
                if addr_data['address'] not in used_addresses:
                    return addr_data
    
    # Fallback si on ne trouve pas d'adresse unique
    # Générer une adresse générique avec des coordonnées parisiennes
    fallback_addresses = [
        {"address": f"Rue de la Paix, 75002 Paris (#{random.randint(1000, 9999)})", "lat": 48.8695, "lon": 2.3312},
        {"address": f"Avenue des Champs-Élysées, 75008 Paris (#{random.randint(1000, 9999)})", "lat": 48.8714, "lon": 2.2945},
        {"address": f"Boulevard Saint-Germain, 75005 Paris (#{random.randint(1000, 9999)})", "lat": 48.8462, "lon": 2.3372},
        {"address": f"Rue de Rivoli, 75001 Paris (#{random.randint(1000, 9999)})", "lat": 48.8566, "lon": 2.3522},
        {"address": f"Place de la Bastille, 75011 Paris (#{random.randint(1000, 9999)})", "lat": 48.8532, "lon": 2.3693},
    ]
    
    return random.choice(fallback_addresses)

def load_yolo_model():
    """Charge le modèle YOLO une seule fois."""
    try:
        # Chemin vers le modèle YOLO
        model_path = os.path.join(os.path.dirname(__file__), 'app', 'classification', 'models', 'best.pt')
        
        if not os.path.exists(model_path):
            print(f"⚠️  Modèle YOLO non trouvé: {model_path}")
            return None
        
        print(f"🤖 Chargement du modèle YOLO: {model_path}")
        model = YOLO(model_path)
        print(f"✅ Modèle YOLO chargé avec succès")
        
        return model
        
    except Exception as e:
        print(f"❌ Erreur chargement YOLO: {e}")
        return None

def classify_with_yolo(filepath, model):
    """Classifie une image avec le modèle YOLO pré-chargé."""
    try:
        if model is None:
            return None, None
            
        # Faire une prédiction
        results = model.predict(filepath, conf=0.25, verbose=False)
        result = results[0]
        
        # Extraire la classe prédite
        pred_class = result.probs.top1
        confidence = result.probs.top1conf.item()
        
        # Mapper la classe à un label
        class_name = 'empty' if pred_class == 0 else 'full'
        
        print(f"  🤖 YOLO prediction: {class_name} (confidence: {confidence:.2f})")
        
        # Générer des features par défaut (puisque YOLO ne fournit pas les features OpenCV)
        features = {
            "dark_ratio": 0.0,
            "edge_density": 0.0,
            "contour_count": 0.0,
            "color_diversity": 0.0,
            "avg_saturation": 0.0,
            "bright_ratio": 0.0,
            "std_intensity": 0.0,
            "entropy": 0.0,
            "color_clusters": 0.0,
            "aspect_dev": 0.0,
            "fill_ratio": 0.0,
        }
        
        return class_name, features
        
    except Exception as e:
        print(f"  ❌ Erreur YOLO: {e}")
        return None, None

def get_random_timestamp():
    """Génère un timestamp aléatoire dans les 30 derniers jours."""
    now = datetime.now()
    days_ago = random.randint(0, 30)
    hours_ago = random.randint(0, 23)
    minutes_ago = random.randint(0, 59)
    
    timestamp = now - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
    return timestamp

def copy_image_to_uploads(source_path, upload_folder):
    """Copie une image vers le dossier uploads et retourne le nom du fichier."""
    filename = os.path.basename(source_path)
    destination = os.path.join(upload_folder, filename)
    
    # Éviter les doublons
    if os.path.exists(destination):
        name, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(destination):
            filename = f"{name}_{counter}{ext}"
            destination = os.path.join(upload_folder, filename)
            counter += 1
    
    shutil.copy2(source_path, destination)
    return filename

def create_location(address_data):
    """Crée ou récupère une location."""
    location = Location.query.filter_by(address=address_data["address"]).first()
    if not location:
        location = Location(
            address=address_data["address"],
            latitude=address_data["lat"],
            longitude=address_data["lon"]
        )
        database.session.add(location)
        database.session.flush()
    return location

def add_image_to_db(filepath, filename, label, location, timestamp, user_id, features):
    """Ajoute une image à la base de données."""
    # Convertir les features en float
    features_dict = {}
    for key, value in features.items():
        features_dict[key] = float(value)
    
    # Créer l'image
    img = Image(
        path=filepath,
        label=label,
        timestamp=timestamp,
        location=location,
        user_id=user_id,
        label_manual=False,
        timestamp_manual=False,
        location_manual=False,
        dark_ratio=features_dict.get("dark_ratio", 0.0),
        edge_density=features_dict.get("edge_density", 0.0),
        contour_count=features_dict.get("contour_count", 0.0),
        color_diversity=features_dict.get("color_diversity", 0.0),
        avg_saturation=features_dict.get("avg_saturation", 0.0),
        bright_ratio=features_dict.get("bright_ratio", 0.0),
        std_intensity=features_dict.get("std_intensity", 0.0),
        entropy=features_dict.get("entropy", 0.0),
        color_clusters=features_dict.get("color_clusters", 0.0),
        aspect_dev=features_dict.get("aspect_dev", 0.0),
        fill_ratio=features_dict.get("fill_ratio", 0.0),
    )
    
    database.session.add(img)
    return img

def populate_database():
    """Fonction principale pour peupler la base de données."""
    app = create_app()
    
    with app.app_context():
        # Vérifier qu'un utilisateur admin existe
        admin_user = User.query.filter_by(is_admin=True).first()
        if not admin_user:
            print("❌ Aucun utilisateur admin trouvé. Créez d'abord un super-admin avec 'flask create-superuser'")
            return
        
        print(f"✅ Utilisateur admin trouvé: {admin_user.name}")
        
        # Dossiers source
        test_folder = "Data/test"
        train_clean_folder = "Data/train/with_label/clean"
        upload_folder = app.config["UPLOAD_FOLDER"]
        
        # Vérifier que les dossiers existent
        if not os.path.exists(test_folder):
            print(f"❌ Dossier {test_folder} non trouvé")
            return
        
        if not os.path.exists(train_clean_folder):
            print(f"❌ Dossier {train_clean_folder} non trouvé")
            return
        
        print(f"✅ Dossiers source trouvés")
        
        # Créer le dossier uploads s'il n'existe pas
        os.makedirs(upload_folder, exist_ok=True)
        
        # Récupérer les images
        test_images = []
        clean_images = []
        
        # Images de test (mixed labels)
        for filename in os.listdir(test_folder):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                test_images.append(os.path.join(test_folder, filename))
        
        # Images clean (empty label)
        for filename in os.listdir(train_clean_folder):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                clean_images.append(os.path.join(train_clean_folder, filename))
        
        print(f"✅ Trouvé {len(test_images)} images de test et {len(clean_images)} images clean")
        
        # Mélanger et limiter le nombre d'images pour éviter la surcharge
        all_images = test_images[:30] + clean_images[:20]  # 50 images au total
        random.shuffle(all_images)
        
        success_count = 0
        error_count = 0
        used_addresses = set()  # Pour suivre les adresses utilisées
        
        # Charger le modèle YOLO une seule fois
        yolo_model = load_yolo_model()
        
        print("🔄 Début de l'insertion des images...")
        print("📍 Récupération d'adresses parisiennes uniques via l'API Adresse...")
        
        for i, source_path in enumerate(all_images, 1):
            try:
                print(f"Traitement de l'image {i}/{len(all_images)}: {os.path.basename(source_path)}")
                
                # Copier l'image vers uploads
                filename = copy_image_to_uploads(source_path, upload_folder)
                filepath = os.path.join(upload_folder, filename)
                
                # Classifier l'image avec YOLO
                label, features = classify_with_yolo(filepath, yolo_model)
                
                if label is None:
                    print(f"  ⚠️  Échec classification YOLO, utilisation du fallback")
                    # Fallback basé sur le dossier source
                    label = "empty" if "clean" in source_path else "full"
                    features = {
                        "dark_ratio": 0.0,
                        "edge_density": 0.0,
                        "contour_count": 0.0,
                        "color_diversity": 0.0,
                        "avg_saturation": 0.0,
                        "bright_ratio": 0.0,
                        "std_intensity": 0.0,
                        "entropy": 0.0,
                        "color_clusters": 0.0,
                        "aspect_dev": 0.0,
                        "fill_ratio": 0.0,
                    }
                    print(f"  📁 Label basé sur le dossier: {label}")
                
                # Obtenir une adresse parisienne unique
                print(f"  🔍 Recherche d'adresse unique...")
                address_data = get_unique_paris_address(used_addresses)
                used_addresses.add(address_data['address'])
                
                # Obtenir un timestamp aléatoire
                timestamp = get_random_timestamp()
                
                # Créer la location
                location = create_location(address_data)
                
                # Ajouter l'image à la DB
                add_image_to_db(filepath, filename, label, location, timestamp, admin_user.id, features)
                
                success_count += 1
                print(f"  ✅ Image ajoutée: {filename} ({label})")
                print(f"     📍 {address_data['address']}")
                print(f"     📍 GPS: {address_data['lat']:.6f}, {address_data['lon']:.6f}")
                
            except Exception as e:
                error_count += 1
                print(f"  ❌ Erreur: {e}")
                continue
        
        # Commit toutes les modifications
        try:
            database.session.commit()
            print(f"\n🎉 Insertion terminée!")
            print(f"✅ {success_count} images ajoutées avec succès")
            print(f"❌ {error_count} erreurs")
            
            # Afficher les statistiques
            total_images = Image.query.count()
            full_count = Image.query.filter_by(label="full").count()
            empty_count = Image.query.filter_by(label="empty").count()
            
            print(f"\n📊 Statistiques de la base de données:")
            print(f"  Total d'images: {total_images}")
            print(f"  Poubelles pleines: {full_count}")
            print(f"  Poubelles vides: {empty_count}")
            
        except Exception as e:
            database.session.rollback()
            print(f"❌ Erreur lors du commit: {e}")

if __name__ == "__main__":
    populate_database()
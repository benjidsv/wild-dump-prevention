#!/usr/bin/env python3
"""
Script pour nettoyer la base de données (supprimer toutes les images et locations)
"""

import os
from app import create_app
from app.extensions import database
from app.db.models import Image, Location

def clean_database():
    """Supprime toutes les images et locations de la base de données."""
    app = create_app()
    
    with app.app_context():
        try:
            # Compter les éléments avant suppression
            image_count = Image.query.count()
            location_count = Location.query.count()
            
            print(f"🔄 Suppression de {image_count} images et {location_count} locations...")
            
            # Supprimer toutes les images
            Image.query.delete()
            
            # Supprimer toutes les locations
            Location.query.delete()
            
            # Commit les modifications
            database.session.commit()
            
            print("✅ Base de données nettoyée avec succès!")
            
        except Exception as e:
            database.session.rollback()
            print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    response = input("⚠️  Êtes-vous sûr de vouloir supprimer toutes les images et locations? (oui/non): ")
    if response.lower() in ['oui', 'yes', 'y']:
        clean_database()
    else:
        print("Operation annulée.")
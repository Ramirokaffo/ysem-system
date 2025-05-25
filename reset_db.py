#!/usr/bin/env python
"""
Script pour réinitialiser la base de données MySQL
"""
import os
import sys
import django
from django.conf import settings
import pymysql

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ysem.settings')
django.setup()

def reset_database():
    """
    Supprime et recrée la base de données
    """
    db_config = settings.DATABASES['default']
    
    # Connexion à MySQL sans spécifier la base de données
    connection = pymysql.connect(
        host=db_config['HOST'],
        user=db_config['USER'],
        password=db_config['PASSWORD'],
        port=int(db_config['PORT'])
    )
    
    try:
        with connection.cursor() as cursor:
            # Supprimer la base de données si elle existe
            cursor.execute(f"DROP DATABASE IF EXISTS `{db_config['NAME']}`")
            print(f"Base de données '{db_config['NAME']}' supprimée.")
            
            # Créer la nouvelle base de données
            cursor.execute(f"CREATE DATABASE `{db_config['NAME']}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"Base de données '{db_config['NAME']}' créée.")
            
        connection.commit()
        
    finally:
        connection.close()

if __name__ == '__main__':
    print("Réinitialisation de la base de données...")
    reset_database()
    print("Base de données réinitialisée avec succès!")

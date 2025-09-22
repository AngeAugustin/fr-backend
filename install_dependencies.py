#!/usr/bin/env python
"""
Script pour installer les dépendances nécessaires
"""

import subprocess
import sys
import os

def install_package(package):
    """Installe un package avec pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} installé avec succès")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'installation de {package}: {e}")
        return False

def main():
    print("🔧 INSTALLATION DES DÉPENDANCES")
    print("=" * 40)
    
    packages = [
        "django",
        "djangorestframework",
        "django-cors-headers",
        "psycopg2-binary",
        "pandas",
        "openpyxl",
        "numpy"
    ]
    
    success_count = 0
    for package in packages:
        print(f"\n📦 Installation de {package}...")
        if install_package(package):
            success_count += 1
    
    print(f"\n📊 Résultat: {success_count}/{len(packages)} packages installés")
    
    if success_count == len(packages):
        print("🎉 Toutes les dépendances sont installées!")
        print("\nVous pouvez maintenant:")
        print("1. Charger les données: python load_csv_to_postgresql.py your_file.csv")
        print("2. Tester le système: python test_postgresql_system.py")
    else:
        print("⚠️  Certaines dépendances n'ont pas pu être installées")
        print("Installez-les manuellement avec: pip install <package_name>")

if __name__ == "__main__":
    main()

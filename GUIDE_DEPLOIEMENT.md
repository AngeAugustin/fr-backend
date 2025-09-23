# 🚀 Guide de Déploiement - Projet FR Backend

## 📋 Vue d'ensemble

Ce projet est une **API Django REST** pour la génération de **Tableaux de Flux de Trésorerie (TFT) SYSCOHADA**. Il permet de traiter des données comptables et générer des rapports financiers conformes aux normes OHADA.

## 🛠️ Prérequis

### Logiciels requis :
- **Python 3.8+** (recommandé : Python 3.11+)
- **PostgreSQL 12+** (ou SQLite pour le développement)
- **Git** (pour cloner le projet)

### Outils recommandés :
- **Visual Studio Code** ou **PyCharm**
- **Postman** (pour tester l'API)
- **pgAdmin** (pour gérer PostgreSQL)

## 📦 Installation - Méthode 1 : PostgreSQL (Production)

### 1. Cloner le projet
```bash
git clone <url-du-repo>
cd fr-backend
```

### 2. Installer PostgreSQL
- **Windows** : Télécharger depuis [postgresql.org](https://www.postgresql.org/download/windows/)
- **Linux** : `sudo apt install postgresql postgresql-contrib`
- **macOS** : `brew install postgresql`

### 3. Créer la base de données
```sql
-- Se connecter à PostgreSQL
psql -U postgres

-- Créer la base de données
CREATE DATABASE af_db;
CREATE USER postgres WITH PASSWORD 'postgres';
GRANT ALL PRIVILEGES ON DATABASE af_db TO af_user;
\q
```

### 4. Configurer l'environnement virtuel
```bash
# Créer l'environnement virtuel
python -m venv .venv

# Activer l'environnement virtuel
# Windows :
.venv\Scripts\Activate.ps1
# Linux/macOS :
source .venv/bin/activate
```

### 5. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 6. Configurer la base de données
Modifier `fr_backend/settings.py` :
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'af_db',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### 7. Migrations et données
```bash
# Appliquer les migrations
python manage.py migrate

# Charger les données de test (optionnel)
python load_csv_to_postgresql.py
```

### 8. Créer un superutilisateur
```bash
python manage.py createsuperuser
```

### 9. Lancer le serveur
```bash
python manage.py runserver
```

## 📦 Installation - Méthode 2 : SQLite (Développement)

### 1-4. Identiques à la méthode PostgreSQL

### 5. Installer les dépendances (sans psycopg2)
```bash
pip install Django==5.2.6
pip install djangorestframework==3.16.1
pip install django-cors-headers==4.9.0
pip install djangorestframework-simplejwt==5.5.1
pip install pandas==2.3.0
pip install openpyxl==3.1.5
```

### 6. Configurer SQLite
Modifier `fr_backend/settings.py` :
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

### 7-9. Identiques à la méthode PostgreSQL

## 🚀 Démarrage Rapide

### Script d'activation automatique
Le projet inclut un script `start-from-env` pour activer rapidement l'environnement :

```bash
# Windows PowerShell
.\start-from-env

# Ou manuellement
.venv\Scripts\Activate.ps1
```

### Commandes essentielles
```bash
# Activer l'environnement virtuel
.venv\Scripts\Activate.ps1

# Installer les dépendances
pip install -r requirements.txt

# Appliquer les migrations
python manage.py migrate

# Lancer le serveur
python manage.py runserver

# Accéder à l'interface d'administration
# http://localhost:8000/admin/
```

## 🔧 Configuration

### Variables d'environnement (optionnel)
Créer un fichier `.env` :
```env
SECRET_KEY=votre-cle-secrete
DEBUG=True
DATABASE_URL=postgresql://af_user:af_password@localhost:5432/af_db
```

### Configuration CORS
Dans `fr_backend/settings.py` :
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React
    "http://localhost:5173",  # Vite
    "http://127.0.0.1:8000", # Django
]
```

## 📊 Chargement des données

### 1. Format CSV requis
Le fichier CSV doit contenir les colonnes :
- `account_number` : Numéro de compte
- `account_label` : Libellé du compte
- `balance` : Solde
- `total_debit` : Total débit
- `total_credit` : Total crédit
- `created_at` : Date de création

### 2. Charger les données
```bash
# Utiliser le script de chargement
python load_csv_to_postgresql.py

# Ou via l'interface web
# http://localhost:8000/api/reports/upload/
```

## 🔄 Traitement Automatique en Temps Réel

### Surveillance des Nouvelles Données

Le système inclut maintenant un **traitement automatique en temps réel** qui surveille les nouvelles données `AccountData` et génère automatiquement les rapports TFT.

#### 🚀 **Modes de Surveillance Disponibles :**

##### 1. **Traitement Automatique par Signal Django** (Recommandé)
- **Activation automatique** dès qu'une nouvelle donnée `AccountData` est créée
- **Traitement différé** pour éviter les conflits
- **Seuil minimum** : 10 comptes par `financial_report_id`

```bash
# Le traitement se fait automatiquement, aucun démarrage requis
# Les logs sont disponibles dans logs/auto_processing.log
```

##### 2. **Commande Django de Surveillance**
```bash
# Surveillance continue (toutes les 60 secondes)
python manage.py monitor_data

# Traitement unique de toutes les données en attente
python manage.py monitor_data --once

# Surveillance personnalisée (toutes les 30 secondes, seuil 20 comptes)
python manage.py monitor_data --interval 30 --min-accounts 20
```

##### 3. **Script Standalone de Surveillance**
```bash
# Surveillance continue
python monitor_realtime_data.py

# Traitement unique
python monitor_realtime_data.py --once

# Vérifier le statut
python monitor_realtime_data.py --status

# Surveillance personnalisée
python monitor_realtime_data.py --interval 120 --min-accounts 15
```

#### 📊 **Fonctionnalités du Système de Surveillance :**

- ✅ **Détection automatique** des nouvelles données
- ✅ **Traitement différé** pour éviter les conflits
- ✅ **Seuil configurable** de comptes minimum
- ✅ **Logs détaillés** de tous les traitements
- ✅ **Gestion d'erreurs** robuste
- ✅ **Évite les doublons** de traitement
- ✅ **Statut en temps réel** du système

#### 🔍 **Monitoring et Logs :**

```bash
# Consulter les logs de traitement automatique
tail -f logs/auto_processing.log

# Vérifier le statut du système
python monitor_realtime_data.py --status

# Voir les données en attente via l'API
curl -X GET http://localhost:8000/api/reports/process-account-data/
```

#### ⚙️ **Configuration Avancée :**

Dans `fr_backend/settings.py`, vous pouvez ajuster :
- **Niveau de logs** : `INFO`, `DEBUG`, `WARNING`, `ERROR`
- **Format des logs** : Simple ou détaillé
- **Fichiers de logs** : Console et/ou fichier

#### 🚨 **Gestion des Erreurs :**

Le système gère automatiquement :
- **Données insuffisantes** : Ignore si < seuil minimum
- **Erreurs de traitement** : Marque comme `error` dans `BalanceUpload`
- **Conflits** : Évite les traitements multiples
- **Données manquantes** : Logs d'avertissement

#### 📈 **Performance et Optimisation :**

- **Traitement différé** : Utilise `transaction.on_commit()`
- **Seuils intelligents** : Évite les traitements prématurés
- **Cache des résultats** : Évite les recalculs inutiles
- **Logs optimisés** : Niveau configurable selon l'environnement

---

## 🧪 Tests et Validation

### Tests de base de données
```bash
python test_database_only.py
```

### Vérification des dividendes
```bash
python check_fm_dividends.py
```

### Tests API
```bash
# Tester l'API avec curl
curl -X GET http://localhost:8000/api/reports/tft/

# Ou utiliser Postman
# GET http://localhost:8000/api/reports/tft/
```

## 🌐 Endpoints API

### Principales routes :
- `GET /api/reports/tft/` - Générer un TFT
- `POST /api/reports/upload/` - Charger des données CSV
- `GET /api/reports/sheets/` - Générer les feuilles maîtresses
- `GET /admin/` - Interface d'administration

### Exemple d'utilisation :
```python
import requests

# Générer un TFT
response = requests.get('http://localhost:8000/api/reports/tft/')
tft_data = response.json()
```

## 🔍 Dépannage

### Problèmes courants :

#### 1. Erreur psycopg2
```bash
# Solution : Installer PostgreSQL ou utiliser SQLite
pip install psycopg2-binary
# OU modifier settings.py pour SQLite
```

#### 2. Erreur de migration
```bash
# Réinitialiser les migrations
python manage.py migrate --fake-initial
python manage.py migrate
```

#### 3. Erreur CORS
```python
# Ajouter l'origine dans settings.py
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
]
```

#### 4. Problème d'environnement virtuel
```bash
# Recréer l'environnement virtuel
rm -rf .venv
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 📁 Structure du projet

```
fr-backend/
├── api/
│   └── reports/
│       ├── models.py          # Modèles de données
│       ├── views.py           # Vues API
│       ├── serializers.py     # Sérialiseurs
│       ├── tft_generator.py   # Générateur TFT
│       └── urls.py           # Routes API
├── fr_backend/
│   ├── settings.py           # Configuration Django
│   ├── urls.py              # Routes principales
│   └── wsgi.py              # Configuration WSGI
├── media/                    # Fichiers uploadés
├── requirements.txt          # Dépendances Python
├── manage.py                # Script de gestion Django
└── start-from-env           # Script d'activation
```

## 🚀 Déploiement en production

### 1. Configuration production
```python
# settings.py
DEBUG = False
ALLOWED_HOSTS = ['votre-domaine.com']
SECRET_KEY = 'votre-cle-secrete-production'
```

### 2. Variables d'environnement
```bash
export DJANGO_SETTINGS_MODULE=fr_backend.settings
export SECRET_KEY=votre-cle-secrete
export DATABASE_URL=postgresql://user:pass@host:port/db
```

### 3. Serveur web (Nginx + Gunicorn)
```bash
pip install gunicorn
gunicorn fr_backend.wsgi:application
```

## 📞 Support

### Logs et débogage
```bash
# Activer les logs détaillés
python manage.py runserver --verbosity=2

# Vérifier la configuration
python manage.py check
```

### Documentation API
- Interface Swagger : `http://localhost:8000/api/docs/`
- Admin Django : `http://localhost:8000/admin/`

---

## ✅ Checklist de déploiement

- [ ] Python 3.8+ installé
- [ ] PostgreSQL installé et configuré
- [ ] Environnement virtuel créé et activé
- [ ] Dépendances installées
- [ ] Base de données créée
- [ ] Migrations appliquées
- [ ] Superutilisateur créé
- [ ] Données de test chargées
- [ ] Serveur lancé et accessible
- [ ] Tests API fonctionnels

---

**🎉 Félicitations ! Votre projet FR Backend est maintenant opérationnel !**

Pour toute question ou problème, consultez les logs Django ou contactez l'équipe de développement.

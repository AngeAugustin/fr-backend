# FR Backend - Système de Génération de Tableaux de Financement de Trésorerie (TFT)

## 📋 Description du Projet

FR Backend est une API Django REST Framework développée pour automatiser la génération de **Tableaux de Financement de Trésorerie (TFT)** conformes aux normes **SYSCOHADA**. Le système permet de traiter des fichiers CSV de balances comptables et de générer automatiquement des rapports financiers structurés.

## 🚀 Fonctionnalités Principales

### 🔐 Authentification et Autorisation
- **Inscription d'utilisateurs** avec validation des données
- **Authentification JWT** (JSON Web Tokens) avec refresh automatique
- **Déconnexion sécurisée** avec invalidation des tokens
- **Gestion des sessions** utilisateur

### 📊 Traitement des Données Financières
- **Upload de fichiers CSV** de balances comptables
- **Filtrage par période** (date de début et fin)
- **Génération automatique de TFT** selon les normes SYSCOHADA
- **Création de feuilles maîtresses** par groupes comptables :
  - Financier
  - Clients-Ventes
  - Fournisseurs-Achats
  - Personnel
  - Impôts-Taxes
  - Immobilisations Corporelles-Incorporelles
  - Immobilisations Financières
  - Stocks
  - Capitaux Propres
  - Provisions R-C

### 📈 Contrôles de Cohérence
- **Validation automatique** des flux de trésorerie
- **Contrôle de cohérence** entre les variations TFT et trésorerie
- **Détection d'erreurs** et messages d'alerte
- **Rapports de cohérence** détaillés

### 📁 Gestion des Fichiers
- **Stockage sécurisé** des fichiers générés en base de données
- **Téléchargement direct** des fichiers Excel générés
- **Historique complet** des uploads et générations
- **Gestion des médias** avec organisation par dossiers

## 🛠️ Technologies Utilisées

- **Backend**: Django 5.2.6
- **API**: Django REST Framework
- **Authentification**: SimpleJWT
- **Base de données**: SQLite3 (développement)
- **Traitement de données**: Pandas
- **Génération Excel**: openpyxl (via pandas)
- **CORS**: django-cors-headers

## 📁 Structure du Projet

```
fr-backend/
├── api/
│   └── reports/
│       ├── models.py          # Modèles de données
│       ├── views.py           # Vues API
│       ├── serializers.py     # Sérialiseurs DRF
│       ├── urls.py            # Routes API
│       ├── tft_generator.py   # Générateur TFT
│       └── migrations/        # Migrations DB
├── fr_backend/
│   ├── settings.py            # Configuration Django
│   ├── urls.py               # Routes principales
│   ├── auth_api.py           # Authentification
│   └── wsgi.py               # Configuration WSGI
├── media/
│   └── balances/             # Fichiers CSV uploadés
├── manage.py                 # Script de gestion Django
└── db.sqlite3               # Base de données SQLite
```

## 🚀 Installation et Configuration

### Prérequis
- Python 3.8+
- pip (gestionnaire de paquets Python)

### Installation

1. **Cloner le repository**
```bash
git clone <url-du-repository>
cd fr-backend
```

2. **Créer un environnement virtuel**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **Installer les dépendances**
```bash
pip install django
pip install djangorestframework
pip install djangorestframework-simplejwt
pip install django-cors-headers
pip install pandas
pip install openpyxl
```

4. **Configurer la base de données**
```bash
python manage.py makemigrations
python manage.py migrate
```

5. **Créer un superutilisateur (optionnel)**
```bash
python manage.py createsuperuser
```

6. **Lancer le serveur de développement**
```bash
python manage.py runserver
```

Le serveur sera accessible sur `http://localhost:8000`

## 📚 API Endpoints

### Authentification
- `POST /api/register/` - Inscription d'un nouvel utilisateur
- `POST /api/token/` - Connexion et obtention du token JWT
- `POST /api/token/refresh/` - Renouvellement du token
- `POST /api/logout/` - Déconnexion

### Rapports Financiers
- `POST /api/reports/upload-balance/` - Upload d'un fichier CSV de balance
- `GET /api/reports/balance-history/` - Historique des uploads
- `GET /api/reports/download-generated/<id>/` - Téléchargement d'un fichier généré

## 🔧 Configuration pour la Production

### Variables d'Environnement
Créer un fichier `.env` avec :
```env
SECRET_KEY=votre-clé-secrète-production
DEBUG=False
ALLOWED_HOSTS=votre-domaine.com,www.votre-domaine.com
DATABASE_URL=postgresql://user:password@host:port/database
```

### Base de Données PostgreSQL
```bash
pip install psycopg2-binary
```

Modifier `settings.py` :
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'nom_base',
        'USER': 'utilisateur',
        'PASSWORD': 'mot_de_passe',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### Sécurité
```python
# settings.py
SECRET_KEY = os.environ.get('SECRET_KEY')
DEBUG = False
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

## 🚀 Déploiement

### Déploiement avec Docker

1. **Créer un Dockerfile**
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

2. **Créer un docker-compose.yml**
```yaml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - SECRET_KEY=votre-clé-secrète
      - DEBUG=False
    volumes:
      - ./media:/app/media
      - ./db.sqlite3:/app/db.sqlite3
```

3. **Déployer**
```bash
docker-compose up -d
```

### Déploiement sur Heroku

1. **Créer un Procfile**
```
web: gunicorn fr_backend.wsgi --log-file -
```

2. **Installer gunicorn**
```bash
pip install gunicorn
```

3. **Déployer**
```bash
git add .
git commit -m "Deploy to Heroku"
git push heroku main
```

### Déploiement sur un Serveur VPS

1. **Installer les dépendances système**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv nginx
```

2. **Configurer Nginx**
```nginx
server {
    listen 80;
    server_name votre-domaine.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /media/ {
        alias /chemin/vers/votre/projet/media/;
    }
}
```

3. **Configurer Gunicorn**
```bash
pip install gunicorn
gunicorn fr_backend.wsgi:application --bind 127.0.0.1:8000
```

## 📊 Format des Données CSV

Le système attend un fichier CSV avec les colonnes suivantes :
- `account_number` : Numéro de compte (ex: "411-001", "601-002")
- `balance` : Solde du compte
- `total_debit` : Total des débits (optionnel)
- `total_credit` : Total des crédits (optionnel)
- `created_at` : Date de création (pour le filtrage par période)

## 🔍 Tests

```bash
# Lancer les tests
python manage.py test

# Tests avec couverture
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

## 📝 Logs et Monitoring

### Configuration des Logs
```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

## 🤝 Contribution

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Commit les changements (`git commit -am 'Ajouter nouvelle fonctionnalité'`)
4. Push vers la branche (`git push origin feature/nouvelle-fonctionnalite`)
5. Créer une Pull Request

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 📞 Support

Pour toute question ou problème :
- Créer une issue sur GitHub
- Contacter l'équipe de développement

## 🔄 Changelog

### Version 1.0.0
- Génération automatique de TFT SYSCOHADA
- Système d'authentification JWT
- Upload et traitement de fichiers CSV
- Contrôles de cohérence financière
- Génération de feuilles maîtresses par groupes comptables

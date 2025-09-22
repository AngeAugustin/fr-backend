# 📊 Guide de Chargement CSV vers PostgreSQL

## 🎯 Objectif
Charger le fichier CSV dans PostgreSQL et tester le système de traitement automatique.

## 🚀 Démarrage Rapide

### 1. Charger les Données CSV

```bash
# Activer l'environnement virtuel
& C:/Users/HP/OneDrive/Documents/GitHub/fr_backend/.venv/Scripts/Activate.ps1

# Charger le fichier CSV
python load_csv_to_postgresql.py api_financialreportaccountdetail_with_previous_year.csv
```

### 2. Démarrer le Serveur

```bash
# Dans un terminal séparé
python manage.py runserver
```

### 3. Tester le Système

```bash
# Dans un autre terminal
python test_postgresql_system.py
```

## 📋 Étapes Détaillées

### Étape 1 : Préparation

```bash
# 1. Activer l'environnement virtuel
& C:/Users/HP/OneDrive/Documents/GitHub/fr_backend/.venv/Scripts/Activate.ps1

# 2. Vérifier que Django est installé
python -c "import django; print(f'Django version: {django.get_version()}')"

# 3. Appliquer les migrations
python manage.py migrate
```

### Étape 2 : Chargement des Données

```bash
# Charger le fichier CSV
python load_csv_to_postgresql.py api_financialreportaccountdetail_with_previous_year.csv
```

**Résultat attendu :**
```
🚀 CHARGEMENT CSV VERS POSTGRESQL
==================================================
✅ Connexion à PostgreSQL réussie
🔄 Chargement du fichier: api_financialreportaccountdetail_with_previous_year.csv
📖 Lecture du fichier CSV...
✅ 4042 lignes lues
📋 Colonnes disponibles: ['id', 'account_number', 'account_label', ...]
🔄 Préparation des données...
💾 Insertion de 4042 enregistrements dans PostgreSQL...
✅ 4042 enregistrements chargés avec succès!

📊 Statistiques:
   - Total enregistrements dans la base: 4042
   - Financial Report IDs: 2
     * 657e0127-ff69-473c-843d-5b8c8e036a10: 2021 enregistrements
     * 32974e1a-e8e0-4784-b4e2-489d329d7eaa: 2021 enregistrements
   - Exercices disponibles: [2025]

🎉 CHARGEMENT TERMINÉ AVEC SUCCÈS!
```

### Étape 3 : Test du Système

```bash
# Tester le système complet
python test_postgresql_system.py
```

**Résultat attendu :**
```
🧪 TEST DU SYSTÈME POSTGRESQL
==================================================
✅ PASS Connexion PostgreSQL: Base de données accessible
✅ PASS Données chargées: 4042 enregistrements, 2 financial_report_ids, Exercices: [2025]
✅ PASS Génération TFT: TFT généré (15432 bytes), 10 feuilles maîtresses
✅ PASS Connexion serveur: Serveur accessible
✅ PASS API Traitement: Traitement réussi, ID: 1
✅ PASS Fichiers générés: 1 fichiers TFT, 10 feuilles maîtresses
✅ PASS Téléchargement: Fichier téléchargeable (15432 bytes)
✅ PASS API Historique: 1 entrées dans l'historique

==================================================
📊 RÉSUMÉ DES TESTS
==================================================
Tests réussis: 8/8
Taux de réussite: 100.0%

🎉 TOUS LES TESTS SONT PASSÉS !
Le système PostgreSQL fonctionne parfaitement.
```

## 🔧 APIs Disponibles

### 1. Lister les Données Disponibles
```bash
curl http://localhost:8000/api/reports/process-account-data/
```

### 2. Traiter un Financial Report ID
```bash
curl -X POST http://localhost:8000/api/reports/process-account-data/ \
  -H "Content-Type: application/json" \
  -d '{
    "financial_report_id": "657e0127-ff69-473c-843d-5b8c8e036a10",
    "start_date": "2025-01-01",
    "end_date": "2025-12-31"
  }'
```

### 3. Traitement Automatique
```bash
curl -X POST http://localhost:8000/api/reports/auto-process/
```

### 4. Consulter l'Historique
```bash
curl http://localhost:8000/api/reports/balance-history/
```

### 5. Télécharger les Fichiers
```bash
# Télécharger un fichier TFT
curl http://localhost:8000/api/reports/download-generated/1/

# Télécharger une feuille maîtresse
curl http://localhost:8000/api/reports/download-generated/2/
```

## 🐛 Dépannage

### Problème : ModuleNotFoundError: No module named 'django'
**Solution :**
```bash
& C:/Users/HP/OneDrive/Documents/GitHub/fr_backend/.venv/Scripts/Activate.ps1
pip install django
```

### Problème : Erreur de connexion PostgreSQL
**Solution :** Vérifiez la configuration dans `settings.py`
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_database',
        'USER': 'your_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### Problème : Table 'account_data' doesn't exist
**Solution :**
```bash
python manage.py migrate
```

### Problème : Aucune donnée chargée
**Solution :**
```bash
python load_csv_to_postgresql.py api_financialreportaccountdetail_with_previous_year.csv
```

### Problème : Serveur non accessible
**Solution :**
```bash
python manage.py runserver
```

## 📊 Résultats Attendus

### Après Chargement Réussi
- ✅ 4042 enregistrements dans AccountData
- ✅ 2 financial_report_ids disponibles
- ✅ Données des exercices 2025

### Après Traitement Réussi
- ✅ 1 BalanceUpload créé
- ✅ 1 fichier TFT généré
- ✅ 10 feuilles maîtresses générées
- ✅ Données JSON stockées
- ✅ Entrée dans l'historique

### Fichiers Générés
- **TFT** : Tableau de Financement de Trésorerie (Excel)
- **Feuilles Maîtresses** : Par groupe de comptes (Clients, Fournisseurs, etc.)
- **Données JSON** : Pour l'API et l'affichage

## 🎯 Prochaines Étapes

1. **Charger vos données** avec le script
2. **Tester le système** pour vérifier le fonctionnement
3. **Utiliser les APIs** pour intégrer dans votre application
4. **Télécharger les rapports** générés

Le système est maintenant prêt pour la production ! 🚀

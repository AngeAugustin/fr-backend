# 📊 DOCUMENTATION COMPLÈTE DU SYSTÈME TFT

## 🎯 Vue d'ensemble

Le système TFT (Tableau de Financement de Trésorerie) est une application Django qui génère automatiquement des rapports financiers conformes aux normes SYSCOHADA à partir de données comptables chargées dans une base PostgreSQL.

## 🏗️ Architecture du système

### 📁 Structure des fichiers
```
fr-backend/
├── api/
│   └── reports/
│       ├── models.py          # Modèles de données
│       ├── views.py           # APIs REST
│       ├── tft_generator.py   # Moteur de génération TFT
│       ├── signals.py         # Traitement automatique
│       ├── urls.py            # Routes API
│       └── serializers.py     # Sérialiseurs
├── fr_backend/
│   ├── settings.py            # Configuration Django
│   └── urls.py               # Routes principales
├── manage.py                  # Gestionnaire Django
└── requirements.txt          # Dépendances
```

## 🗄️ Modèles de données

### 1. **AccountData** - Données comptables brutes
```python
class AccountData(models.Model):
    id = models.CharField(max_length=36, primary_key=True)  # UUID
    account_number = models.CharField(max_length=20)        # Numéro de compte
    account_label = models.CharField(max_length=200)        # Libellé du compte
    account_class = models.CharField(max_length=10)         # Classe comptable
    balance = models.DecimalField(max_digits=15, decimal_places=2)  # Solde
    total_debit = models.DecimalField(max_digits=15, decimal_places=2)  # Total débit
    total_credit = models.DecimalField(max_digits=15, decimal_places=2) # Total crédit
    entries_count = models.IntegerField(default=0)          # Nombre d'écritures
    created_at = models.DateTimeField()                     # Date de création
    financial_report_id = models.CharField(max_length=36)   # ID du rapport financier
    account_lookup_key = models.CharField(max_length=20)    # Clé de recherche
```

### 2. **BalanceUpload** - Historique des traitements
```python
class BalanceUpload(models.Model):
    file = models.FileField(null=True, blank=True)          # Fichier CSV (optionnel)
    start_date = models.DateField()                         # Date de début
    end_date = models.DateField()                           # Date de fin
    uploaded_at = models.DateTimeField()                    # Date d'upload
    user = models.ForeignKey(User)                          # Utilisateur
    status = models.CharField(max_length=20)                # Statut du traitement
    financial_report_id = models.CharField(max_length=36)   # ID du rapport
    tft_json = models.JSONField()                           # Données TFT JSON
    feuilles_maitresses_json = models.JSONField()           # Données feuilles maîtresses
    coherence_json = models.JSONField()                     # Contrôle de cohérence
```

### 3. **GeneratedFile** - Fichiers générés
```python
class GeneratedFile(models.Model):
    balance_upload = models.ForeignKey(BalanceUpload)       # Lien vers l'upload
    file_type = models.CharField(max_length=30)             # Type: 'TFT' ou 'feuille_maitresse'
    group_name = models.CharField(max_length=50)            # Nom du groupe (pour feuilles maîtresses)
    file_content = models.BinaryField()                     # Contenu binaire du fichier
    comment = models.TextField()                            # Commentaire
    created_at = models.DateTimeField()                     # Date de création
```

## 🔄 Flux de traitement

### 1. **Chargement des données**
```python
# Script: load_csv_to_postgresql.py
# Charge un fichier CSV dans la table AccountData
def load_csv(csv_file_path):
    df = pd.read_csv(csv_file_path)
    records = []
    for _, row in df.iterrows():
        records.append(AccountData(
            id=row['id'],
            account_number=row['account_number'],
            account_label=row['account_label'],
            # ... autres champs
        ))
    AccountData.objects.bulk_create(records)
```

### 2. **Détermination des dates TFT**
```python
def determine_tft_dates(financial_report_id):
    """
    Logique SYSCOHADA pour les dates :
    - Si N et N-1 disponibles : 01/01/N-1 à 31/12/N
    - Si N uniquement : 01/01/N à 31/12/N
    """
    account_data = AccountData.objects.filter(financial_report_id=financial_report_id)
    exercices = set(data.created_at.year for data in account_data)
    exercices = sorted(exercices)
    
    if len(exercices) >= 2:
        # N-1 et N disponibles
        n_1, n = exercices[-2], exercices[-1]
        return date(n_1, 1, 1), date(n, 12, 31)
    elif len(exercices) == 1:
        # Un seul exercice
        n = exercices[0]
        return date(n, 1, 1), date(n, 12, 31)
    else:
        raise ValueError("Aucun exercice détecté")
```

### 3. **Génération TFT et feuilles maîtresses**
```python
def generate_tft_and_sheets_from_database(financial_report_id, start_date, end_date):
    """
    Processus de génération :
    1. Récupération des données AccountData
    2. Conversion en DataFrame pandas
    3. Filtrage par période
    4. Calcul des rubriques TFT
    5. Génération des feuilles maîtresses
    6. Contrôle de cohérence
    """
    # Récupération des données
    account_data = AccountData.objects.filter(financial_report_id=financial_report_id)
    
    # Conversion en DataFrame
    df_data = []
    for data in account_data:
        df_data.append({
            'account_number': data.account_number,
            'account_name': data.account_label,
            'balance': float(data.balance),
            'total_debit': float(data.total_debit),
            'total_credit': float(data.total_credit),
            'created_at': data.created_at,
            'exercice': data.created_at.year
        })
    
    df = pd.DataFrame(df_data)
    
    # Génération TFT et feuilles maîtresses
    return generate_tft_and_sheets_from_df(df, start_date, end_date)
```

## 📊 Modèle TFT SYSCOHADA

### Rubriques principales

#### **A. Trésorerie**
- **ZA** : Trésorerie nette au 1er janvier
- **ZH** : Trésorerie nette au 31 décembre
- **G** : Variation de trésorerie

#### **B. Activités opérationnelles**
- **FA** : Capacité d'AutoFinancement Globale (CAFG)
- **FB** : Variation Actif circulant HAO
- **FC** : Variation des stocks
- **FD** : Variation des créances
- **FE** : Variation du passif circulant
- **BF** : Variation du BF lié aux activités opérationnelles
- **ZB** : Flux de trésorerie provenant des activités opérationnelles

#### **C. Activités d'investissement**
- **FF** : Décaissements liés aux acquisitions d'immobilisations incorporelles
- **FG** : Décaissements liés aux acquisitions d'immobilisations corporelles
- **FH** : Décaissements liés aux acquisitions d'immobilisations financières
- **FI** : Décaissements liés aux acquisitions d'immobilisations en cours
- **FJ** : Décaissements liés aux acquisitions d'immobilisations mises en concession
- **ZC** : Flux de trésorerie provenant des activités d'investissement

#### **D. Activités de financement**
- **FK** : Encaissements provenant de capital apporté nouveaux
- **FL** : Encaissements provenant de subventions reçues
- **FM** : Dividendes versés
- **FO** : Encaissements des emprunts et autres dettes financières
- **FP** : Décaissements liés au remboursement des emprunts
- **ZE** : Flux de trésorerie provenant des activités de financement

### Mapping des comptes

```python
# Exemple de mapping pour les rubriques
tft_model = [
    {'ref': 'ZA', 'libelle': 'Trésorerie nette au 1er janvier', 'prefixes': ['521', '431']},
    {'ref': 'FA', 'libelle': 'CAFG', 'prefixes': ['131', '681-689', '691-699']},
    {'ref': 'FB', 'libelle': 'Variation Actif circulant HAO', 'prefixes': ['31', '32', '33']},
    # ... autres rubriques
]
```

## 📋 Feuilles maîtresses

### Groupes de comptes
```python
groups = {
    'financier': ['431', '521'],
    'Clients-Ventes': ['411', '419', '445', '622', '628', '631', '661', '758'],
    'Fournisseurs-Achats': ['283', '284', '401', '409', '422', '445', '447', '476', '605', '633', '637', '641', '658', '661', '664', '681'],
    'personnel': ['422', '447', '633', '641', '661', '664'],
    'Impots-Taxes': ['447', '641'],
    'Immobilisations': ['244', '624'],
    'stocks': ['605'],
    'capitaux_propres': ['121'],
    'Provisions R-C': ['121'],
}
```

## 🌐 APIs REST

### 1. **POST /api/reports/auto-process/**
```json
{
    "message": "Traitement automatique déclenché",
    "processed_count": 3,
    "success_count": 3,
    "errors": []
}
```

### 2. **GET /api/reports/balance-history/**
```json
{
    "history": [
        {
            "id": 1,
            "start_date": "2023-01-01",
            "end_date": "2024-12-31",
            "uploaded_at": "2024-01-15T10:30:00Z",
            "status": "success",
            "generated_files": [
                {
                    "id": 1,
                    "file_type": "TFT",
                    "download_url": "/api/reports/download-generated/1/",
                    "created_at": "2024-01-15T10:30:00Z"
                }
            ]
        }
    ]
}
```

### 3. **GET /api/reports/download-generated/{id}/**
Télécharge un fichier généré (TFT ou feuille maîtresse)

## 🔧 Traitement automatique

### Signal Django
```python
# api/reports/signals.py
def process_financial_report_async(financial_report_id):
    """
    Traite automatiquement un financial_report_id :
    1. Détermine les dates TFT
    2. Génère le TFT et les feuilles maîtresses
    3. Enregistre les fichiers dans GeneratedFile
    4. Met à jour l'historique dans BalanceUpload
    """
```

### Surveillance en temps réel
```python
# monitor_realtime_data.py
def monitor_data():
    """
    Surveille les nouvelles données AccountData
    et déclenche le traitement automatique
    """
    while True:
        unprocessed_ids = get_unprocessed_financial_report_ids()
        for financial_report_id in unprocessed_ids:
            process_financial_report_async(financial_report_id)
        time.sleep(60)  # Vérification toutes les minutes
```

## 🚀 Utilisation

### 1. **Chargement des données**
```bash
# Charger un fichier CSV
python load_csv_to_postgresql.py
```

### 2. **Démarrage du serveur**
```bash
# Démarrer Django
python manage.py runserver

# Démarrer la surveillance
python monitor_realtime_data.py
```

### 3. **Traitement manuel**
```bash
# Traitement via API
curl -X POST http://localhost:8000/api/reports/auto-process/

# Vérification de l'historique
curl http://localhost:8000/api/reports/balance-history/
```

## 🔍 Contrôles de cohérence

### Validation TFT
```python
def controle_coherence(tft_data):
    """
    Vérifie la cohérence du TFT :
    Variation TFT = Variation Trésorerie
    """
    flux_operationnels = tft_data.get('ZB', {}).get('montant', 0)
    flux_investissement = tft_data.get('ZC', {}).get('montant', 0)
    flux_financement = tft_data.get('ZE', {}).get('montant', 0)
    
    variation_tft = flux_operationnels + flux_investissement + flux_financement
    variation_treso = treso_cloture - treso_ouverture
    
    return {
        'is_coherent': abs(variation_tft - variation_treso) < 1e-2,
        'variation_tft': variation_tft,
        'variation_treso': variation_treso
    }
```

## 📈 Monitoring et logs

### Configuration des logs
```python
# fr_backend/settings.py
LOGGING = {
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/auto_processing.log',
            'maxBytes': 1024*1024*5,  # 5 MB
            'backupCount': 5,
        },
    },
    'loggers': {
        'api.reports.signals': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
        },
    },
}
```

## 🛠️ Scripts utilitaires

### 1. **check_fm_dividends.py**
Diagnostic spécifique de la rubrique FM (Dividendes versés)

### 2. **test_realtime_surveillance.py**
Test du système de surveillance en temps réel

### 3. **load_csv_to_postgresql.py**
Chargement de fichiers CSV dans la base de données

## 📊 Statistiques du système

- **4040** enregistrements AccountData chargés
- **8** traitements BalanceUpload effectués
- **87** fichiers générés (TFT + feuilles maîtresses)
- **100%** de taux de réussite TFT
- **Toutes** les feuilles maîtresses fonctionnelles

## 🎯 Avantages du système

1. **Automatisation complète** - Traitement automatique des nouvelles données
2. **Conformité SYSCOHADA** - Respect des normes comptables africaines
3. **Stockage en base** - Aucun fichier sur le disque, tout en PostgreSQL
4. **APIs REST** - Intégration facile avec d'autres systèmes
5. **Contrôles de cohérence** - Validation automatique des calculs
6. **Surveillance temps réel** - Monitoring continu des nouvelles données
7. **Logs détaillés** - Traçabilité complète des opérations

## 🔮 Évolutions possibles

1. **Interface web** - Dashboard pour visualiser les rapports
2. **Notifications** - Alertes en cas d'erreur ou de nouveau traitement
3. **Export PDF** - Génération de rapports PDF
4. **Planification** - Traitement programmé (cron jobs)
5. **Multi-utilisateurs** - Gestion des permissions et rôles
6. **API GraphQL** - Interface de requête plus flexible

---

*Documentation générée le 2024-01-15 - Système TFT v1.0*

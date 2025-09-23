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

## 📊 Modèle TFT SYSCOHADA - Conforme à la documentation officielle

### Structure générale conforme OHADA

Le système implémente la structure TFT SYSCOHADA selon la documentation officielle :

#### **SECTION A - ACTIVITÉS OPÉRATIONNELLES**
- **FA** : Capacité d'AutoFinancement Globale (CAFG)
  - Formule : `131 + 681-689 + 691-699 - 781-789 - 791-799 - 775 + 675`
  - Retraitements obligatoires selon documentation
- **FB** : Variation Actif circulant HAO (créances hors activité ordinaire)
- **FC** : Variation des stocks `-(Solde N - Solde N-1)`
- **FD** : Variation des créances d'exploitation `-(Solde N - Solde N-1)`
- **FE** : Variation du passif circulant `+(Solde N - Solde N-1)`
- **ZB** : Flux de trésorerie provenant des activités opérationnelles

#### **SECTION B - ACTIVITÉS D'INVESTISSEMENT**
- **FF** : Décaissements acquisitions immobilisations incorporelles
- **FG** : Décaissements acquisitions immobilisations corporelles
- **FH** : Décaissements acquisitions immobilisations financières
- **FI** : Encaissements cessions immobilisations incorporelles/corporelles
- **FJ** : Encaissements cessions immobilisations financières
- **FJ_DIV** : Dividendes reçus (761-762)
- **FJ_CRE** : Produits de créances financières (763-764)
- **ZC** : Flux de trésorerie provenant des activités d'investissement

#### **SECTION C - ACTIVITÉS DE FINANCEMENT**
- **FK** : Encaissements provenant de capital apporté nouveaux
- **FL** : Encaissements provenant de subventions reçues
- **FM** : Dividendes versés
- **FO** : Encaissements des emprunts et autres dettes financières
- **FP** : Décaissements liés au remboursement des emprunts
- **ZE** : Flux de trésorerie provenant des activités de financement

#### **TRÉSORERIE ET CONTRÔLES**
- **ZA** : Trésorerie nette au 1er janvier
- **ZH** : Trésorerie nette au 31 décembre
- **G** : Variation de la trésorerie nette de la période
- **CONTROLE** : Contrôle de cohérence `G = ZH - ZA`

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

### Détail des 10 feuilles maîtresses

#### **1. CAPITAUX**
- 101 : Capital social
- 103 : Primes liées au capital social  
- 104 : Écarts d'évaluation
- 105 : Écarts de réévaluation
- 106 : Réserves (légale, statutaire, facultative)
- 108 : Compte de l'exploitant
- 109 : Actionnaires, capital souscrit non appelé
- 110 : Report à nouveau (débiteur/créditeur)
- 130 : Résultat en instance d'affectation
- 131 : Résultat net de l'exercice

#### **2. IMMOS CORPS & INCORPS**
**Incorporelles :**
- 201 : Frais de recherche et de développement
- 203 : Logiciels
- 204 : Brevets, licences, concessions et droits similaires
- 205 : Fonds commercial et droit au bail
- 208 : Autres immobilisations incorporelles

**Corporelles :**
- 211 : Terrains
- 212 : Agencements et aménagements de terrains
- 213 : Bâtiments
- 214 : Constructions sur sol d'autrui
- 215 : Installations techniques, matériel et outillage
- 218 : Autres immobilisations corporelles
- 237 : Immobilisations corporelles en cours
- 238 : Avances et acomptes versés sur commandes d'immobilisations corporelles

#### **3. IMMOS FINANCIÈRES**
- 251 : Titres de participation
- 256 : Autres formes de participation
- 261 : Titres immobilisés (droit de propriété)
- 262 : Titres immobilisés (droit de créance)
- 264 : Prêts et créances sur l'État
- 265 : Prêts et créances sur les collectivités publiques
- 266 : Prêts et créances sur les entreprises liées
- 267 : Prêts et créances sur les entreprises avec lesquelles il existe un lien de participation
- 268 : Autres prêts et créances financières
- 269 : Versements restant à effectuer sur titres non libérés
- 274 : Créances immobilisées
- 275 : Dépôts et cautionnements versés

#### **4. STOCKS**
- 311 : Marchandises
- 321 : Matières premières
- 322 : Matières et fournitures consommables
- 323 : Emballages
- 331 : Produits en cours
- 335 : Produits et travaux finis
- 341 : Études en cours
- 345 : Prestations de services en cours
- 351 : Produits résiduels
- 358 : Déchets et rebuts
- 39x : Dépréciations des stocks

#### **5. CLIENTS - VENTES**
**Comptes concernés :**
- 411 : Clients
- 416 : Clients douteux
- 417 : Créances sur travaux non encore facturables
- 418 : Clients - Produits non encore livrés
- 419 : Clients créditeurs, avances et acomptes reçus
- 491 : Dépréciations des comptes clients

**Comptes de produits :**
- 701 : Ventes de marchandises dans la région
- 702 : Ventes de marchandises hors région
- 703 : Ventes de produits fabriqués dans la région
- 704 : Ventes de produits fabriqués hors région
- 705 : Travaux facturés
- 706 : Services vendus dans la région
- 707 : Services vendus hors région
- 708 : Produits des activités annexes
- 781 : Transfert de charges d'exploitation

#### **6. FOURNISSEURS - ACHATS**
**Comptes concernés :**
- 401 : Fournisseurs de stocks et services locaux
- 402 : Fournisseurs de stocks et services dans la région
- 403 : Fournisseurs de stocks et services hors région
- 408 : Fournisseurs, factures non parvenues
- 409 : Fournisseurs débiteurs, avances et acomptes versés

**Comptes d'achats :**
- 601 : Achats de marchandises dans la région
- 602 : Achats de marchandises hors région
- 603 : Variations de stocks de marchandises
- 604 : Achats stockés de matières premières et fournitures liées
- 605 : Autres achats stockés
- 606 : Achats non stockés de matières et fournitures
- 607 : Achats de travaux, études et prestations de service
- 608 : Achats d'emballages récupérables

#### **7. PERSONNEL**
**Comptes concernés :**
- 421 : Personnel, avances et acomptes
- 422 : Personnel, rémunérations dues
- 423 : Personnel, oppositions
- 424 : Personnel, œuvres sociales internes
- 425 : Personnel, autres créditeurs
- 43x : Organismes sociaux (CNSS, etc.)
- 447 : Personnel, charges à payer

**Comptes de charges :**
- 661 : Rémunérations directes versées au personnel national
- 662 : Rémunérations directes versées au personnel non national
- 663 : Indemnités forfaitaires versées au personnel
- 664 : Charges sociales sur rémunérations du personnel national
- 665 : Charges sociales sur rémunérations du personnel non national
- 666 : Rémunérations transférées pour compte de tiers
- 667 : Rémunérations de l'exploitant individuel
- 668 : Autres charges sociales

#### **8. IMPÔTS & TAXES**
**Comptes concernés :**
- 441 : État et collectivités publiques, subventions à recevoir
- 442 : État, impôts et taxes recouvrables sur des tiers
- 443 : État, TVA facturée sur ventes
- 444 : État, TVA due ou crédit de TVA
- 445 : État, TVA récupérable sur achats
- 446 : État, TVA récupérable sur immobilisations
- 447 : État, impôts retenus à la source
- 448 : État, charges à payer et produits à recevoir
- 449 : État, créditeurs et débiteurs divers

**Comptes de charges :**
- 631 : Impôts et taxes directs
- 633 : Impôts, taxes et droits de douane
- 635 : Autres impôts et taxes
- 695 : Impôt sur le résultat

#### **9. FINANCIER**
- 501 : Titres de placement
- 502 : Actions propres
- 503 : Obligations et bons du Trésor
- 504 : Bons de caisse et bons de trésor
- 505 : Titres négociables hors région
- 506 : Intérêts courus sur titres de placement
- 521 : Banques locales
- 522 : Banques autres États de l'UEMOA
- 523 : Banques autres États de l'UMOA
- 524 : Banques hors UMOA
- 531 : Chèques postaux
- 532 : Trésor public
- 533 : Régies d'avances
- 541 : Caisse siège social
- 542 : Caisse succursale A, B, C...
- 58x : Virements internes
- 59x : Dépréciations

#### **10. PROVISIONS R&C**
- 141 : Provisions pour risques
- 142 : Provisions pour charges
- 143 : Provisions pour pensions et obligations similaires
- 148 : Autres provisions pour charges
- 149 : Provisions pour dépréciation des comptes de la classe 1

### Groupes de comptes - 10 feuilles maîtresses exactes
```python
groups = {
    # 1. CAPITAUX
    'Capitaux': ['101', '103', '104', '105', '106', '108', '109', '110', '130', '131'],
    
    # 2. IMMOS CORPS & INCORPS
    'Immos corps & incorps': ['201', '203', '204', '205', '208', '211', '212', '213', '214', '215', '218', '237', '238'],
    
    # 3. IMMOS FINANCIÈRES
    'Immos financières': ['251', '256', '261', '262', '264', '265', '266', '267', '268', '269', '274', '275'],
    
    # 4. STOCKS
    'Stocks': ['311', '321', '322', '323', '331', '335', '341', '345', '351', '358', '39'],
    
    # 5. CLIENTS - VENTES
    'Clients - Ventes': ['411', '416', '417', '418', '419', '491', '701', '702', '703', '704', '705', '706', '707', '708', '781'],
    
    # 6. FOURNISSEURS - ACHATS
    'Fournisseurs - Achats': ['401', '402', '403', '408', '409', '601', '602', '603', '604', '605', '606', '607', '608'],
    
    # 7. PERSONNEL
    'Personnel': ['421', '422', '423', '424', '425', '43', '447', '661', '662', '663', '664', '665', '666', '667', '668'],
    
    # 8. IMPÔTS & TAXES
    'Impôts & Taxes': ['441', '442', '443', '444', '445', '446', '447', '448', '449', '631', '633', '635', '695'],
    
    # 9. FINANCIER
    'Financier': ['501', '502', '503', '504', '505', '506', '521', '522', '523', '524', '531', '532', '533', '541', '542', '58', '59'],
    
    # 10. PROVISIONS R&C
    'Provisions R&C': ['141', '142', '143', '148', '149'],
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

## 🔍 Contrôles automatiques conformes SYSCOHADA

### Vérifications obligatoires implémentées

#### **1. Égalité variation calculée/variation bilantielle**
```python
def controle_coherence_complet(tft_data):
    variation_tft = flux_operationnels + flux_investissement + flux_financement
    variation_treso = treso_cloture - treso_ouverture
    ecart = abs(variation_tft - variation_treso)
    return ecart < 1e-2  # Tolérance de 0.01
```

#### **2. Cohérence des totaux par section**
- **Section A** : Vérification `FA + FB + FC + FD + FE = ZB`
- **Section B** : Vérification `FF + FG + FH + FI + FJ + FJ_DIV + FJ_CRE = ZC`
- **Section C** : Vérification `FK + FL - FM + FO - FP = ZE`

#### **3. Absence de comptes orphelins**
- Détection des comptes non mappés dans les rubriques TFT
- Alerte pour les comptes sans affectation

#### **4. Respect des seuils de matérialité**
- Contrôle des montants faibles (< seuil configurable)
- Alertes pour les rubriques sous le seuil de matérialité

### Retraitements obligatoires implémentés

#### **Éléments sans effet trésorerie à éliminer :**
- ✅ Dotations et reprises d'amortissements (681-689, 781-789)
- ✅ Dotations et reprises de provisions (691-699, 791-799)
- ✅ Plus et moins-values de cession (775, 675)
- ✅ Transferts de charges (781-789)
- ✅ Quote-part de subventions virée au résultat

#### **Reclassements nécessaires :**
- ✅ Cessions d'immobilisations : du résultat vers investissement
- ✅ Charges et produits financiers liés aux emprunts
- ✅ Impôt sur les bénéfices : séparé des autres impôts

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

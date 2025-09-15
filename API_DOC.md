# Documentation API - fr_backend

## API Upload Balance

### Endpoint
`POST /api/reports/upload-balance/`

### Description
Permet d'uploader un fichier de balance comptable (CSV) pour générer le TFT et les feuilles maîtresses.

### Paramètres attendus
- `file` : Fichier CSV de la balance
- `start_date` : Date de début de l'exercice (format YYYY-MM-DD)
- `end_date` : Date de fin de l'exercice (format YYYY-MM-DD)

### Réponse (succès)
```json
{
  "tft_json": { ... },
  "feuilles_maitresses_json": { ... },
  "coherence": { ... },
  "history": { ... }
}
```
- `tft_json` : Données du Tableau de Flux de Trésorerie (TFT)
- `feuilles_maitresses_json` : Données des feuilles maîtresses (groupes de comptes)
- `coherence` : Contrôle de cohérence du TFT
- `history` : Métadonnées et liens de téléchargement des fichiers générés

### Réponse (erreur)
```json
{
  "error": "..."
}
```

---

## API Balance History

### Endpoint
`GET /api/reports/balance-history/`

### Description
Retourne l'historique des balances uploadées, avec leurs données TFT, feuilles maîtresses, cohérence et liens de téléchargement.

### Réponse
```json
{
  "history": [
    {
      "id": 1,
      "file": "...",
      "start_date": "YYYY-MM-DD",
      "end_date": "YYYY-MM-DD",
      "uploaded_at": "...",
      "status": "success",
      "error_message": null,
      "generated_files": [
        {
          "file_type": "TFT",
          "group_name": null,
          "download_url": "/api/reports/download-generated/1/",
          "created_at": "..."
        },
        ...
      ],
      "tft_json": { ... },
      "feuilles_maitresses_json": { ... },
      "coherence": { ... }
    },
    ...
  ]
}
```

### Contenu détaillé
- `generated_files` : Liste des fichiers générés (TFT et feuilles maîtresses) avec liens de téléchargement
- `tft_json` : Données du TFT pour la balance
- `feuilles_maitresses_json` : Données des feuilles maîtresses
- `coherence` : Contrôle de cohérence du TFT

### Notes
- Les données JSON sont stockées lors de l'upload et lues directement pour chaque historique
- Les fichiers générés sont téléchargeables via les liens fournis

---

## Bonnes pratiques
- Utiliser le format CSV attendu pour la balance (voir structure dans le code)
- Vérifier les dates d'exercice
- Utiliser l'API Upload avant de consulter l'historique

---

## Exemple d'utilisation
### Upload
```bash
curl -X POST -F "file=@ma_balance.csv" -F "start_date=2024-01-01" -F "end_date=2024-12-31" http://127.0.0.1:8000/api/reports/upload-balance/
```

### Historique
```bash
curl http://127.0.0.1:8000/api/reports/balance-history/
```

### Exemple de contenu JSON retourné
```json
{
  "history": [
    {
      "id": 1,
      "file": "/media/balances/api_financialreportaccountdetail_XXXX.csv",
      "start_date": "2024-01-01",
      "end_date": "2024-12-31",
      "uploaded_at": "2025-09-15T11:54:57",
      "status": "success",
      "error_message": null,
      "generated_files": [
        {
          "file_type": "TFT",
          "group_name": null,
          "download_url": "/api/reports/download-generated/1/",
          "created_at": "2025-09-15T11:54:57"
        },
        {
          "file_type": "feuille_maitresse",
          "group_name": "Clients-Ventes",
          "download_url": "/api/reports/download-generated/2/",
          "created_at": "2025-09-15T11:54:57"
        }
      ],
      "tft_json": {
        "ZA": {"libelle": "Trésorerie nette au 1er janvier", "montant": 10000, ...},
        "ZB": {"libelle": "Flux opérationnels", "montant": 5000, ...},
        ...
      },
      "feuilles_maitresses_json": {
        "Clients-Ventes": {"solde_n": 12000, "solde_n1": 11000, "variation": 1000, ...},
        "Fournisseurs-Achats": {"solde_n": 8000, ...},
        ...
      },
      "coherence": {
        "variation_tft": 7000,
        "variation_treso": 7000,
        "is_coherent": true,
        "details": { ... }
      }
    }
  ]
}
```

---

## Contact
Pour toute question, contactez l'équipe technique.

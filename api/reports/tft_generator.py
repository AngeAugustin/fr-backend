import pandas as pd
import os

def generate_tft_and_sheets(csv_path, start_date, end_date):
    # Lecture du CSV
    df = pd.read_csv(csv_path)
    # Filtrage par période (si la colonne created_at correspond à la date d'écriture)
    if 'created_at' in df.columns:
        df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
        # Convertir toutes les dates en timezone-naive
        if df['created_at'].dt.tz is not None:
            df['created_at'] = df['created_at'].dt.tz_convert(None)
        else:
            df['created_at'] = df['created_at'].dt.tz_localize(None)
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        df = df[(df['created_at'] >= start_dt) & (df['created_at'] <= end_dt)]

    # Mapping SYSCOHADA détaillé
    groups = {
        'financier': ['50', '51', '53'],
        'clients': ['41', '70', '4457'],
        'fournisseurs': ['40', '60', '4456'],
        'personnel': ['42', '64'],
        'impots': ['44', '63'],
        'immobilisations': ['20', '21', '23'],  # corporelles + incorporelles
        'immobilisations_financieres': ['26', '27'],
        'stocks': ['31', '32', '33', '34', '35', '36', '37'],
        'capitaux_propres': ['10', '11', '12', '13', '14'],
        'provisions_dettes': ['15', '16', '17', '18', '19'],
    }

    tft_mapping = {
        'Actif Immobilisé': ['20', '21', '23', '26', '27'],
        'Actif Circulant': ['31', '32', '33', '34', '35', '36', '37', '40', '41', '42', '43', '44', '45', '50', '51', '53'],
        'Capitaux Propres': ['10', '11', '12', '13', '14'],
        'Passif Non Courant': ['15', '16'],
        'Passif Courant': ['40', '42', '44', '45', '46'],
        'Produits': ['70', '71', '72', '74'],
        'Charges': ['60', '61', '62', '63', '64', '65'],
    }

    # Fonction utilitaire pour filtrer par préfixe de numéro de compte
    def filter_by_prefix(df, prefixes):
        # Certains comptes (ex: 4457, 4456) sont sur 4 chiffres
        prefixes = set(prefixes)
        def match_prefix(acc):
            acc = str(acc)
            for p in prefixes:
                if acc.startswith(p):
                    return True
            return False
        return df[df['account_number'].apply(match_prefix)]

    # Génération des feuilles maîtresses
    sheets_contents = {}
    sheets_data = {}
    from io import BytesIO
    for group_name, prefixes in groups.items():
        group_df = filter_by_prefix(df, prefixes)
        output = BytesIO()
        group_df.to_excel(output, index=False)
        sheets_contents[group_name] = output.getvalue()
        sheets_data[group_name] = group_df.to_dict(orient='records')

    # Modèle TFT SYSCOHADA (exemple simplifié, à compléter selon le guide)
    # Modèle TFT conforme au tableau fourni
    # Préfixes à adapter selon la structure de ton plan comptable
    tft_model = [
        {'ref': 'ZA', 'libelle': 'Trésorerie nette au 1er janvier', 'formule': 'Trésorerie actif N-1 - Trésorerie passif N-1', 'prefixes': ['50', '51', '53']},
        {'ref': 'FA', 'libelle': 'Capacité d’AutoFinancement Globale (CAFG)', 'formule': None, 'prefixes': ['70', '71', '72', '74', '60', '61', '62', '63', '64', '65']},
        {'ref': 'FB', 'libelle': 'Variation Actif circulant HAO', 'formule': None, 'prefixes': ['31', '32', '33', '34', '35', '36', '37']},
        {'ref': 'FC', 'libelle': 'Variation des stocks', 'formule': None, 'prefixes': ['31', '32', '33', '34', '35', '36', '37']},
        {'ref': 'FD', 'libelle': 'Variation des créances', 'formule': None, 'prefixes': ['41']},
        {'ref': 'FE', 'libelle': 'Variation du passif circulant', 'formule': None, 'prefixes': ['40', '44', '45', '46']},
        {'ref': 'BF', 'libelle': 'Variation du BF lié aux activités opérationnelles', 'formule': 'FB+FC+FD-FE', 'prefixes': []},
        {'ref': 'ZB', 'libelle': 'Flux de trésorerie provenant des activités opérationnelles (somme FA à FE)', 'formule': 'FA+FB+FC+FD+FE', 'prefixes': []},
        {'ref': 'FF', 'libelle': 'Décaissements liés aux acquisitions d’immobilisations incorporelles', 'formule': None, 'prefixes': ['20']},
        {'ref': 'FG', 'libelle': 'Décaissements liés aux acquisitions d’immobilisations corporelles', 'formule': None, 'prefixes': ['21']},
        {'ref': 'FH', 'libelle': 'Décaissements liés aux acquisitions d’immobilisations financières', 'formule': None, 'prefixes': ['26', '27']},
        {'ref': 'FI', 'libelle': 'Encaissements liés aux cessions d’immobilisations incorporelles et corporelles', 'formule': None, 'prefixes': ['20', '21']},
        {'ref': 'FJ', 'libelle': 'Encaissements liés aux cessions d’immobilisations financières', 'formule': None, 'prefixes': ['26', '27']},
        {'ref': 'ZC', 'libelle': 'Flux de trésorerie provenant des activités d’investissement (somme FF à FJ)', 'formule': 'FF+FG+FH+FI+FJ', 'prefixes': []},
        {'ref': 'FK', 'libelle': 'Encaissements provenant de capital apporté nouveaux', 'formule': None, 'prefixes': ['10', '11', '12', '13', '14']},
        {'ref': 'FL', 'libelle': 'Encaissements provenant de subventions reçues', 'formule': None, 'prefixes': ['14']},
        {'ref': 'FM', 'libelle': 'Dividendes versés', 'formule': None, 'prefixes': []},
        {'ref': 'D', 'libelle': 'Flux de trésorerie provenant des capitaux propres (somme FK à FM)', 'formule': 'FK+FL-FM', 'prefixes': []},
        {'ref': 'FO', 'libelle': 'Encaissements des emprunts et autres dettes financières', 'formule': None, 'prefixes': ['15', '16', '17', '18', '19']},
        {'ref': 'FP', 'libelle': 'Décaissements liés au remboursement des emprunts et autres dettes financières', 'formule': None, 'prefixes': ['15', '16', '17', '18', '19']},
        {'ref': 'ZE', 'libelle': 'Flux de trésorerie provenant des activités de financement (FO-FP)', 'formule': 'FO-FP', 'prefixes': []},
        {'ref': 'G', 'libelle': 'VARIATION DE LA TRÉSORERIE NETTE DE LA PÉRIODE (D+B+C+F)', 'formule': 'D+B+C+F', 'prefixes': []},
        {'ref': 'ZH', 'libelle': 'Trésorerie nette au 31 Décembre (G+A)', 'formule': 'G+A', 'prefixes': ['50', '51', '53']},
    ]

    # Calcul des montants pour chaque ligne avec application des règles SYSCOHADA
    # On suppose que le CSV contient une colonne 'exercice' ou 'periode' pour distinguer N et N-1
    # Si non, il faudra adapter la structure du CSV ou demander deux fichiers
    tft_rows = []
    tft_data = {}
    montant_refs = {}
    # On prépare les DataFrames N et N-1
    if 'exercice' in df.columns:
        # N = exercice max, N-1 = exercice précédent
        exercices = sorted(df['exercice'].unique())
        n = exercices[-1]
        n_1 = exercices[-2] if len(exercices) > 1 else n
        df_n = df[df['exercice'] == n]
        df_n1 = df[df['exercice'] == n_1]
    else:
        # Si pas de colonne, on considère tout comme N
        df_n = df.copy()
        df_n1 = pd.DataFrame(columns=df.columns)

    for ligne in tft_model:
        comptes_n = filter_by_prefix(df_n, ligne['prefixes']) if ligne['prefixes'] else pd.DataFrame()
        comptes_n1 = filter_by_prefix(df_n1, ligne['prefixes']) if ligne['prefixes'] else pd.DataFrame()
        solde_n = comptes_n['balance'].sum() if not comptes_n.empty else 0
        solde_n1 = comptes_n1['balance'].sum() if not comptes_n1.empty else 0
        variation = solde_n - solde_n1
        # Pour les flux, on peut utiliser total_debit/total_credit si pertinent
        debit_n = comptes_n['total_debit'].sum() if 'total_debit' in comptes_n else 0
        credit_n = comptes_n['total_credit'].sum() if 'total_credit' in comptes_n else 0
        montant = None
        comptes = comptes_n.to_dict(orient='records')
        if ligne['formule']:
            formule = ligne['formule']
            for ref in montant_refs:
                formule = formule.replace(ref, f"({montant_refs[ref]['montant']})")
            try:
                montant = eval(formule)
            except Exception:
                montant = None
        else:
            montant = solde_n
        montant_refs[ligne['ref']] = {
            'montant': montant if montant is not None else 0,
            'solde_n': solde_n,
            'solde_n1': solde_n1,
            'variation': variation,
            'debit_n': debit_n,
            'credit_n': credit_n
        }
        tft_rows.append({
            'Réf': ligne['ref'],
            'Libellé': ligne['libelle'],
            'Montant': montant,
            'Solde_N': solde_n,
            'Solde_N-1': solde_n1,
            'Variation': variation,
            'Débit_N': debit_n,
            'Crédit_N': credit_n,
            'Formule': ligne['formule']
        })
        tft_data[ligne['ref']] = {
            'libelle': ligne['libelle'],
            'montant': montant,
            'solde_n': solde_n,
            'solde_n1': solde_n1,
            'variation': variation,
            'debit_n': debit_n,
            'credit_n': credit_n,
            'formule': ligne['formule'],
            'comptes': comptes
        }

    tft_df = pd.DataFrame(tft_rows)
    tft_output = BytesIO()
    tft_df.to_excel(tft_output, index=False)
    tft_content = tft_output.getvalue()
    # Feuilles maîtresses : solde N, N-1, variation, correspondance TFT
    for group_name, prefixes in groups.items():
        group_n = filter_by_prefix(df_n, prefixes)
        group_n1 = filter_by_prefix(df_n1, prefixes)
        solde_n = group_n['balance'].sum() if not group_n.empty else 0
        solde_n1 = group_n1['balance'].sum() if not group_n1.empty else 0
        variation = solde_n - solde_n1
        sheets_data[group_name] = {
            'solde_n': solde_n,
            'solde_n1': solde_n1,
            'variation': variation,
            'comptes_n': group_n.to_dict(orient='records'),
            'comptes_n1': group_n1.to_dict(orient='records'),
            'correspondance_tft': [ref for ref in tft_data if set(prefixes) & set(tft_model[[l['ref'] for l in tft_model].index(ref)]['prefixes'])]
        }
    return tft_content, sheets_contents, tft_data, sheets_data

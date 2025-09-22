import pandas as pd
import os
from io import BytesIO

def generate_tft_and_sheets(csv_path, start_date, end_date):
    # Contrôle de cohérence TFT
    def controle_coherence(tft_data):
        # Références des rubriques
        flux_operationnels = tft_data.get('ZB', {}).get('montant', 0)
        flux_investissement = tft_data.get('ZC', {}).get('montant', 0)
        flux_financement = tft_data.get('ZE', {}).get('montant', 0)
        treso_ouverture = tft_data.get('ZA', {}).get('montant', 0)
        treso_cloture = tft_data.get('ZH', {}).get('montant', 0)
        treso_ouverture = treso_ouverture if treso_ouverture is not None else 0
        treso_cloture = treso_cloture if treso_cloture is not None else 0
        variation_tft = flux_operationnels + flux_investissement + flux_financement
        variation_treso = (treso_cloture or 0) - (treso_ouverture or 0)
        return {
            'variation_tft': variation_tft,
            'variation_treso': variation_treso,
            'is_coherent': abs(variation_tft - variation_treso) < 1e-2,
            'details': {
                'flux_operationnels': flux_operationnels,
                'flux_investissement': flux_investissement,
                'flux_financement': flux_financement,
                'treso_ouverture': treso_ouverture,
                'treso_cloture': treso_cloture
            }
        }

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
        # Ajout de la colonne 'exercice' à partir de l'année de 'created_at'
        df['exercice'] = df['created_at'].dt.year

    # Mapping SYSCOHADA détaillé
    groups = {
        'financier': ['501', '502', '503', '504', '505', '506', '521', '522', '523', '524', '531', '532', '533', '541', '542', '58', '59'],
        'Clients-Ventes': ['411', '416', '417', '418', '419', '491', '701', '702', '703', '704', '705', '706', '707', '708', '781'],
        'Fournisseurs-Achats': ['401', '402', '403', '408', '409', '419', '601', '602', '603', '604', '605', '606', '607', '608'],
        'personnel': ['421', '422', '423', '424', '425', '43', '447', '661', '662', '663', '664', '665', '666', '667', '668'],
        'Impots-Taxes': ['441', '442', '443', '444', '445', '446', '447', '448', '449', '631', '633', '635', '695'],
        'Immobilisations Corporelles - Incorporelles': ['201', '203', '204', '205', '208', '211', '212', '213', '214', '215', '218', '237', '238'],
        'immobilisations_financieres': ['251', '256', '261', '262', '264', '265', '266', '267', '268', '269', '274', '275'],
        'stocks': ['311', '321', '322', '323', '331', '335', '341', '345', '351', '358', '39'],
        'capitaux_propres': ['101', '103', '104', '105', '106', '108', '109', '110', '130', '131'],
        'Provisions R-C': ['141', '142', '143', '148', '149'],
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
            # Extraire la partie avant le tiret, enlever les zéros initiaux
            base = acc.split('-')[0].lstrip('0')
            # Préfixe sur 2 ou 3 chiffres selon le modèle (ici 2 par défaut)
            for p in prefixes:
                if base.startswith(p):
                    return True
            return False
        return df[df['account_number'].apply(match_prefix)]

    # Génération des feuilles maîtresses (sera déplacée après la définition de df_n et df_n1)

    # Modèle TFT SYSCOHADA (exemple simplifié, à compléter selon le guide)
    # Modèle TFT conforme au tableau fourni
    # Préfixes à adapter selon la structure de ton plan comptable
    tft_model = [
    {'ref': '2H_TRESO_NEG', 'libelle': "Trésorerie passive (négative) - concours et escomptes", 'formule': None, 'prefixes': ['561', '564', '565']},
    {'ref': '2H_TRESO_POS', 'libelle': "Trésorerie active (positive) - composition détaillée", 'formule': None, 'prefixes': ['521', '522', '523', '524', '531', '532', '541', '542', '501', '502', '503', '504', '505', '506']},
        {'ref': 'ZA', 'libelle': 'Trésorerie nette au 1er janvier', 'formule': 'Trésorerie actif N-1 - Trésorerie passif N-1', 'prefixes': ['50', '51', '53']},
        {'ref': 'FA', 'libelle': 'Capacité d’AutoFinancement Globale (CAFG)', 'formule': None, 'prefixes': ['131', '681-689', '691-699', '781-789', '791-799', '775', '675']},
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
        {'ref': 'FJ', 'libelle': 'Encaissements liés aux cessions d’immobilisations financières', 'formule': None, 'prefixes': ['26', '27', '251', '261', '262']},
        {'ref': 'FJ_VMP', 'libelle': 'Produits nets sur cessions VMP (767)', 'formule': None, 'prefixes': ['767']},
        {'ref': 'INV_DIV', 'libelle': "Dividendes reçus (761-762)", 'formule': None, 'prefixes': ['761', '762']},
        {'ref': 'INV_CRE', 'libelle': "Produits de créances financières (763-764)", 'formule': None, 'prefixes': ['763', '764']},
        {'ref': 'ZC', 'libelle': 'Flux de trésorerie provenant des activités d’investissement (somme FF à FJ)', 'formule': 'FF+FG+FH+FI+FJ', 'prefixes': []},
        {'ref': 'FK', 'libelle': 'Encaissements provenant de capital apporté nouveaux', 'formule': None, 'prefixes': ['10', '11', '12', '13', '14']},
        {'ref': 'T4_101', 'libelle': "Capital social (101) - hors apports en nature", 'formule': None, 'prefixes': ['101']},
        {'ref': 'T4_103', 'libelle': "Primes d'émission (103) - encaissements effectifs", 'formule': None, 'prefixes': ['103']},
        {'ref': 'T4_104', 'libelle': "Écarts d'évaluation (104) - non concerné", 'formule': None, 'prefixes': ['104']},
        {'ref': 'FL', 'libelle': 'Encaissements provenant de subventions reçues', 'formule': None, 'prefixes': ['14']},
        {'ref': 'T5_141', 'libelle': "Subventions d'investissement reçues (141) - hors reprises (865)", 'formule': None, 'prefixes': ['141']},
        {'ref': 'FM', 'libelle': 'Dividendes versés', 'formule': None, 'prefixes': []},
        {'ref': 'TH1_108', 'libelle': "Compte de l'exploitant (108) - prélèvements nets", 'formule': None, 'prefixes': ['108']},
        {'ref': 'TH2_457', 'libelle': "Dividendes à payer (457) - distributions décidées/payées", 'formule': None, 'prefixes': ['457']},
        {'ref': 'D', 'libelle': 'Flux de trésorerie provenant des capitaux propres (somme FK à FM)', 'formule': 'FK+FL-FM', 'prefixes': []},
        {'ref': 'FO', 'libelle': 'Encaissements des emprunts et autres dettes financières', 'formule': None, 'prefixes': ['15', '16', '17', '18', '19']},
        {'ref': 'FP', 'libelle': 'Décaissements liés au remboursement des emprunts et autres dettes financières', 'formule': None, 'prefixes': ['15', '16', '17', '18', '19']},
    {'ref': 'TG_161_168', 'libelle': "Nouveaux emprunts (161-168) - augmentation/variation nette", 'formule': None, 'prefixes': ['161', '162', '163', '164', '165', '168']},
    {'ref': 'TP_161_168', 'libelle': "Remboursements d'emprunts (161-168) - capital remboursé uniquement", 'formule': None, 'prefixes': ['161', '162', '163', '164', '165', '168']},
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
        exercices = sorted(df['exercice'].unique())
        n = exercices[-1]
        if len(exercices) > 1:
            n_1 = exercices[-2]
            df_n = df[df['exercice'] == n]
            df_n1 = df[df['exercice'] == n_1]
        else:
            # Un seul exercice disponible
            df_n = df[df['exercice'] == n]
            # Créer un DataFrame vide pour N-1 avec les mêmes colonnes
            df_n1 = pd.DataFrame(columns=df.columns)
    else:
        # Si pas de colonne, on considère tout comme N
        df_n = df.copy()
        df_n1 = pd.DataFrame(columns=df.columns)

    for ligne in tft_model:
        if ligne['ref'] == 'FA':
            cafg_comptes = [
                {'prefixes': ['131'], 'sign': 1},
                {'prefixes': [str(i) for i in range(681, 690)], 'sign': 1},
                {'prefixes': [str(i) for i in range(691, 700)], 'sign': 1},
                {'prefixes': [str(i) for i in range(781, 790)], 'sign': -1},
                {'prefixes': [str(i) for i in range(791, 800)], 'sign': -1},
                {'prefixes': ['775'], 'sign': -1},
                {'prefixes': ['675'], 'sign': 1},
            ]
            montant = 0
            comptes = []
            for item in cafg_comptes:
                comptes_n = filter_by_prefix(df_n, item['prefixes'])
                solde = comptes_n['balance'].sum() if not comptes_n.empty else 0
                montant += item['sign'] * solde
                comptes.extend(comptes_n.to_dict(orient='records'))
            solde_n = montant
            # Si N-1 existe, calculer, sinon mettre à zéro
            solde_n1 = None if df_n1.empty else 0
            variation = None if df_n1.empty else 0
            debit_n = None
            credit_n = None
        else:
            comptes_n = filter_by_prefix(df_n, ligne['prefixes']) if ligne['prefixes'] else pd.DataFrame()
            comptes_n1 = filter_by_prefix(df_n1, ligne['prefixes']) if ligne['prefixes'] else pd.DataFrame()
            if ligne['ref'] == 'T5_141':
                comptes_n = comptes_n[comptes_n['account_number'] != '865'] if not comptes_n.empty else comptes_n
                comptes_n1 = comptes_n1[comptes_n1['account_number'] != '865'] if not comptes_n1.empty else comptes_n1
            solde_n = comptes_n['balance'].sum() if not comptes_n.empty else 0
            solde_n1 = comptes_n1['balance'].sum() if not comptes_n1.empty else 0
            solde_n = solde_n if solde_n is not None else 0
            # Si N-1 n'existe pas, mettre à zéro
            solde_n1 = solde_n1 if not df_n1.empty else 0
            if ligne['ref'] == 'FJ_VMP':
                variation = (solde_n or 0) - (solde_n1 or 0)
                debit_n = comptes_n['total_debit'].sum() if 'total_debit' in comptes_n else 0
                credit_n = comptes_n['total_credit'].sum() if 'total_credit' in comptes_n else 0
                montant = variation
                comptes = comptes_n.to_dict(orient='records')
            elif ligne['ref'] == 'FB':
                variation = 0
                comptes_486_n = filter_by_prefix(df_n, ['486'])
                comptes_486_n1 = filter_by_prefix(df_n1, ['486'])
                solde_486_n = comptes_486_n['balance'].sum() if not comptes_486_n.empty else 0
                solde_486_n1 = comptes_486_n1['balance'].sum() if not comptes_486_n1.empty else 0
                variation += -((solde_486_n or 0) - (solde_486_n1 or 0)) if not df_n1.empty else 0
                comptes_487_n = filter_by_prefix(df_n, ['487'])
                comptes_487_n1 = filter_by_prefix(df_n1, ['487'])
                solde_487_n = comptes_487_n['balance'].sum() if not comptes_487_n.empty else 0
                solde_487_n1 = comptes_487_n1['balance'].sum() if not comptes_487_n1.empty else 0
                variation += ((solde_487_n or 0) - (solde_487_n1 or 0)) if not df_n1.empty else 0
                comptes_461_469_n = filter_by_prefix(df_n, [str(i) for i in range(461, 470)])
                comptes_461_469_n1 = filter_by_prefix(df_n1, [str(i) for i in range(461, 470)])
                solde_461_469_n = comptes_461_469_n['balance'].sum() if not comptes_461_469_n.empty else 0
                solde_461_469_n1 = comptes_461_469_n1['balance'].sum() if not comptes_461_469_n1.empty else 0
                variation += ((solde_461_469_n or 0) - (solde_461_469_n1 or 0)) if not df_n1.empty else 0
            elif ligne['ref'] == 'FC':
                variation = -((solde_n or 0) - (solde_n1 or 0)) if not df_n1.empty else 0
            elif ligne['ref'] == 'FD':
                variation = (solde_n or 0) - (solde_n1 or 0) if not df_n1.empty else 0
            elif ligne['ref'] == 'FE':
                variation = (solde_n or 0) - (solde_n1 or 0) if not df_n1.empty else 0
            elif ligne['ref'] == 'FH':
                variation = 0
                for prefix in ['251', '256', '261', '262']:
                    comptes_n = filter_by_prefix(df_n, [prefix])
                    comptes_n1 = filter_by_prefix(df_n1, [prefix])
                    solde_n = comptes_n['balance'].sum() if not comptes_n.empty else 0
                    solde_n1 = comptes_n1['balance'].sum() if not comptes_n1.empty else 0
                    cessions_n = filter_by_prefix(df_n, ['775'])
                    cessions_n1 = filter_by_prefix(df_n1, ['775'])
                    cessions = cessions_n['balance'].sum() if not cessions_n.empty else 0
                    cessions += cessions_n1['balance'].sum() if not cessions_n1.empty else 0
                    variation += ((solde_n or 0) - (solde_n1 or 0)) + (cessions or 0) if not df_n1.empty else 0
                for prefix in [str(i) for i in range(264, 269)]:
                    comptes_n = filter_by_prefix(df_n, [prefix])
                    comptes_n1 = filter_by_prefix(df_n1, [prefix])
                    solde_n = comptes_n['balance'].sum() if not comptes_n.empty else 0
                    solde_n1 = comptes_n1['balance'].sum() if not comptes_n1.empty else 0
                    variation += (solde_n or 0) - (solde_n1 or 0) if not df_n1.empty else 0
                comptes_275_n = filter_by_prefix(df_n, ['275'])
                comptes_275_n1 = filter_by_prefix(df_n1, ['275'])
                solde_275_n = comptes_275_n['balance'].sum() if not comptes_275_n.empty else 0
                solde_275_n1 = comptes_275_n1['balance'].sum() if not comptes_275_n1.empty else 0
                variation += (solde_275_n or 0) - (solde_275_n1 or 0) if not df_n1.empty else 0
            else:
                variation = (solde_n or 0) - (solde_n1 or 0) if not df_n1.empty else 0
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
                montant = variation if not df_n1.empty else solde_n
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
    
    # Génération des feuilles maîtresses avec structure multi-onglets
    sheets_contents = {}
    sheets_data = {}
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils.dataframe import dataframe_to_rows
    
    for group_name, prefixes in groups.items():
        # Filtrer les données par groupe et exercice
        group_n = filter_by_prefix(df_n, prefixes)
        group_n1 = filter_by_prefix(df_n1, prefixes)
        
        # Créer un nouveau classeur Excel
        wb = openpyxl.Workbook()
        
        # Supprimer la feuille par défaut
        wb.remove(wb.active)
        
        # Déterminer si on a deux exercices
        has_two_exercices = not df_n1.empty and len(exercices) > 1
        
        if has_two_exercices:
            # Cas 1: Deux exercices - Créer 3 onglets
            
            # 1. Onglet Exercice N
            ws_n = wb.create_sheet(f"Exercice_{n}")
            ws_n.append(['Compte', 'Libellé', 'Solde', 'Débit', 'Crédit', 'Exercice', 'Date_Creation'])
            
            # Remplir les données N
            n_data = []
            for _, row in group_n.iterrows():
                n_data.append({
                    'Compte': row['account_number'],
                    'Libellé': row.get('account_name', ''),
                    'Solde': row['balance'],
                    'Débit': row.get('total_debit', 0),
                    'Crédit': row.get('total_credit', 0),
                    'Exercice': n,
                    'Date_Creation': row.get('created_at', '')
                })
            
            # Trier par numéro de compte
            n_data.sort(key=lambda x: str(x['Compte']))
            
            for row_data in n_data:
                ws_n.append([row_data['Compte'], row_data['Libellé'], row_data['Solde'], 
                           row_data['Débit'], row_data['Crédit'], row_data['Exercice'], row_data['Date_Creation']])
            
            # 2. Onglet Exercice N-1
            ws_n1 = wb.create_sheet(f"Exercice_{n_1}")
            ws_n1.append(['Compte', 'Libellé', 'Solde', 'Débit', 'Crédit', 'Exercice', 'Date_Creation'])
            
            # Remplir les données N-1
            n1_data = []
            for _, row in group_n1.iterrows():
                n1_data.append({
                    'Compte': row['account_number'],
                    'Libellé': row.get('account_name', ''),
                    'Solde': row['balance'],
                    'Débit': row.get('total_debit', 0),
                    'Crédit': row.get('total_credit', 0),
                    'Exercice': n_1,
                    'Date_Creation': row.get('created_at', '')
                })
            
            # Trier par numéro de compte
            n1_data.sort(key=lambda x: str(x['Compte']))
            
            for row_data in n1_data:
                ws_n1.append([row_data['Compte'], row_data['Libellé'], row_data['Solde'], 
                            row_data['Débit'], row_data['Crédit'], row_data['Exercice'], row_data['Date_Creation']])
            
            # 3. Onglet Comparatif
            ws_comp = wb.create_sheet(f"Comparatif_{n}_{n_1}")
            ws_comp.append(['Compte', 'Libellé', 'Solde_N', 'Solde_N-1', 'Variation', 
                          '%_Evolution', 'Débit_N', 'Crédit_N', 'Débit_N-1', 'Crédit_N-1', 'Date_Creation_N', 'Date_Creation_N-1', 'Exercices'])
            
            # Créer un dictionnaire pour faciliter la comparaison
            n_dict = {row['Compte']: row for row in n_data}
            n1_dict = {row['Compte']: row for row in n1_data}
            
            # Obtenir tous les comptes uniques
            all_accounts = set(n_dict.keys()) | set(n1_dict.keys())
            
            # Remplir le tableau comparatif
            comp_data = []
            for account in sorted(all_accounts):
                n_row = n_dict.get(account, {})
                n1_row = n1_dict.get(account, {})
                
                # Remplacer les "trous" par 0
                solde_n = n_row.get('Solde', 0) if n_row else 0
                solde_n1 = n1_row.get('Solde', 0) if n1_row else 0
                debit_n = n_row.get('Débit', 0) if n_row else 0
                credit_n = n_row.get('Crédit', 0) if n_row else 0
                debit_n1 = n1_row.get('Débit', 0) if n1_row else 0
                credit_n1 = n1_row.get('Crédit', 0) if n1_row else 0
                
                # Calculer la variation
                variation = solde_n - solde_n1
                
                # Calculer le pourcentage d'évolution
                if solde_n1 != 0:
                    pct_evolution = (variation / abs(solde_n1)) * 100
                else:
                    pct_evolution = 100 if solde_n != 0 else 0
                
                # Utiliser le libellé de N ou N-1 (priorité à N)
                libelle = n_row.get('Libellé', n1_row.get('Libellé', ''))
                
                comp_data.append({
                    'Compte': account,
                    'Libellé': libelle,
                    'Solde_N': solde_n,
                    'Solde_N-1': solde_n1,
                    'Variation': variation,
                    '%_Evolution': pct_evolution,
                    'Débit_N': debit_n,
                    'Crédit_N': credit_n,
                    'Débit_N-1': debit_n1,
                    'Crédit_N-1': credit_n1,
                    'Date_Creation_N': n_row.get('Date_Creation', ''),
                    'Date_Creation_N-1': n1_row.get('Date_Creation', ''),
                    'Exercices': f"{n}/{n_1}"
                })
            
            # Trier par numéro de compte
            comp_data.sort(key=lambda x: str(x['Compte']))
            
            for row_data in comp_data:
                ws_comp.append([row_data['Compte'], row_data['Libellé'], row_data['Solde_N'], 
                              row_data['Solde_N-1'], row_data['Variation'], row_data['%_Evolution'],
                              row_data['Débit_N'], row_data['Crédit_N'], row_data['Débit_N-1'], 
                              row_data['Crédit_N-1'], row_data['Date_Creation_N'], row_data['Date_Creation_N-1'], row_data['Exercices']])
            
            # Appliquer le formatage aux onglets
            for ws in [ws_n, ws_n1, ws_comp]:
                # En-têtes en gras
                for cell in ws[1]:
                    cell.font = Font(bold=True)
                    cell.fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
                    cell.alignment = Alignment(horizontal="center")
                
                # Ajuster la largeur des colonnes
                for column in ws.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    ws.column_dimensions[column_letter].width = adjusted_width
            
            # Stocker les données pour l'API
            sheets_data[group_name] = {
                'exercice_n': n_data,
                'exercice_n1': n1_data,
                'comparatif': comp_data,
                'has_two_exercices': True,
                'exercices': [n, n_1]
            }
            
        else:
            # Cas 2: Un seul exercice - Créer 1 onglet
            ws_n = wb.create_sheet(f"Exercice_{n}")
            ws_n.append(['Compte', 'Libellé', 'Solde', 'Débit', 'Crédit', 'Exercice', 'Date_Creation'])
            
            # Remplir les données N
            n_data = []
            for _, row in group_n.iterrows():
                n_data.append({
                    'Compte': row['account_number'],
                    'Libellé': row.get('account_name', ''),
                    'Solde': row['balance'],
                    'Débit': row.get('total_debit', 0),
                    'Crédit': row.get('total_credit', 0),
                    'Exercice': n,
                    'Date_Creation': row.get('created_at', '')
                })
            
            # Trier par numéro de compte
            n_data.sort(key=lambda x: str(x['Compte']))
            
            for row_data in n_data:
                ws_n.append([row_data['Compte'], row_data['Libellé'], row_data['Solde'], 
                           row_data['Débit'], row_data['Crédit'], row_data['Exercice'], row_data['Date_Creation']])
            
            # Appliquer le formatage
            for cell in ws_n[1]:
                cell.font = Font(bold=True)
                cell.fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
                cell.alignment = Alignment(horizontal="center")
            
            # Ajuster la largeur des colonnes
            for column in ws_n.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                ws_n.column_dimensions[column_letter].width = adjusted_width
            
            # Stocker les données pour l'API
            sheets_data[group_name] = {
                'exercice_n': n_data,
                'has_two_exercices': False,
                'exercices': [n]
            }
        
        # Sauvegarder le fichier Excel
        output = BytesIO()
        wb.save(output)
        sheets_contents[group_name] = output.getvalue()
    
    # Ajout du contrôle de cohérence au retour
    coherence = controle_coherence(tft_data)
    return tft_content, sheets_contents, tft_data, sheets_data, coherence

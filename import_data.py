from sqlalchemy import create_engine, text
import pandas as pd
import logging
import os
from pathlib import Path

# Nastavenie logovania
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Konfigurácia pripojenia k databáze ---
DB_USER = 'tassu_user'
DB_PASSWORD = 'tassu_password'
DB_HOST = os.getenv('DB_HOST', 'localhost')  # Použije 'postgres' v Dockeri, 'localhost' lokálne
DB_PORT = '5432'  # Interný port v Dockeri je 5432
DB_NAME = 'tassu_db'

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# --- Zoznam CSV súborov na import ---
CSV_DIR = 'data_csv'  # Priečinok s CSV súbormi
CSV_FILES = {
    'health': os.path.join(CSV_DIR, 'health_indicators_che.csv'),
    'air_pollution': os.path.join(CSV_DIR, 'air_pollution_indicators_che.csv'),
    'environment': os.path.join(CSV_DIR, 'environment_and_health_indicators_che.csv'),
    'alcohol': os.path.join(CSV_DIR, 'global_information_system_on_alcohol_and_health_indicators_che.csv'),
    'financing': os.path.join(CSV_DIR, 'health_financing_indicators_che.csv'),
    'nutrition': os.path.join(CSV_DIR, 'nutrition_indicators_che.csv')
}




def clean_column_names(df):
    """Čistí názvy stĺpcov pre jednoduchšiu prácu."""
    # Odstránenie # a všetkého za prvým '+'
    df.columns = df.columns.str.split('+').str[0].str.replace('#', '')
    # Nahradenie špeciálnych znakov
    df.columns = df.columns.str.lower().str.replace(r'[\s\(\)]', '_', regex=True)
    df.columns = df.columns.str.replace(r'__+', '_', regex=True).str.strip('_')
    return df


def parse_demographic_info(row):
    """Extrahuje demografické informácie z riadku."""
    pohlavie = 'vsetky'
    vekova_skupina = 'vsetky'
    
    dimension_type = row.get('dimension_type', '')
    dimension_code = row.get('dimension_code', '')
    dimension_name = row.get('dimension_name', '')
    
    if pd.notna(dimension_type):
        if dimension_type == 'SEX':
            if 'MLE' in str(dimension_code):
                pohlavie = 'muz'
            elif 'FMLE' in str(dimension_code):
                pohlavie = 'zena'
            elif 'BTSX' in str(dimension_code):
                pohlavie = 'vsetky'
        
        elif dimension_type == 'AGEGROUP':
            age_str = str(dimension_name).lower()
            if any(x in age_str for x in ['0-27', 'neonatal', '0-4', '5-9', '10-14']):
                vekova_skupina = '0-17'
            elif any(x in age_str for x in ['15-19', '18-34', 'adolescent', '20-24', '25-29', '30-34']):
                vekova_skupina = '18-34'
            elif any(x in age_str for x in ['35-39', '40-44', '45-49']):
                vekova_skupina = '35-49'
            elif any(x in age_str for x in ['50-54', '55-59', '60-64']):
                vekova_skupina = '50-64'
            elif '65' in age_str or '70' in age_str or '75' in age_str:
                vekova_skupina = '65+'
    
    return {
        'vekova_skupina': vekova_skupina,
        'pohlavie': pohlavie,
        'dimension_type': dimension_type if pd.notna(dimension_type) else None,
        'dimension_code': dimension_code if pd.notna(dimension_code) else None,
        'dimension_name': dimension_name if pd.notna(dimension_name) else None
    }


def categorize_indicator(indicator_name, indicator_code, csv_type):
    """Kategorizuje indikátor podľa názvu, kódu a typu CSV súboru."""
    indicator_lower = str(indicator_name).lower()
    
    # Podľa typu CSV
    if csv_type == 'air_pollution':
        return ('Znečistenie ovzdušia', 'AIR_POLL', 'environmentalny', 4)
    elif csv_type == 'environment':
        return ('Environmentálne zdravie', 'ENV_HEALTH', 'environmentalny', 3)
    elif csv_type == 'alcohol':
        return ('Alkohol a zdravie', 'ALCOHOL', 'rizikovy_faktor', 4)
    elif csv_type == 'financing':
        return ('Zdravotné financovanie', 'FIN_HEALTH', 'financovanie', 2)
    elif csv_type == 'nutrition':
        return ('Výživa a obezita', 'NUTRITION', 'vyzivovacie', 3)
    
    # Pre health indicators - detailnejšia kategorizácia
    if any(word in indicator_lower for word in ['mortality', 'death', 'úmrtí']):
        return ('Úmrtnosť', 'MORT', 'choroba', 5)
    elif any(word in indicator_lower for word in ['obesity', 'overweight', 'bmi', 'underweight', 'thinness']):
        return ('Obezita a telesná hmotnosť', 'OBES', 'vyzivovacie', 3)
    elif any(word in indicator_lower for word in ['tobacco', 'smoking', 'cigarette']):
        return ('Fajčenie a tabak', 'TOBAC', 'rizikovy_faktor', 4)
    elif any(word in indicator_lower for word in ['alcohol', 'drinking']):
        return ('Alkohol', 'ALC', 'rizikovy_faktor', 4)
    elif any(word in indicator_lower for word in ['immunization', 'vaccination', 'vaccine', 'measles', 'diphtheria']):
        return ('Infekčné choroby - vakcinácia', 'VAX', 'choroba', 4)
    elif any(word in indicator_lower for word in ['hepatitis', 'hiv', 'malaria', 'tuberculosis']):
        return ('Infekčné choroby', 'INF', 'choroba', 5)
    elif any(word in indicator_lower for word in ['air pollution', 'environmental']):
        return ('Environmentálne faktory', 'ENV', 'environmentalny', 3)
    elif any(word in indicator_lower for word in ['anaemia', 'anemia', 'nutrition', 'malnutrition']):
        return ('Výživa a anémia', 'NUTR', 'vyzivovacie', 3)
    elif any(word in indicator_lower for word in ['birth', 'neonatal', 'infant']):
        return ('Zdravie matiek a detí', 'MAT_CHILD', 'choroba', 5)
    else:
        return ('Ostatné zdravotné indikátory', 'OTHER', 'choroba', 2)


def load_csv_data(csv_path, csv_type):
    """Načíta dáta z CSV súboru."""
    try:
        if not os.path.exists(csv_path):
            logging.warning(f"Súbor nebol nájdený: {csv_path}")
            return None
        
        logging.info(f"Načítavam {csv_type}: '{csv_path}'...")
        # Preskočíme druhý riadok s metadátami (riadok s # symbolami)
        df = pd.read_csv(csv_path, skiprows=[1])
        df = clean_column_names(df)
        
        # Konverzia dátových typov
        if 'year_display' in df.columns:
            df['year_display'] = pd.to_numeric(df['year_display'], errors='coerce').astype('Int64')
        if 'numeric' in df.columns:
            df['numeric'] = pd.to_numeric(df['numeric'], errors='coerce')
        if 'low' in df.columns:
            df['low'] = pd.to_numeric(df['low'], errors='coerce')
        if 'high' in df.columns:
            df['high'] = pd.to_numeric(df['high'], errors='coerce')
        
        logging.info(f"  ✓ Načítaných {len(df)} riadkov z {csv_type}")
        return df
    
    except Exception as e:
        logging.error(f"Chyba pri načítaní {csv_path}: {e}")
        return None




def import_to_db(all_data, db_url):
    """Importuje všetky dáta do databázy."""
    try:
        logging.info(f"\n{'='*60}")
        logging.info(f"Pripájam sa k databáze '{DB_NAME}'...")
        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            logging.info("✓ Pripojenie úspešné\n")
            
            # 1. Vyčistenie existujúcich dát
            logging.info("Čistím existujúce dáta...")
            conn.execute(text("TRUNCATE TABLE alkoholove_indikatory RESTART IDENTITY CASCADE;"))
            conn.execute(text("TRUNCATE TABLE vyzivovacie_indikatory RESTART IDENTITY CASCADE;"))
            conn.execute(text("TRUNCATE TABLE zdravotne_financovanie RESTART IDENTITY CASCADE;"))
            conn.execute(text("TRUNCATE TABLE environmentalne_faktory RESTART IDENTITY CASCADE;"))
            conn.execute(text("TRUNCATE TABLE merania_indikatorov RESTART IDENTITY CASCADE;"))
            conn.execute(text("TRUNCATE TABLE zdravotne_indikatory RESTART IDENTITY CASCADE;"))
            conn.execute(text("TRUNCATE TABLE kategorie_indikatorov RESTART IDENTITY CASCADE;"))
            conn.execute(text("TRUNCATE TABLE demograficke_skupiny RESTART IDENTITY CASCADE;"))
            conn.commit()
            logging.info("✓ Dáta vyčistené\n")
            
            # 2. Import kategórií indikátorov
            logging.info("Importujem kategórie indikátorov...")
            kategorie = {}
            
            for csv_type, df in all_data.items():
                if df is None or df.empty:
                    continue
                
                for _, row in df.iterrows():
                    kat_nazov, kat_kod, kat_typ, uroven = categorize_indicator(
                        row.get('gho_display', ''),
                        row.get('gho_code', ''),
                        csv_type
                    )
                    
                    if kat_kod not in kategorie:
                        result = conn.execute(text("""
                            INSERT INTO kategorie_indikatorov (nazov, kod, typ, popis)
                            VALUES (:nazov, :kod, :typ, :popis)
                            ON CONFLICT (kod) DO UPDATE SET nazov = EXCLUDED.nazov
                            RETURNING id
                        """), {
                            'nazov': kat_nazov,
                            'kod': kat_kod,
                            'typ': kat_typ,
                            'popis': f'Kategória pre {csv_type}'
                        })
                        kategorie[kat_kod] = result.fetchone()[0]
            
            conn.commit()
            logging.info(f"  ✓ Importovaných {len(kategorie)} kategórií\n")
            
            # 3. Import zdravotných indikátorov
            logging.info("Importujem zdravotné indikátory...")
            indikatory = {}
            
            for csv_type, df in all_data.items():
                if df is None or df.empty:
                    continue
                
                for _, row in df.iterrows():
                    gho_kod = row.get('gho_code', '')
                    if pd.isna(gho_kod) or gho_kod in indikatory:
                        continue
                    
                    kat_nazov, kat_kod, kat_typ, uroven = categorize_indicator(
                        row.get('gho_display', ''),
                        gho_kod,
                        csv_type
                    )
                    
                    result = conn.execute(text("""
                        INSERT INTO zdravotne_indikatory 
                        (gho_kod, nazov, url, kategoria_id, jednotka, uroven_zavaznosti)
                        VALUES (:gho_kod, :nazov, :url, :kat_id, :jednotka, :uroven)
                        ON CONFLICT (gho_kod) DO UPDATE SET nazov = EXCLUDED.nazov
                        RETURNING id
                    """), {
                        'gho_kod': gho_kod,
                        'nazov': row.get('gho_display', '')[:500],
                        'url': row.get('gho_url', ''),
                        'kat_id': kategorie[kat_kod],
                        'jednotka': None,
                        'uroven': uroven
                    })
                    indikatory[gho_kod] = result.fetchone()[0]
            
            conn.commit()
            logging.info(f"  ✓ Importovaných {len(indikatory)} indikátorov\n")
            
            # 4. Import demografických skupín
            logging.info("Importujem demografické skupiny...")
            demografie = {}
            
            for csv_type, df in all_data.items():
                if df is None or df.empty:
                    continue
                
                for _, row in df.iterrows():
                    demo_info = parse_demographic_info(row)
                    demo_key = (
                        demo_info['vekova_skupina'],
                        demo_info['pohlavie'],
                        demo_info['dimension_type'],
                        demo_info['dimension_code']
                    )
                    
                    if demo_key not in demografie:
                        result = conn.execute(text("""
                            INSERT INTO demograficke_skupiny 
                            (vekova_skupina, pohlavie, dimension_type, dimension_code, dimension_name)
                            VALUES (:vek, :pohl, :dtype, :dcode, :dname)
                            ON CONFLICT (vekova_skupina, pohlavie, dimension_type, dimension_code) 
                            DO UPDATE SET dimension_name = EXCLUDED.dimension_name
                            RETURNING id
                        """), {
                            'vek': demo_info['vekova_skupina'],
                            'pohl': demo_info['pohlavie'],
                            'dtype': demo_info['dimension_type'],
                            'dcode': demo_info['dimension_code'],
                            'dname': demo_info['dimension_name']
                        })
                        demografie[demo_key] = result.fetchone()[0]
            
            conn.commit()
            logging.info(f"  ✓ Importovaných {len(demografie)} demografických skupín\n")
            
            # 5. Import meraní do príslušných tabuliek
            logging.info("Importujem merania do špecializovaných tabuliek...\n")
            
            counts = {
                'merania': 0,
                'environmentalne': 0,
                'financovanie': 0,
                'vyzivovacie': 0,
                'alkoholove': 0
            }
            
            for csv_type, df in all_data.items():
                if df is None or df.empty:
                    continue
                
                logging.info(f"  Spracovávam {csv_type}...")
                type_count = 0
                
                for _, row in df.iterrows():
                    gho_kod = row.get('gho_code', '')
                    if pd.isna(gho_kod) or gho_kod not in indikatory:
                        continue
                    
                    indikator_id = indikatory[gho_kod]
                    rok = row.get('year_display')
                    if pd.isna(rok):
                        continue
                    
                    # Demografická skupina
                    demo_info = parse_demographic_info(row)
                    demo_key = (
                        demo_info['vekova_skupina'],
                        demo_info['pohlavie'],
                        demo_info['dimension_type'],
                        demo_info['dimension_code']
                    )
                    demo_id = demografie.get(demo_key)
                    
                    # Hodnoty
                    hodnota_cislo = row.get('numeric')
                    hodnota_text = row.get('value')
                    dolna = row.get('low')
                    horna = row.get('high')
                    
                    try:
                        # Rozhodnutie do ktorej tabuľky importovať
                        if csv_type == 'air_pollution' or csv_type == 'environment':
                            # Environmentálne faktory
                            conn.execute(text("""
                                INSERT INTO environmentalne_faktory 
                                (indikator_id, rok, demograficka_skupina_id, hodnota_cislo, hodnota_text, 
                                 dolna_hranica, horna_hranica, typ_znecistenia, zdroj_dat)
                                VALUES (:ind_id, :rok, :demo_id, :h_cislo, :h_text, :dolna, :horna, :typ, :zdroj)
                                ON CONFLICT (indikator_id, rok, demograficka_skupina_id) DO NOTHING
                            """), {
                                'ind_id': indikator_id,
                                'rok': int(rok),
                                'demo_id': demo_id,
                                'h_cislo': float(hodnota_cislo) if pd.notna(hodnota_cislo) else None,
                                'h_text': str(hodnota_text)[:200] if pd.notna(hodnota_text) else None,
                                'dolna': float(dolna) if pd.notna(dolna) else None,
                                'horna': float(horna) if pd.notna(horna) else None,
                                'typ': csv_type,
                                'zdroj': row.get('gho_url', '')
                            })
                            counts['environmentalne'] += 1
                            type_count += 1
                            
                        elif csv_type == 'financing':
                            # Zdravotné financovanie
                            conn.execute(text("""
                                INSERT INTO zdravotne_financovanie 
                                (indikator_id, rok, hodnota_cislo, hodnota_text, typ_vydavku, zdroj_dat)
                                VALUES (:ind_id, :rok, :h_cislo, :h_text, :typ, :zdroj)
                                ON CONFLICT (indikator_id, rok) DO NOTHING
                            """), {
                                'ind_id': indikator_id,
                                'rok': int(rok),
                                'h_cislo': float(hodnota_cislo) if pd.notna(hodnota_cislo) else None,
                                'h_text': str(hodnota_text)[:200] if pd.notna(hodnota_text) else None,
                                'typ': gho_kod.split('_')[1] if '_' in gho_kod else 'OTHER',
                                'zdroj': row.get('gho_url', '')
                            })
                            counts['financovanie'] += 1
                            type_count += 1
                            
                        elif csv_type == 'nutrition':
                            # Výživové indikátory
                            severity = None
                            if 'severity' in row and pd.notna(row.get('severity')):
                                severity = row.get('severity')
                            
                            conn.execute(text("""
                                INSERT INTO vyzivovacie_indikatory 
                                (indikator_id, rok, demograficka_skupina_id, hodnota_cislo, hodnota_text,
                                 dolna_hranica, horna_hranica, typ_merania, severity, zdroj_dat)
                                VALUES (:ind_id, :rok, :demo_id, :h_cislo, :h_text, :dolna, :horna, :typ, :sev, :zdroj)
                                ON CONFLICT (indikator_id, rok, demograficka_skupina_id) DO NOTHING
                            """), {
                                'ind_id': indikator_id,
                                'rok': int(rok),
                                'demo_id': demo_id,
                                'h_cislo': float(hodnota_cislo) if pd.notna(hodnota_cislo) else None,
                                'h_text': str(hodnota_text)[:200] if pd.notna(hodnota_text) else None,
                                'dolna': float(dolna) if pd.notna(dolna) else None,
                                'horna': float(horna) if pd.notna(horna) else None,
                                'typ': 'BMI' if 'bmi' in gho_kod.lower() else 'OTHER',
                                'sev': severity,
                                'zdroj': row.get('gho_url', '')
                            })
                            counts['vyzivovacie'] += 1
                            type_count += 1
                            
                        elif csv_type == 'alcohol':
                            # Alkoholové indikátory
                            typ_alkoholu = None
                            if 'dimension_type' in row and row.get('dimension_type') == 'ALCOHOLTYPE':
                                typ_alkoholu = row.get('dimension_name')
                            
                            conn.execute(text("""
                                INSERT INTO alkoholove_indikatory 
                                (indikator_id, rok, demograficka_skupina_id, hodnota_cislo, hodnota_text,
                                 dolna_hranica, horna_hranica, typ_alkoholu, typ_merania, zdroj_dat)
                                VALUES (:ind_id, :rok, :demo_id, :h_cislo, :h_text, :dolna, :horna, :typ_alk, :typ_mer, :zdroj)
                                ON CONFLICT (indikator_id, rok, demograficka_skupina_id) DO NOTHING
                            """), {
                                'ind_id': indikator_id,
                                'rok': int(rok),
                                'demo_id': demo_id,
                                'h_cislo': float(hodnota_cislo) if pd.notna(hodnota_cislo) else None,
                                'h_text': str(hodnota_text)[:200] if pd.notna(hodnota_text) else None,
                                'dolna': float(dolna) if pd.notna(dolna) else None,
                                'horna': float(horna) if pd.notna(horna) else None,
                                'typ_alk': str(typ_alkoholu)[:100] if pd.notna(typ_alkoholu) else None,
                                'typ_mer': row.get('gho_display', '')[:200],
                                'zdroj': row.get('gho_url', '')
                            })
                            counts['alkoholove'] += 1
                            type_count += 1
                            
                        else:
                            # Všeobecné merania (health indicators)
                            conn.execute(text("""
                                INSERT INTO merania_indikatorov 
                                (indikator_id, demograficka_skupina_id, rok, hodnota_cislo, hodnota_text,
                                 dolna_hranica, horna_hranica, region_kod, region_nazov, 
                                 krajina_kod, krajina_nazov, zdroj_url)
                                VALUES (:ind_id, :demo_id, :rok, :h_cislo, :h_text, :dolna, :horna,
                                        :reg_kod, :reg_nazov, :kraj_kod, :kraj_nazov, :url)
                                ON CONFLICT (indikator_id, demograficka_skupina_id, rok) DO NOTHING
                            """), {
                                'ind_id': indikator_id,
                                'demo_id': demo_id,
                                'rok': int(rok),
                                'h_cislo': float(hodnota_cislo) if pd.notna(hodnota_cislo) else None,
                                'h_text': str(hodnota_text)[:200] if pd.notna(hodnota_text) else None,
                                'dolna': float(dolna) if pd.notna(dolna) else None,
                                'horna': float(horna) if pd.notna(horna) else None,
                                'reg_kod': row.get('region_code'),
                                'reg_nazov': row.get('region_display'),
                                'kraj_kod': row.get('country_code'),
                                'kraj_nazov': row.get('country_display'),
                                'url': row.get('gho_url', '')
                            })
                            counts['merania'] += 1
                            type_count += 1
                    
                    except Exception as e:
                        # Logujeme chybu, ale pokračujeme
                        logging.debug(f"Chyba pri importe riadku: {e}")
                        continue
                
                logging.info(f"    ✓ {type_count} záznamov")
            
            conn.commit()
            
            # Výpis štatistík
            logging.info(f"\n{'='*60}")
            logging.info("IMPORT DOKONČENÝ - ŠTATISTIKY:")
            logging.info(f"{'='*60}")
            
            stats = conn.execute(text("""
                SELECT 
                    (SELECT COUNT(*) FROM kategorie_indikatorov) as kategorie,
                    (SELECT COUNT(*) FROM zdravotne_indikatory) as indikatory,
                    (SELECT COUNT(*) FROM demograficke_skupiny) as demografie,
                    (SELECT COUNT(*) FROM merania_indikatorov) as merania,
                    (SELECT COUNT(*) FROM environmentalne_faktory) as environmentalne,
                    (SELECT COUNT(*) FROM zdravotne_financovanie) as financovanie,
                    (SELECT COUNT(*) FROM vyzivovacie_indikatory) as vyzivovacie,
                    (SELECT COUNT(*) FROM alkoholove_indikatory) as alkoholove
            """)).fetchone()
            
            logging.info(f"  • Kategórie indikátorov: {stats[0]}")
            logging.info(f"  • Zdravotné indikátory: {stats[1]}")
            logging.info(f"  • Demografické skupiny: {stats[2]}")
            logging.info(f"  • Všeobecné merania: {stats[3]}")
            logging.info(f"  • Environmentálne faktory: {stats[4]}")
            logging.info(f"  • Zdravotné financovanie: {stats[5]}")
            logging.info(f"  • Výživové indikátory: {stats[6]}")
            logging.info(f"  • Alkoholové indikátory: {stats[7]}")
            logging.info(f"{'='*60}\n")
            
            # Top 5 kategórií podľa počtu meraní
            logging.info("TOP 5 KATEGÓRIÍ PODĽA POČTU MERANÍ:")
            top_kategorie = conn.execute(text("""
                SELECT k.nazov, k.typ, COUNT(m.id) as pocet
                FROM kategorie_indikatorov k
                JOIN zdravotne_indikatory i ON i.kategoria_id = k.id
                LEFT JOIN merania_indikatorov m ON m.indikator_id = i.id
                GROUP BY k.id, k.nazov, k.typ
                ORDER BY pocet DESC
                LIMIT 5
            """)).fetchall()
            
            for i, (nazov, typ, pocet) in enumerate(top_kategorie, 1):
                logging.info(f"  {i}. {nazov} ({typ}): {pocet} meraní")
            
            logging.info(f"{'='*60}\n")
    
    except Exception as e:
        logging.error(f"Chyba pri importe do databázy: {e}")
        raise


if __name__ == "__main__":
    logging.info("\n" + "="*60)
    logging.info("IMPORT WHO ZDRAVOTNÝCH DÁT PRE ŠVAJČIARSKO")
    logging.info("="*60 + "\n")
    
    # Načítanie všetkých CSV súborov
    all_data = {}
    for csv_type, csv_file in CSV_FILES.items():
        df = load_csv_data(csv_file, csv_type)
        all_data[csv_type] = df
    
    # Import do databázy
    import_to_db(all_data, DATABASE_URL)
    
    logging.info("✓ IMPORT ÚSPEŠNE DOKONČENÝ!\n")

#!/usr/bin/env python3
"""
GBD 2023 Švajčiarsko - Dynamický Import
Automatické vytvorenie tabuľky pre každý typ choroby/rizika
3 Domény: CHOROBY, PROSTREDIE, ŽIVOTNÝ ŠTÝL
"""

from sqlalchemy import create_engine, text
import pandas as pd
import logging
import os
import glob
import time
import re

logging.basicConfig(level=logging.INFO, format='%(message)s')

# Database config
DB_USER = 'tassu_user'
DB_PASSWORD = 'tassu_password'
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = '5432'
DB_NAME = 'tassu_db'
DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

CSV_DIR = 'data_csv'
GBD_FILES = glob.glob(os.path.join(CSV_DIR, 'IHME-GBD_2023_DATA-*.csv'))

# ============================================================
# SKUPINY
# ============================================================

DISEASE_GROUPS = {
    'CANCER': 'Rakovina',
    'CARDIO': 'Kardiovaskulárne',
    'NEURO': 'Neurologické',
    'RESPIRATORY': 'Respiračné',
    'METABOLIC': 'Metabolické',
    'INFECTIOUS': 'Infekčné',
    'DIGESTIVE': 'Tráviacie',
    'MENTAL': 'Mentálne',
    'OTHER': 'Ostatné',
}

ENV_GROUPS = {
    'AIR_POLLUTION': 'Znečistenie ovzdušia',
    'TEMPERATURE': 'Teplota',
    'WATER_SANITATION': 'Voda a sanitácia',
    'LEAD': 'Olovo',
}

LIFESTYLE_GROUPS = {
    'TOBACCO': 'Tabak',
    'ALCOHOL_DRUGS': 'Alkohol a drogy',
    'DIET': 'Strava',
    'PHYSICAL_ACTIVITY': 'Fyzická aktivita',
    'METABOLIC': 'Metabolické faktory',
}

# Agregáty na filtrovanie
AGGREGATES = [
    'all causes', 'total cancer', 'cardiovascular diseases', 
    'chronic respiratory diseases', 'digestive diseases', 
    'neurological disorders', 'mental disorders',
    'non-communicable diseases', 'injuries', 'neoplasms',
    'alcohol use disorders', 'substance use disorders',
    'maternal and neonatal disorders', 'respiratory infections',
    'enteric infections', 'neglected tropical diseases',
    'hiv/aids and sexually transmitted infections',
]

# Cirkulárne závislosti
CIRCULAR_DEPENDENCIES = {'alcohol use disorders', 'drug use disorders', 'eating disorders'}

# ============================================================
# POMOCNÉ FUNKCIE
# ============================================================

def normalize_table_name(cause_name):
    """Vytvorí názov tabuľky z názvu choroby"""
    name = cause_name.lower()
    name = re.sub(r"['\",\(\)/]", '', name)
    name = re.sub(r'[\s\-]+', '_', name)
    name = re.sub(r'_+', '_', name).strip('_')
    if len(name) > 55:
        name = name[:55]
    return f'dm_{name}'

def categorize_disease(cause_name):
    """Kategorizácia choroby"""
    c = str(cause_name).lower()
    if any(k in c for k in ['cancer', 'carcinoma', 'neoplasm', 'leukemia', 'lymphoma', 'melanoma']):
        return 'CANCER'
    if any(k in c for k in ['heart', 'stroke', 'ischemic', 'cardiovascular', 'myocardial', 'hypertensive']):
        return 'CARDIO'
    if any(k in c for k in ['alzheimer', 'dementia', 'parkinson', 'epilepsy', 'sclerosis', 'motor neuron']):
        return 'NEURO'
    if any(k in c for k in ['respiratory', 'copd', 'asthma', 'pneumonia', 'bronch', 'lung']):
        return 'RESPIRATORY'
    if any(k in c for k in ['diabetes', 'kidney', 'renal']):
        return 'METABOLIC'
    if any(k in c for k in ['infection', 'hepatitis', 'tuberculosis', 'hiv', 'aids', 'malaria']):
        return 'INFECTIOUS'
    if any(k in c for k in ['digestive', 'liver', 'cirrhosis', 'peptic', 'bowel', 'appendicitis']):
        return 'DIGESTIVE'
    if any(k in c for k in ['mental', 'depression', 'anxiety', 'schizophrenia', 'bipolar']):
        return 'MENTAL'
    return 'OTHER'

def categorize_env(risk_name):
    """Kategorizácia env rizika"""
    r = str(risk_name).lower()
    if 'pollution' in r or 'ozone' in r or 'particulate' in r:
        return 'AIR_POLLUTION'
    if 'temperature' in r:
        return 'TEMPERATURE'
    if 'water' in r or 'sanitation' in r or 'handwashing' in r:
        return 'WATER_SANITATION'
    if 'lead' in r:
        return 'LEAD'
    return None

def categorize_lifestyle(risk_name):
    """Kategorizácia lifestyle rizika"""
    r = str(risk_name).lower()
    if 'smok' in r or 'tobacco' in r:
        return 'TOBACCO'
    if 'alcohol' in r or 'drug' in r:
        return 'ALCOHOL_DRUGS'
    if 'diet' in r:
        return 'DIET'
    if 'physical' in r:
        return 'PHYSICAL_ACTIVITY'
    if 'pressure' in r or 'cholesterol' in r or 'body-mass' in r or 'glucose' in r:
        return 'METABOLIC'
    return None

def normalize_env_table_name(risk_name):
    """Vytvorí názov tabuľky pre env riziko"""
    name = risk_name.lower()
    name = re.sub(r"['\",\(\)/]", '', name)
    name = re.sub(r'[\s\-]+', '_', name)
    name = re.sub(r'_+', '_', name).strip('_')
    if len(name) > 55:
        name = name[:55]
    return f'em_{name}'

def normalize_lifestyle_table_name(risk_name):
    """Vytvorí názov tabuľky pre lifestyle riziko"""
    name = risk_name.lower()
    name = re.sub(r"['\",\(\)/]", '', name)
    name = re.sub(r'[\s\-]+', '_', name)
    name = re.sub(r'_+', '_', name).strip('_')
    if len(name) > 55:
        name = name[:55]
    return f'lm_{name}'

def is_aggregate(name):
    """Kontrola či je názov agregát"""
    name_lower = str(name).lower()
    return any(agg in name_lower for agg in AGGREGATES)

def connect_db(max_retries=10, delay=5):
    """Pripojenie k databáze"""
    for attempt in range(1, max_retries + 1):
        try:
            engine = create_engine(DATABASE_URL)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logging.info("✓ Pripojené k databáze")
            return engine
        except Exception as e:
            if attempt < max_retries:
                logging.warning(f"Pokus {attempt}/{max_retries} zlyhal...")
                time.sleep(delay)
            else:
                raise Exception(f"Nepodarilo sa pripojiť: {e}")
    return None

# ============================================================
# HLAVNÁ IMPORTNÁ FUNKCIA
# ============================================================

def import_data():
    """Hlavná importná funkcia"""
    try:
        print("="*70)
        print("GBD 2023 ŠVAJČIARSKO - DYNAMICKÝ IMPORT")
        print("="*70)
        
        if not GBD_FILES:
            raise Exception(f"Žiadne CSV súbory v {CSV_DIR}")
        
        logging.info(f"\nNájdené {len(GBD_FILES)} súbory")
        logging.info("\nPripájanie...")
        engine = connect_db()
        
        with engine.connect() as conn:
            # Načítanie CSV
            logging.info("\nNačítavanie CSV súborov...")
            dfs = []
            for csv_file in GBD_FILES:
                df = pd.read_csv(csv_file)
                logging.info(f"  {os.path.basename(csv_file)}: {len(df)} riadkov")
                dfs.append(df)
            
            df_all = pd.concat(dfs, ignore_index=True)
            logging.info(f"\nCelkom: {len(df_all)} riadkov")
            
            # Filtrovanie agregátov
            df_filtered = df_all[~df_all['cause_name'].apply(is_aggregate)]
            logging.info(f"Vyfiltrovaných: {len(df_all) - len(df_filtered)} agregátov")
            logging.info(f"Zostáva: {len(df_filtered)} riadkov")
            
            # Konverzia na integer
            for col in ['val', 'upper', 'lower']:
                if col in df_filtered.columns:
                    df_filtered.loc[:, col] = df_filtered[col].fillna(0).round().astype(int)
            
            # ========================================
            # DOMÉNA 1: CHOROBY
            # ========================================
            
            print("\n" + "="*70)
            print("DOMÉNA 1: CHOROBY")
            print("="*70)
            
            # 1. Vytvorenie skupín chorôb
            logging.info("\n1. Vytváranie skupín chorôb...")
            for group_code, group_name in DISEASE_GROUPS.items():
                conn.execute(text("""
                    INSERT INTO disease_groups (group_code, group_name)
                    VALUES (:code, :name)
                    ON CONFLICT (group_code) DO UPDATE SET group_name = EXCLUDED.group_name
                """), {'code': group_code, 'name': group_name})
                conn.commit()
            logging.info(f"   ✓ {len(DISEASE_GROUPS)} skupín")
            
            # 2. Spracovanie každej choroby
            logging.info("\n2. Spracovanie chorôb (vytvorenie indikátorov a tabuliek)...")
            df_health = df_filtered[df_filtered['rei_id'].isna()].copy()
            causes = df_health[['cause_id', 'cause_name']].dropna().drop_duplicates()
            
            indicator_map = {}
            table_data = {}  # {table_name: [records]}
            created_tables = set()
            
            for _, row in causes.iterrows():
                cause_id = int(row['cause_id'])
                cause_name = row['cause_name']
                
                # Určenie skupiny
                group_code = categorize_disease(cause_name)
                
                # Získanie group_id
                result = conn.execute(text(
                    "SELECT group_id FROM disease_groups WHERE group_code = :code"
                ), {'code': group_code})
                group_id = result.fetchone()[0]
                
                # Vytvorenie názvu tabuľky
                table_name = normalize_table_name(cause_name)
                
                # Vytvorenie tabuľky (ak ešte neexistuje)
                if table_name not in created_tables:
                    try:
                        conn.execute(text("SELECT create_disease_table(:table_name)"), 
                                   {'table_name': table_name})
                        conn.commit()
                        created_tables.add(table_name)
                        logging.info(f"   ✓ Vytvorená tabuľka: {table_name}")
                    except Exception as e:
                        logging.warning(f"   ⚠ Tabuľka {table_name} už existuje alebo chyba: {e}")
                
                # Vytvorenie indikátora
                conn.execute(text("""
                    INSERT INTO disease_indicators (cause_id, cause_name, group_id, table_name)
                    VALUES (:cause_id, :cause_name, :group_id, :table_name)
                    ON CONFLICT (cause_id) DO UPDATE 
                    SET cause_name = EXCLUDED.cause_name, 
                        group_id = EXCLUDED.group_id,
                        table_name = EXCLUDED.table_name
                    RETURNING indicator_id
                """), {
                    'cause_id': cause_id,
                    'cause_name': cause_name,
                    'group_id': group_id,
                    'table_name': table_name
                })
                result = conn.execute(text(
                    "SELECT indicator_id FROM disease_indicators WHERE cause_id = :cause_id"
                ), {'cause_id': cause_id})
                indicator_id = result.fetchone()[0]
                indicator_map[cause_id] = indicator_id
                conn.commit()
                
                # Inicializácia zoznamu pre túto tabuľku
                if table_name not in table_data:
                    table_data[table_name] = []
            
            logging.info(f"\n   ✓ Vytvorených {len(created_tables)} tabuliek pre {len(causes)} chorôb")
            
            # 3. Import faktov do tabuliek
            logging.info("\n3. Importovanie faktov o chorobách...")
            for _, row in df_health.iterrows():
                cause_id = int(row['cause_id'])
                indicator_id = indicator_map.get(cause_id)
                
                if indicator_id:
                    # Získanie table_name pre tento indikátor
                    result = conn.execute(text(
                        "SELECT table_name FROM disease_indicators WHERE indicator_id = :id"
                    ), {'id': indicator_id})
                    table_name = result.fetchone()[0]
                    
                    if table_name:
                        table_data[table_name].append({
                            'sex': row['sex_name'],
                            'age': row['age_name'],
                            'year': int(row['year']),
                            'indicator_id': indicator_id,
                            'measure': row['measure_name'],
                            'value': int(row['val'])
                        })
            
            # Vloženie do tabuliek
            total_records = 0
            for table_name, records in table_data.items():
                if records:
                    df_insert = pd.DataFrame(records)
                    df_insert.to_sql(table_name, engine, if_exists='append', index=False, method='multi')
                    total_records += len(records)
                    logging.info(f"   ✓ {table_name}: {len(records)} záznamov")
            
            logging.info(f"\n   📊 CELKOM: {len(created_tables)} tabuliek, {total_records} záznamov")
            
            # ========================================
            # DOMÉNA 2: PROSTREDIE
            # ========================================
            
            print("\n" + "="*70)
            print("DOMÉNA 2: PROSTREDIE")
            print("="*70)
            
            df_risks = df_filtered[df_filtered['rei_id'].notna()].copy()
            
            # 1. Vytvorenie env skupín
            logging.info("\n1. Vytváranie environmentálnych skupín...")
            for group_code, group_name in ENV_GROUPS.items():
                conn.execute(text("""
                    INSERT INTO environment_groups (group_code, group_name)
                    VALUES (:code, :name)
                    ON CONFLICT (group_code) DO UPDATE SET group_name = EXCLUDED.group_name
                """), {'code': group_code, 'name': group_name})
                conn.commit()
            logging.info(f"   ✓ {len(ENV_GROUPS)} skupín")
            
            # 2. Spracovanie env rizík
            logging.info("\n2. Spracovanie env rizík (vytvorenie indikátorov a tabuliek)...")
            env_risks = df_risks[['rei_id', 'rei_name']].dropna().drop_duplicates()
            
            env_indicator_map = {}
            env_table_data = {}
            env_created_tables = set()
            
            for _, row in env_risks.iterrows():
                rei_id = int(row['rei_id'])
                rei_name = row['rei_name']
                
                group_code = categorize_env(rei_name)
                if not group_code:
                    continue
                
                result = conn.execute(text(
                    "SELECT group_id FROM environment_groups WHERE group_code = :code"
                ), {'code': group_code})
                group_id = result.fetchone()[0]
                
                table_name = normalize_env_table_name(rei_name)
                
                # Vytvorenie tabuľky
                if table_name not in env_created_tables:
                    try:
                        conn.execute(text("SELECT create_environment_table(:table_name)"), 
                                   {'table_name': table_name})
                        conn.commit()
                        env_created_tables.add(table_name)
                        logging.info(f"   ✓ Vytvorená tabuľka: {table_name}")
                    except Exception as e:
                        logging.warning(f"   ⚠ Tabuľka {table_name}: {e}")
                
                # Vytvorenie indikátora
                conn.execute(text("""
                    INSERT INTO environment_indicators (rei_id, rei_name, group_id, table_name)
                    VALUES (:rei_id, :rei_name, :group_id, :table_name)
                    ON CONFLICT (rei_id) DO UPDATE 
                    SET rei_name = EXCLUDED.rei_name, 
                        group_id = EXCLUDED.group_id,
                        table_name = EXCLUDED.table_name
                    RETURNING indicator_id
                """), {
                    'rei_id': rei_id,
                    'rei_name': rei_name,
                    'group_id': group_id,
                    'table_name': table_name
                })
                result = conn.execute(text(
                    "SELECT indicator_id FROM environment_indicators WHERE rei_id = :rei_id"
                ), {'rei_id': rei_id})
                env_indicator_map[rei_id] = result.fetchone()[0]
                conn.commit()
                
                if table_name not in env_table_data:
                    env_table_data[table_name] = []
            
            logging.info(f"\n   ✓ Vytvorených {len(env_created_tables)} env tabuliek")
            
            # 3. Import env faktov
            logging.info("\n3. Importovanie environmentálnych faktov...")
            for _, row in df_risks.iterrows():
                rei_id = int(row['rei_id'])
                cause_id = int(row['cause_id'])
                
                env_indicator_id = env_indicator_map.get(rei_id)
                disease_indicator_id = indicator_map.get(cause_id)
                
                if env_indicator_id and disease_indicator_id:
                    result = conn.execute(text(
                        "SELECT table_name FROM environment_indicators WHERE indicator_id = :id"
                    ), {'id': env_indicator_id})
                    table_name = result.fetchone()[0]
                    
                    if table_name:
                        env_table_data[table_name].append({
                            'sex': row['sex_name'],
                            'age': row['age_name'],
                            'year': int(row['year']),
                            'disease_indicator_id': disease_indicator_id,
                            'env_indicator_id': env_indicator_id,
                            'measure': row['measure_name'],
                            'value': int(row['val'])
                        })
            
            env_total_records = 0
            for table_name, records in env_table_data.items():
                if records:
                    df_insert = pd.DataFrame(records)
                    df_insert.to_sql(table_name, engine, if_exists='append', index=False, method='multi')
                    env_total_records += len(records)
                    logging.info(f"   ✓ {table_name}: {len(records)} záznamov")
            
            logging.info(f"\n   📊 CELKOM: {len(env_created_tables)} tabuliek, {env_total_records} záznamov")
            
            # ========================================
            # DOMÉNA 3: ŽIVOTNÝ ŠTÝL
            # ========================================
            
            print("\n" + "="*70)
            print("DOMÉNA 3: ŽIVOTNÝ ŠTÝL")
            print("="*70)
            
            # Filter cirkulárnych závislostí
            df_risks_clean = df_risks.copy()
            df_risks_clean = df_risks_clean[
                ~df_risks_clean['cause_name'].str.lower().str.strip().isin(CIRCULAR_DEPENDENCIES)
            ]
            filtered = len(df_risks) - len(df_risks_clean)
            if filtered > 0:
                logging.info(f"\n⚠  Vyfiltrovaných {filtered} cirkulárnych závislostí")
            
            # 1. Vytvorenie lifestyle skupín
            logging.info("\n1. Vytváranie lifestyle skupín...")
            for group_code, group_name in LIFESTYLE_GROUPS.items():
                conn.execute(text("""
                    INSERT INTO lifestyle_groups (group_code, group_name)
                    VALUES (:code, :name)
                    ON CONFLICT (group_code) DO UPDATE SET group_name = EXCLUDED.group_name
                """), {'code': group_code, 'name': group_name})
                conn.commit()
            logging.info(f"   ✓ {len(LIFESTYLE_GROUPS)} skupín")
            
            # 2. Spracovanie lifestyle rizík
            logging.info("\n2. Spracovanie lifestyle rizík (vytvorenie indikátorov a tabuliek)...")
            lifestyle_risks = df_risks_clean[['rei_id', 'rei_name']].dropna().drop_duplicates()
            
            lifestyle_indicator_map = {}
            lifestyle_table_data = {}
            lifestyle_created_tables = set()
            
            for _, row in lifestyle_risks.iterrows():
                rei_id = int(row['rei_id'])
                rei_name = row['rei_name']
                
                group_code = categorize_lifestyle(rei_name)
                if not group_code:
                    continue
                
                result = conn.execute(text(
                    "SELECT group_id FROM lifestyle_groups WHERE group_code = :code"
                ), {'code': group_code})
                group_id = result.fetchone()[0]
                
                table_name = normalize_lifestyle_table_name(rei_name)
                
                # Vytvorenie tabuľky
                if table_name not in lifestyle_created_tables:
                    try:
                        conn.execute(text("SELECT create_lifestyle_table(:table_name)"), 
                                   {'table_name': table_name})
                        conn.commit()
                        lifestyle_created_tables.add(table_name)
                        logging.info(f"   ✓ Vytvorená tabuľka: {table_name}")
                    except Exception as e:
                        logging.warning(f"   ⚠ Tabuľka {table_name}: {e}")
                
                # Vytvorenie indikátora
                conn.execute(text("""
                    INSERT INTO lifestyle_indicators (rei_id, rei_name, group_id, table_name)
                    VALUES (:rei_id, :rei_name, :group_id, :table_name)
                    ON CONFLICT (rei_id) DO UPDATE 
                    SET rei_name = EXCLUDED.rei_name, 
                        group_id = EXCLUDED.group_id,
                        table_name = EXCLUDED.table_name
                    RETURNING indicator_id
                """), {
                    'rei_id': rei_id,
                    'rei_name': rei_name,
                    'group_id': group_id,
                    'table_name': table_name
                })
                result = conn.execute(text(
                    "SELECT indicator_id FROM lifestyle_indicators WHERE rei_id = :rei_id"
                ), {'rei_id': rei_id})
                lifestyle_indicator_map[rei_id] = result.fetchone()[0]
                conn.commit()
                
                if table_name not in lifestyle_table_data:
                    lifestyle_table_data[table_name] = []
            
            logging.info(f"\n   ✓ Vytvorených {len(lifestyle_created_tables)} lifestyle tabuliek")
            
            # 3. Import lifestyle faktov
            logging.info("\n3. Importovanie lifestyle faktov...")
            
            for _, row in df_risks_clean.iterrows():
                rei_id = int(row['rei_id'])
                cause_id = int(row['cause_id'])
                
                lifestyle_indicator_id = lifestyle_indicator_map.get(rei_id)
                disease_indicator_id = indicator_map.get(cause_id)
                
                if lifestyle_indicator_id and disease_indicator_id:
                    result = conn.execute(text(
                        "SELECT table_name FROM lifestyle_indicators WHERE indicator_id = :id"
                    ), {'id': lifestyle_indicator_id})
                    table_name = result.fetchone()[0]
                    
                    if table_name:
                        lifestyle_table_data[table_name].append({
                            'sex': row['sex_name'],
                            'age': row['age_name'],
                            'year': int(row['year']),
                            'disease_indicator_id': disease_indicator_id,
                            'lifestyle_indicator_id': lifestyle_indicator_id,
                            'measure': row['measure_name'],
                            'value': int(row['val'])
                        })
            
            lifestyle_total_records = 0
            for table_name, records in lifestyle_table_data.items():
                if records:
                    df_insert = pd.DataFrame(records)
                    df_insert.to_sql(table_name, engine, if_exists='append', index=False, method='multi')
                    lifestyle_total_records += len(records)
                    logging.info(f"   ✓ {table_name}: {len(records)} záznamov")
            
            logging.info(f"\n   📊 CELKOM: {len(lifestyle_created_tables)} tabuliek, {lifestyle_total_records} záznamov")
            
            # ========================================
            # SÚHRN
            # ========================================
            
            print("\n" + "="*70)
            print("IMPORT DOKONČENÝ")
            print("="*70)
            print(f"Choroby:      {len(created_tables):3d} tabuliek, {total_records:6d} záznamov")
            print(f"Prostredie:   {len(env_created_tables):3d} tabuliek, {env_total_records:6d} záznamov")
            print(f"Život. štýl:  {len(lifestyle_created_tables):3d} tabuliek, {lifestyle_total_records:6d} záznamov")
            print(f"CELKOM:       {len(created_tables) + len(env_created_tables) + len(lifestyle_created_tables):3d} tabuliek, {total_records + env_total_records + lifestyle_total_records:6d} záznamov")
            print("="*70)
            
    except Exception as e:
        logging.error(f"\nImport zlyhal: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == '__main__':
    import_data()

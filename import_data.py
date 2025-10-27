from sqlalchemy import create_engine, text
import pandas as pd
import logging
import os

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
CSV_DIR = 'data_csv'
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
    df.columns = df.columns.str.split('+').str[0].str.replace('#', '')
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
    """
    Kategorizuje indikátor do správnej tabuľky a kategórie.
    Vracia: (typ_tabulky, nazov_kategorie, kod_kategorie, uroven_zavaznosti, typ_merania)
    """
    indicator_lower = str(indicator_name).lower()

    # === FINANCOVANIE ===
    if csv_type == 'financing':
        return ('financovanie', None, None, None, None)

    # === ENVIRONMENTÁLNE FAKTORY ===
    if csv_type == 'air_pollution' or csv_type == 'environment':
        return ('environment', None, None, None, None)

    # === ŽIVOTNÝ ŠTÝL ===

    # Vakcinácia (prevencia, nie choroba!)
    if any(word in indicator_lower for word in ['immunization', 'vaccination', 'vaccine', 'measles vaccine', 'diphtheria', 'polio', 'bcg', 'hepb']):
        return ('zivotny_styl', 'vakcinacia', 'VACCINATION', None, None)

    # Alkohol
    if csv_type == 'alcohol' or any(word in indicator_lower for word in ['alcohol', 'drinking']):
        return ('zivotny_styl', 'alkohol', 'ALCOHOL', None, None)

    # Fajčenie
    if any(word in indicator_lower for word in ['tobacco', 'smoking', 'cigarette']):
        return ('zivotny_styl', 'fajcenie', 'TOBACCO', None, None)

    # Výživa
    if csv_type == 'nutrition' or any(word in indicator_lower for word in ['obesity', 'overweight', 'bmi', 'underweight', 'thinness', 'anaemia', 'anemia', 'nutrition', 'malnutrition']):
        return ('zivotny_styl', 'vyziva', 'NUTRITION', None, None)

    # === CHOROBY ===

    # Určenie typu merania
    typ_merania = None
    if any(word in indicator_lower for word in ['mortality', 'death', 'deaths']):
        typ_merania = 'mortality'
    elif any(word in indicator_lower for word in ['incidence', 'new cases']):
        typ_merania = 'incidence'
    elif any(word in indicator_lower for word in ['prevalence']):
        typ_merania = 'prevalence'
    elif any(word in indicator_lower for word in ['cases', 'number of']):
        typ_merania = 'cases'

    # Infekčné choroby
    if any(word in indicator_lower for word in ['hepatitis', 'hiv', 'aids', 'malaria', 'tuberculosis', 'tb ', 'infection', 'infectious', 'covid', 'influenza', 'measles', 'rubella', 'tetanus']):
        return ('choroba', 'Infekčné choroby', 'INFECTIOUS', 5, typ_merania)

    # Respiračné ochorenia
    if any(word in indicator_lower for word in ['respiratory', 'asthma', 'copd', 'pneumonia', 'lung disease', 'bronchitis']):
        return ('choroba', 'Respiračné ochorenia', 'RESPIRATORY', 4, typ_merania)

    # Kardiovaskulárne ochorenia
    if any(word in indicator_lower for word in ['cardiovascular', 'heart', 'stroke', 'hypertension', 'blood pressure', 'cardiac', 'ischemic']):
        return ('choroba', 'Kardiovaskulárne ochorenia', 'CARDIOVASCULAR', 5, typ_merania)

    # Rakoviny
    if any(word in indicator_lower for word in ['cancer', 'carcinoma', 'neoplasm', 'tumor', 'tumour', 'malignant']):
        return ('choroba', 'Rakoviny', 'CANCER', 5, typ_merania)

    # Metabolické ochorenia
    if any(word in indicator_lower for word in ['diabetes', 'metabolic', 'obesity-related disease']):
        return ('choroba', 'Metabolické ochorenia', 'METABOLIC', 4, typ_merania)

    # Zdravie matiek a detí
    if any(word in indicator_lower for word in ['birth', 'neonatal', 'infant', 'maternal', 'pregnancy', 'child health', 'perinatal']):
        return ('choroba', 'Zdravie matiek a detí', 'MATERNAL_CHILD', 5, typ_merania)

    # Neuropsychiatrické poruchy
    if any(word in indicator_lower for word in ['mental', 'depression', 'anxiety', 'neurological', 'alzheimer', 'dementia', 'epilepsy']):
        return ('choroba', 'Neuropsychiatrické poruchy', 'NEUROPSYCHIATRIC', 4, typ_merania)

    # Ostatné choroby
    return ('choroba', 'Ostatné ochorenia', 'OTHER_DISEASE', 3, typ_merania)


def load_csv_data(csv_path, csv_type):
    """Načíta dáta z CSV súboru."""
    try:
        if not os.path.exists(csv_path):
            logging.warning(f"Súbor nebol nájdený: {csv_path}")
            return None

        logging.info(f"Načítavam {csv_type}: '{csv_path}'...")
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
            conn.execute(text("TRUNCATE TABLE vyskyt_chorob, zivotny_styl_data, environmentalne_faktory, financovanie_zdravotnictva RESTART IDENTITY CASCADE;"))
            conn.execute(text("TRUNCATE TABLE choroby, zivotny_styl RESTART IDENTITY CASCADE;"))
            conn.execute(text("TRUNCATE TABLE kategorie_chorob, demograficke_skupiny RESTART IDENTITY CASCADE;"))
            conn.commit()
            logging.info("✓ Dáta vyčistené\n")

            # 2. Import demografických skupín
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

            # 3. Príprava kategórií chorôb a faktorov životného štýlu
            logging.info("Vytváram kategórie chorôb a faktorov životného štýlu...")

            kategorie_chorob = {}
            choroby_map = {}
            zivotny_styl_map = {}

            for csv_type, df in all_data.items():
                if df is None or df.empty:
                    continue

                for _, row in df.iterrows():
                    gho_kod = row.get('gho_code', '')
                    gho_nazov = row.get('gho_display', '')
                    gho_url = row.get('gho_url', '')

                    if pd.isna(gho_kod):
                        continue

                    typ_tabulky, nazov_kategorie, kod_kategorie, uroven, _ = categorize_indicator(
                        gho_nazov, gho_kod, csv_type
                    )

                    # === CHOROBY ===
                    if typ_tabulky == 'choroba':
                        # Vytvor kategóriu choroby, ak neexistuje
                        if kod_kategorie not in kategorie_chorob:
                            result = conn.execute(text("""
                                INSERT INTO kategorie_chorob (nazov, kod, popis)
                                VALUES (:nazov, :kod, :popis)
                                ON CONFLICT (kod) DO UPDATE SET nazov = EXCLUDED.nazov
                                RETURNING id
                            """), {
                                'nazov': nazov_kategorie,
                                'kod': kod_kategorie,
                                'popis': f'Kategória: {nazov_kategorie}'
                            })
                            kategorie_chorob[kod_kategorie] = result.fetchone()[0]

                        # Vytvor chorobu, ak neexistuje
                        if gho_kod not in choroby_map:
                            result = conn.execute(text("""
                                INSERT INTO choroby (nazov, kod, kategoria_id, url, uroven_zavaznosti)
                                VALUES (:nazov, :kod, :kat_id, :url, :uroven)
                                ON CONFLICT (kod) DO UPDATE SET nazov = EXCLUDED.nazov
                                RETURNING id
                            """), {
                                'nazov': gho_nazov[:500],
                                'kod': gho_kod,
                                'kat_id': kategorie_chorob[kod_kategorie],
                                'url': gho_url,
                                'uroven': uroven
                            })
                            choroby_map[gho_kod] = result.fetchone()[0]

                    # === ŽIVOTNÝ ŠTÝL ===
                    elif typ_tabulky == 'zivotny_styl':
                        if gho_kod not in zivotny_styl_map:
                            result = conn.execute(text("""
                                INSERT INTO zivotny_styl (nazov, kod, kategoria, url)
                                VALUES (:nazov, :kod, :kategoria, :url)
                                ON CONFLICT (kod) DO UPDATE SET nazov = EXCLUDED.nazov
                                RETURNING id
                            """), {
                                'nazov': gho_nazov[:200],
                                'kod': gho_kod,
                                'kategoria': nazov_kategorie,
                                'url': gho_url
                            })
                            zivotny_styl_map[gho_kod] = result.fetchone()[0]

            conn.commit()
            logging.info(f"  ✓ Vytvorených {len(kategorie_chorob)} kategórií chorôb")
            logging.info(f"  ✓ Vytvorených {len(choroby_map)} chorôb")
            logging.info(f"  ✓ Vytvorených {len(zivotny_styl_map)} faktorov životného štýlu\n")

            # 4. Import meraní
            logging.info("Importujem merania...\n")

            counts = {
                'vyskyt_chorob': 0,
                'zivotny_styl_data': 0,
                'environmentalne_faktory': 0,
                'financovanie_zdravotnictva': 0
            }

            for csv_type, df in all_data.items():
                if df is None or df.empty:
                    continue

                logging.info(f"  Spracovávam {csv_type}...")
                type_count = 0
                error_count = 0
                skipped_count = 0
                category_counts = {'choroba': 0, 'zivotny_styl': 0, 'environment': 0, 'financovanie': 0}

                for _, row in df.iterrows():
                    gho_kod = row.get('gho_code', '')
                    rok = row.get('year_display')

                    if pd.isna(gho_kod) or pd.isna(rok):
                        skipped_count += 1
                        continue

                    gho_nazov = row.get('gho_display', '')
                    typ_tabulky, _, _, _, typ_merania = categorize_indicator(gho_nazov, gho_kod, csv_type)
                    category_counts[typ_tabulky] = category_counts.get(typ_tabulky, 0) + 1

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
                        # === VYSKYT CHORÔB ===
                        if typ_tabulky == 'choroba' and gho_kod in choroby_map:
                            conn.execute(text("""
                                INSERT INTO vyskyt_chorob
                                (choroba_id, demografie_id, rok, hodnota_cislo, hodnota_text,
                                 dolna_hranica, horna_hranica, typ_merania, region_kod, region_nazov,
                                 krajina_kod, krajina_nazov, zdroj_url)
                                VALUES (:choroba_id, :demo_id, :rok, :h_cislo, :h_text, :dolna, :horna,
                                        :typ_mer, :reg_kod, :reg_nazov, :kraj_kod, :kraj_nazov, :url)
                            """), {
                                'choroba_id': choroby_map[gho_kod],
                                'demo_id': demo_id,
                                'rok': int(rok),
                                'h_cislo': float(hodnota_cislo) if pd.notna(hodnota_cislo) else None,
                                'h_text': str(hodnota_text)[:200] if pd.notna(hodnota_text) else None,
                                'dolna': float(dolna) if pd.notna(dolna) else None,
                                'horna': float(horna) if pd.notna(horna) else None,
                                'typ_mer': typ_merania,
                                'reg_kod': row.get('region_code'),
                                'reg_nazov': row.get('region_display'),
                                'kraj_kod': row.get('country_code'),
                                'kraj_nazov': row.get('country_display'),
                                'url': row.get('gho_url', '')
                            })
                            counts['vyskyt_chorob'] += 1
                            type_count += 1

                        # === ŽIVOTNÝ ŠTÝL ===
                        elif typ_tabulky == 'zivotny_styl' and gho_kod in zivotny_styl_map:
                            typ_alkoholu = None
                            severity = None

                            if 'dimension_type' in row and row.get('dimension_type') == 'ALCOHOLTYPE':
                                typ_alkoholu = row.get('dimension_name')

                            if 'severity' in row and pd.notna(row.get('severity')):
                                severity = row.get('severity')

                            typ_merania_zs = gho_nazov[:200]

                            conn.execute(text("""
                                INSERT INTO zivotny_styl_data
                                (zivotny_styl_id, demografie_id, rok, hodnota_cislo, hodnota_text,
                                 dolna_hranica, horna_hranica, typ_alkoholu, typ_merania, severity, zdroj_url)
                                VALUES (:zs_id, :demo_id, :rok, :h_cislo, :h_text, :dolna, :horna,
                                        :typ_alk, :typ_mer, :severity, :url)
                            """), {
                                'zs_id': zivotny_styl_map[gho_kod],
                                'demo_id': demo_id,
                                'rok': int(rok),
                                'h_cislo': float(hodnota_cislo) if pd.notna(hodnota_cislo) else None,
                                'h_text': str(hodnota_text)[:200] if pd.notna(hodnota_text) else None,
                                'dolna': float(dolna) if pd.notna(dolna) else None,
                                'horna': float(horna) if pd.notna(horna) else None,
                                'typ_alk': str(typ_alkoholu)[:100] if pd.notna(typ_alkoholu) else None,
                                'typ_mer': typ_merania_zs,
                                'severity': severity,
                                'url': row.get('gho_url', '')
                            })
                            counts['zivotny_styl_data'] += 1
                            type_count += 1

                        # === ENVIRONMENTÁLNE FAKTORY ===
                        elif typ_tabulky == 'environment':
                            conn.execute(text("""
                                INSERT INTO environmentalne_faktory
                                (nazov, kod, rok, demografie_id, hodnota_cislo, hodnota_text,
                                 dolna_hranica, horna_hranica, typ, typ_znecistenia, zdroj_url)
                                VALUES (:nazov, :kod, :rok, :demo_id, :h_cislo, :h_text, :dolna, :horna,
                                        :typ, :typ_znec, :url)
                            """), {
                                'nazov': gho_nazov[:500],
                                'kod': gho_kod,
                                'rok': int(rok),
                                'demo_id': demo_id,
                                'h_cislo': float(hodnota_cislo) if pd.notna(hodnota_cislo) else None,
                                'h_text': str(hodnota_text)[:200] if pd.notna(hodnota_text) else None,
                                'dolna': float(dolna) if pd.notna(dolna) else None,
                                'horna': float(horna) if pd.notna(horna) else None,
                                'typ': csv_type,
                                'typ_znec': gho_nazov[:100],
                                'url': row.get('gho_url', '')
                            })
                            counts['environmentalne_faktory'] += 1
                            type_count += 1

                        # === FINANCOVANIE ===
                        elif typ_tabulky == 'financovanie':
                            typ_vydavku = gho_kod.split('_')[1] if '_' in gho_kod else 'OTHER'

                            conn.execute(text("""
                                INSERT INTO financovanie_zdravotnictva
                                (nazov, kod, rok, hodnota_cislo, hodnota_text, typ_vydavku,
                                 region_kod, region_nazov, krajina_kod, krajina_nazov, zdroj_url)
                                VALUES (:nazov, :kod, :rok, :h_cislo, :h_text, :typ,
                                        :reg_kod, :reg_nazov, :kraj_kod, :kraj_nazov, :url)
                                ON CONFLICT (kod, rok, typ_vydavku) DO NOTHING
                            """), {
                                'nazov': gho_nazov[:500],
                                'kod': gho_kod,
                                'rok': int(rok),
                                'h_cislo': float(hodnota_cislo) if pd.notna(hodnota_cislo) else None,
                                'h_text': str(hodnota_text)[:200] if pd.notna(hodnota_text) else None,
                                'typ': typ_vydavku,
                                'reg_kod': row.get('region_code'),
                                'reg_nazov': row.get('region_display'),
                                'kraj_kod': row.get('country_code'),
                                'kraj_nazov': row.get('country_display'),
                                'url': row.get('gho_url', '')
                            })
                            counts['financovanie_zdravotnictva'] += 1
                            type_count += 1

                    except Exception as e:
                        error_count += 1
                        if error_count <= 5:  # Loguj prvých 5 chýb
                            logging.warning(f"Chyba pri importe riadku ({csv_type}, {gho_kod}): {e}")
                        conn.rollback()  # Rollback na pokračovanie transakcie
                        continue

                # Detailné štatistiky
                logging.info(f"    ✓ Importovaných: {type_count} záznamov")
                if skipped_count > 0:
                    logging.info(f"    ! Preskočených: {skipped_count} (chýbajúci gho_code alebo rok)")
                if error_count > 0:
                    logging.info(f"    ! Chýb pri importe: {error_count}")

                # Kategorizácia
                if category_counts:
                    cat_summary = ", ".join([f"{k}: {v}" for k, v in category_counts.items() if v > 0])
                    logging.info(f"    → Kategorizácia: {cat_summary}")

            conn.commit()

            # Výpis štatistík
            logging.info(f"\n{'='*60}")
            logging.info("IMPORT DOKONČENÝ - ŠTATISTIKY:")
            logging.info(f"{'='*60}")

            # Celkové počty
            total_imported = sum(counts.values())
            total_csv_rows = sum([len(df) for df in all_data.values() if df is not None])
            logging.info(f"  • Celkový počet riadkov v CSV: {total_csv_rows}")
            logging.info(f"  • Celkový počet importovaných: {total_imported}")
            if total_imported < total_csv_rows:
                logging.info(f"  • Rozdiel: {total_csv_rows - total_imported} záznamov sa neimportovalo")
            logging.info("")

            stats = conn.execute(text("""
                SELECT
                    (SELECT COUNT(*) FROM kategorie_chorob) as kategorie_chorob,
                    (SELECT COUNT(*) FROM choroby) as choroby,
                    (SELECT COUNT(*) FROM vyskyt_chorob) as vyskyt_chorob,
                    (SELECT COUNT(*) FROM zivotny_styl) as zivotny_styl,
                    (SELECT COUNT(*) FROM zivotny_styl_data) as zivotny_styl_data,
                    (SELECT COUNT(*) FROM environmentalne_faktory) as env_faktory,
                    (SELECT COUNT(*) FROM financovanie_zdravotnictva) as financovanie,
                    (SELECT COUNT(*) FROM demograficke_skupiny) as demografie
            """)).fetchone()

            logging.info(f"  • Kategórie chorôb: {stats[0]}")
            logging.info(f"  • Choroby: {stats[1]}")
            logging.info(f"  • Výskyt chorôb (merania): {stats[2]}")
            logging.info(f"  • Faktory životného štýlu: {stats[3]}")
            logging.info(f"  • Dáta o životnom štýle: {stats[4]}")
            logging.info(f"  • Environmentálne faktory: {stats[5]}")
            logging.info(f"  • Financovanie zdravotníctva: {stats[6]}")
            logging.info(f"  • Demografické skupiny: {stats[7]}")
            logging.info(f"{'='*60}\n")

            # Top kategórie chorôb
            logging.info("TOP KATEGÓRIE CHORÔB:")
            top_kat = conn.execute(text("""
                SELECT k.nazov, COUNT(v.id) as pocet
                FROM kategorie_chorob k
                LEFT JOIN choroby c ON c.kategoria_id = k.id
                LEFT JOIN vyskyt_chorob v ON v.choroba_id = c.id
                GROUP BY k.id, k.nazov
                ORDER BY pocet DESC
            """)).fetchall()

            for i, (nazov, pocet) in enumerate(top_kat, 1):
                logging.info(f"  {i}. {nazov}: {pocet} meraní")

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

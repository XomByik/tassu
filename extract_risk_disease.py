#!/usr/bin/env python3
"""
Extract RISK→DISEASE relationships from all 4 countries into PostgreSQL star schema.
Each of the 4 fact tables contains data from ALL 4 countries.
"""

import psycopg2
import re
import sys
import os

# Database connections - use environment variables for Docker compatibility
PG_CONFIG = {
    'host': os.getenv('PG_HOST', 'localhost'),
    'port': int(os.getenv('PG_PORT', '5433')),
    'database': os.getenv('PG_DATABASE', 'tassu_db'),
    'user': os.getenv('PG_USER', 'tassu_user'),
    'password': os.getenv('PG_PASSWORD', 'tassu_password')
}

# SQL files to parse (Germany, Sweden, USA)
SQL_FILES = {
    'DEU': 'databazy_ine_krajiny/germany.sql',  # Germany
    'SWE': 'databazy_ine_krajiny/sweden.sql',  # Sweden
    'USA': 'databazy_ine_krajiny/usa.sql',  # USA
}

# Age group mappings
AGE_MAPPINGS = {
    'DEU': {'1': '0-14', '2': '15-49', '3': '50-69', '4': '70+', '5': 'ALL'},
    'SWE': {'1': '0-14', '2': '15-49', '3': '50-69', '4': '70+', '5': 'ALL'},
    # USA has detailed age groups - map them to WHO standard groups
    'USA': {
        '1': '0-14',   # <5 years
        '23': '0-14',  # 5-14 years
        '8': '15-49',  # 15-19 years
        '9': '15-49',  # 20-24 years
        '10': '15-49', # 25-29 years
        '11': '15-49', # 30-34 years
        '12': '15-49', # 35-39 years
        '13': '15-49', # 40-44 years
        '14': '15-49', # 45-49 years
        '25': '50-69', # 50-69 years
        '19': '70+',   # 70-74 years
        '20': '70+',   # 75-79 years
        '21': '70+',   # 80+ years
    },
    'CHE': {'1': '0-14', '2': '15-49', '3': '50-69', '4': '70+', '5': 'ALL'},
}

# Sex mappings - use single letter codes to match dim_sex
SEX_MAPPINGS = {
    'DEU': {'1': 'M', '2': 'F', '3': 'B'},
    'SWE': {'1': 'M', '2': 'F', '3': 'B'},
    'USA': {'1': 'M', '2': 'F', '3': 'B'},
    'CHE': {'1': 'M', '2': 'F', '3': 'B'},
}

def get_dimension_id(cursor, table, code_column, code_value):
    """Get dimension ID from code."""
    cursor.execute(f"SELECT {table.replace('dim_', '')}_id FROM {table} WHERE {code_column} = %s", (code_value,))
    result = cursor.fetchone()
    return result[0] if result else None

def parse_sql_inserts(sql_content, table_name):
    """Parse INSERT statements from SQL file (supports both MySQL and PostgreSQL format)."""
    # Try MySQL format: INSERT INTO `table_name`
    pattern = rf"INSERT INTO `{table_name}`.*?VALUES\s*(.*?);"
    matches = re.findall(pattern, sql_content, re.DOTALL | re.IGNORECASE)
    
    # Try PostgreSQL format: INSERT INTO public.table_name or schema.table_name
    if not matches:
        pattern = rf"INSERT INTO (?:public\.)?{table_name}.*?VALUES\s*(.*?);"
        matches = re.findall(pattern, sql_content, re.DOTALL | re.IGNORECASE)
    
    all_rows = []
    for match in matches:
        # Split by ),( to get individual rows
        rows = re.findall(r'\((.*?)\)(?:,|\s*$)', match, re.DOTALL)
        for row in rows:
            # Parse values
            values = []
            current = ''
            in_quotes = False
            for char in row:
                if char == "'" and (not current or current[-1] != '\\'):
                    in_quotes = not in_quotes
                elif char == ',' and not in_quotes:
                    values.append(current.strip().strip("'"))
                    current = ''
                    continue
                current += char
            if current:
                values.append(current.strip().strip("'"))
            all_rows.append(values)
    
    return all_rows

def extract_usa_risk_disease(cursor, sql_content):
    """Extract RISK→DISEASE data from USA by combining fact_disease and fact_disease_risk tables."""
    print("  Extracting USA data from fact_disease (total deaths) and fact_disease_risk (attributable deaths)...")
    
    # USA has both total disease deaths and attributable deaths!
    # fact_disease: Total deaths from disease (measure_id=1, Deaths)
    # fact_disease_risk: Attributable deaths (deaths caused by risk factor)
    
    # Parse both tables
    disease_rows = parse_sql_inserts(sql_content, 'fact_disease')
    risk_rows = parse_sql_inserts(sql_content, 'fact_disease_risk')
    print(f"    Parsed {len(disease_rows)} rows from fact_disease, {len(risk_rows)} rows from fact_disease_risk")
    
    data = {
        'smoking_lung_cancer': [],
        'bmi_cardiovascular': [],
        'pollution_respiratory': [],
        'alcohol_cirrhosis': []
    }
    
    # Build total disease deaths dictionary from fact_disease
    # Columns: id, measure_id, sex_id, age_id, cause_id, metric_id, year, value, upper, lower, unit
    # measure_id 1 = Deaths, metric_id 1 = Number (not rate)
    # cause_id: 426=Lung cancer, 493=Ischemic heart, 509=COPD, 521=Cirrhosis
    total_deaths_dict = {}
    for row in disease_rows:
        if len(row) < 8:
            continue
        
        measure_id = row[1]
        sex_id = row[2]
        age_id = row[3]
        cause_id = row[4]
        metric_id = row[5]
        year = row[6]
        value = float(row[7]) if row[7] and row[7] != 'NULL' else 0
        
        # Only deaths (measure_id = 1), metric_id = 1 (Number), years 2014-2023
        if measure_id != '1' or metric_id != '1' or int(year) < 2014 or int(year) > 2023:
            continue
        
        sex_code = SEX_MAPPINGS['USA'].get(sex_id)
        age_code = AGE_MAPPINGS['USA'].get(age_id)
        
        if not sex_code or not age_code:
            continue
        
        # Aggregate by (cause_id, sex, age, year)
        key = (cause_id, sex_code, age_code, year)
        total_deaths_dict[key] = total_deaths_dict.get(key, 0) + value
    
    # Build attributable deaths dictionary from fact_disease_risk
    # Columns: id, measure_id, sex_id, age_id, cause_id, risk_id, metric_id, year, value, upper, lower, unit
    # risk_id: 99=Smoking, 102=High alcohol, 108=High BMI, 85=Air pollution
    attributable_dict = {}
    for row in risk_rows:
        if len(row) < 9:
            continue
        
        measure_id = row[1]
        sex_id = row[2]
        age_id = row[3]
        cause_id = row[4]
        risk_id = row[5]
        metric_id = row[6]
        year = row[7]
        value = float(row[8]) if row[8] and row[8] != 'NULL' else 0
        
        # Only deaths (measure_id = 1), metric_id = 1 (Number), years 2014-2023
        if measure_id != '1' or metric_id != '1' or int(year) < 2014 or int(year) > 2023:
            continue
        
        sex_code = SEX_MAPPINGS['USA'].get(sex_id)
        age_code = AGE_MAPPINGS['USA'].get(age_id)
        
        if not sex_code or not age_code:
            continue
        
        # Filter by specific risk→cause pairs
        if risk_id == '99' and cause_id == '426':  # Smoking → Lung cancer
            key = ('smoking', sex_code, age_code, year, '426')
            attributable_dict[key] = attributable_dict.get(key, 0) + value
        elif risk_id == '108' and cause_id in ('493', '498'):  # High BMI → IHD + Stroke
            key = ('bmi', sex_code, age_code, year, cause_id)
            attributable_dict[key] = attributable_dict.get(key, 0) + value
        elif risk_id == '85' and cause_id in ('509', '322'):  # Air pollution → COPD + LRI
            key = ('pollution', sex_code, age_code, year, cause_id)
            attributable_dict[key] = attributable_dict.get(key, 0) + value
        elif risk_id == '102' and cause_id == '521':  # High alcohol → Cirrhosis
            key = ('alcohol', sex_code, age_code, year, '521')
            attributable_dict[key] = attributable_dict.get(key, 0) + value
    
    # Combine total + attributable deaths
    # Group by (risk_type, sex, age, year) for final output
    combined = {}
    
    # Smoking → Lung cancer (cause=426)
    for (risk_type, sex, age, year, cause_id), attr_value in attributable_dict.items():
        if risk_type == 'smoking':
            key = ('smoking', 'USA', sex, age, year)
            total_value = total_deaths_dict.get((cause_id, sex, age, year), 0)
            if key not in combined:
                combined[key] = {'total': 0, 'attributable': 0}
            combined[key]['total'] += total_value
            combined[key]['attributable'] += attr_value
    
    # BMI → CVD (cause=493,498)
    for (risk_type, sex, age, year, cause_id), attr_value in attributable_dict.items():
        if risk_type == 'bmi':
            key = ('bmi', 'USA', sex, age, year)
            total_value = total_deaths_dict.get((cause_id, sex, age, year), 0)
            if key not in combined:
                combined[key] = {'total': 0, 'attributable': 0}
            combined[key]['total'] += total_value
            combined[key]['attributable'] += attr_value
    
    # Pollution → Respiratory (cause=509,322)
    for (risk_type, sex, age, year, cause_id), attr_value in attributable_dict.items():
        if risk_type == 'pollution':
            key = ('pollution', 'USA', sex, age, year)
            total_value = total_deaths_dict.get((cause_id, sex, age, year), 0)
            if key not in combined:
                combined[key] = {'total': 0, 'attributable': 0}
            combined[key]['total'] += total_value
            combined[key]['attributable'] += attr_value
    
    # Alcohol → Cirrhosis (cause=521)
    for (risk_type, sex, age, year, cause_id), attr_value in attributable_dict.items():
        if risk_type == 'alcohol':
            key = ('alcohol', 'USA', sex, age, year)
            total_value = total_deaths_dict.get((cause_id, sex, age, year), 0)
            if key not in combined:
                combined[key] = {'total': 0, 'attributable': 0}
            combined[key]['total'] += total_value
            combined[key]['attributable'] += attr_value
    
    # Convert to final format: (country, sex, age, year, disease_deaths, attributable_deaths)
    for key, values in combined.items():
        risk_type, country, sex, age, year = key
        if risk_type == 'smoking':
            data['smoking_lung_cancer'].append((country, sex, age, year, values['total'], values['attributable']))
        elif risk_type == 'bmi':
            data['bmi_cardiovascular'].append((country, sex, age, year, values['total'], values['attributable']))
        elif risk_type == 'pollution':
            data['pollution_respiratory'].append((country, sex, age, year, values['total'], values['attributable']))
        elif risk_type == 'alcohol':
            data['alcohol_cirrhosis'].append((country, sex, age, year, values['total'], values['attributable']))
    
    print(f"    Extracted: Smoking→LC={len(data['smoking_lung_cancer'])}, BMI→CVD={len(data['bmi_cardiovascular'])}, Pollution→Resp={len(data['pollution_respiratory'])}, Alcohol→Cirrhosis={len(data['alcohol_cirrhosis'])}")
    
    # Debug: Show sample years
    if len(data['smoking_lung_cancer']) > 0:
        sample_years = set([row[3] for row in data['smoking_lung_cancer'][:10]])
        print(f"    Sample years: {sorted(sample_years)}")
    
    return data
    
    # Debug: Show sample years
    if len(data['smoking_lung_cancer']) > 0:
        sample_years = set([row[3] for row in data['smoking_lung_cancer'][:10]])
        print(f"    Sample years: {sorted(sample_years)}")
    
    return data

def extract_germany_risk_disease(cursor, sql_content):
    """Extract RISK→DISEASE data from Germany by joining separate tables."""
    print("  Extracting Germany data from lm_* and dm_* tables...")
    
    # Germany uses text age groups like "15-19 years", "20-24 years" etc
    # Need to aggregate to WHO groups
    def map_germany_age(age_text):
        """Map Germany age text to WHO standard group."""
        age_text = age_text.strip().upper()
        # Parse numeric range (e.g., '15-19 years')
        match = re.match(r'(\d+)-(\d+)', age_text)
        if match:
            start = int(match.group(1))
            if start < 15:
                return '0-14'
            elif start < 50:
                return '15-49'
            elif start < 70:
                return '50-69'
            else:
                return '70+'
        return None
    
    def map_germany_sex(sex_text):
        """Map Germany sex text to code."""
        sex_text = sex_text.upper()
        if 'MALE' in sex_text and 'FEMALE' not in sex_text:
            return 'M'
        elif 'FEMALE' in sex_text:
            return 'F'
        else:
            return 'B'
    
    data = {
        'smoking_lung_cancer': [],
        'bmi_cardiovascular': [],
        'pollution_respiratory': [],
        'alcohol_cirrhosis': []
    }
    
    # Parse risk factor tables - format: country, sex, age_group, year, value
    tobacco_rows = parse_sql_inserts(sql_content, 'lm_tobaco')
    alcohol_rows = parse_sql_inserts(sql_content, 'lm_alcohol_use_disorders')
    air_pollution_rows = parse_sql_inserts(sql_content, 'em_air_polution')
    
    # Parse SDR (Standardized Death Rate) tables - format: country, sex, year, value (rate per 100k)
    # These aggregate across all age groups and give us proper mortality rates
    lung_cancer_rows = parse_sql_inserts(sql_content, 'dm_lung_cancer_sdr')
    ischemic_heart_rows = parse_sql_inserts(sql_content, 'dm_ischaemic_heart_sdr')  # British spelling
    lower_respiratory_rows = parse_sql_inserts(sql_content, 'dm_chronic_lover_respiratory_sdr')
    liver_disease_rows = parse_sql_inserts(sql_content, 'dm_liver_disiasee_sdr')
    
    # Parse population data to convert rates to absolute deaths
    population_rows = parse_sql_inserts(sql_content, 'population')
    
    print(f"    Parsed Germany tables: tobacco={len(tobacco_rows)}, alcohol={len(alcohol_rows)}, pollution={len(air_pollution_rows)}")
    print(f"    Diseases SDR: lung_cancer={len(lung_cancer_rows)}, ischemic={len(ischemic_heart_rows)}, respiratory={len(lower_respiratory_rows)}, liver={len(liver_disease_rows)}")
    print(f"    Population data: {len(population_rows)} rows")
    
    # Build population dict by (sex, year) - sum across all age groups
    population_dict = {}
    for row in population_rows:
        if len(row) >= 5:
            country, sex_text, age_text, year, pop = row[0], row[1], row[2], row[3], float(row[4]) if row[4] != 'NULL' else 0
            sex_code = map_germany_sex(sex_text)
            if sex_code in ('M', 'F') and 2013 <= int(year) <= 2023:
                key = (sex_code, year)
                population_dict[key] = population_dict.get(key, 0) + pop
    
    # Aggregate tobacco by (sex, year) summing all age groups
    tobacco_dict = {}
    for row in tobacco_rows:
        if len(row) >= 5:
            country, sex_text, age_text, year, value = row[0], row[1], row[2], row[3], float(row[4]) if row[4] != 'NULL' else 0
            sex_code = map_germany_sex(sex_text)
            if sex_code in ('M', 'F') and 2013 <= int(year) <= 2023:
                key = (sex_code, year)
                tobacco_dict[key] = tobacco_dict.get(key, 0) + value

    # Aggregate alcohol
    alcohol_dict = {}
    for row in alcohol_rows:
        if len(row) >= 5:
            country, sex_text, age_text, year, value = row[0], row[1], row[2], row[3], float(row[4]) if row[4] != 'NULL' else 0
            sex_code = map_germany_sex(sex_text)
            if sex_code in ('M', 'F') and 2013 <= int(year) <= 2023:
                key = (sex_code, year)
                alcohol_dict[key] = alcohol_dict.get(key, 0) + value

    # Aggregate air pollution
    air_pollution_dict = {}
    for row in air_pollution_rows:
        if len(row) >= 5:
            country, sex_text, age_text, year, value = row[0], row[1], row[2], row[3], float(row[4]) if row[4] != 'NULL' else 0
            sex_code = map_germany_sex(sex_text)
            if sex_code in ('M', 'F') and 2013 <= int(year) <= 2023:
                key = (sex_code, year)
                air_pollution_dict[key] = air_pollution_dict.get(key, 0) + value

    # Process SDR disease tables (format: country, sex, year, rate_per_100k)
    # Apply attributable fractions (AF) to Germany like Sweden:
    # - Smoking → LC: AF = 0.80 (RKI studies show ~80% of lung cancer attributable to smoking)
    # - BMI → CVD: AF = 0.15 (epidemiological estimate for obesity contribution to CVD)
    # - PM2.5 → Resp: AF = 0.20 (GBD 2019 shows ~20% respiratory deaths from air pollution)
    # - Alcohol → Cirrhosis: AF = 0.48 (Global studies show ~48% of cirrhosis alcohol-attributable)
    
    # Smoking → Lung cancer
    lung_cancer_dict = {}
    for row in lung_cancer_rows:
        if len(row) >= 4:  # SDR tables have no age_group column
            country, sex_text, year, rate = row[0], row[1], row[2], float(row[3]) if row[3] != 'NULL' else 0
            sex_code = map_germany_sex(sex_text)
            if sex_code in ('M', 'F') and 2013 <= int(year) <= 2023:
                key = (sex_code, year)
                # Convert rate per 100k to absolute deaths using population
                pop = population_dict.get(key, 0)
                absolute_deaths = (rate / 100_000) * pop if pop > 0 else 0
                lung_cancer_dict[key] = absolute_deaths

    for key, deaths in lung_cancer_dict.items():
        sex_code, year = key
        # Apply 80% attributable fraction for smoking→LC
        attributable_deaths = deaths * 0.80
        # Store total deaths in disease_deaths, AF-calculated in attributable_deaths
        data['smoking_lung_cancer'].append(('DEU', sex_code, 'ALL', year, deaths, attributable_deaths))
    
    # High BMI → Ischemic heart
    ischemic_dict = {}
    for row in ischemic_heart_rows:
        if len(row) >= 4:
            country, sex_text, year, rate = row[0], row[1], row[2], float(row[3]) if row[3] != 'NULL' else 0
            sex_code = map_germany_sex(sex_text)
            if sex_code in ('M', 'F') and 2013 <= int(year) <= 2023:
                key = (sex_code, year)
                pop = population_dict.get(key, 0)
                absolute_deaths = (rate / 100_000) * pop if pop > 0 else 0
                ischemic_dict[key] = absolute_deaths

    for key, deaths in ischemic_dict.items():
        sex_code, year = key
        # Apply 15% attributable fraction for BMI→CVD
        attributable_deaths = deaths * 0.15
        # Store total CVD deaths, then AF-calculated attributable deaths
        data['bmi_cardiovascular'].append(('DEU', sex_code, 'ALL', year, deaths, attributable_deaths))
    
    # Air pollution → Respiratory
    respiratory_dict = {}
    for row in lower_respiratory_rows:
        if len(row) >= 4:
            country, sex_text, year, rate = row[0], row[1], row[2], float(row[3]) if row[3] != 'NULL' else 0
            sex_code = map_germany_sex(sex_text)
            if sex_code in ('M', 'F') and 2013 <= int(year) <= 2023:
                key = (sex_code, year)
                pop = population_dict.get(key, 0)
                absolute_deaths = (rate / 100_000) * pop if pop > 0 else 0
                respiratory_dict[key] = absolute_deaths

    for key, deaths in respiratory_dict.items():
        sex_code, year = key
        # Apply 20% attributable fraction for pollution→respiratory
        attributable_deaths = deaths * 0.20
        # Store total respiratory deaths, then AF-calculated attributable deaths
        data['pollution_respiratory'].append(('DEU', sex_code, 'ALL', year, deaths, attributable_deaths))
    
    # Alcohol → Liver disease
    liver_dict = {}
    for row in liver_disease_rows:
        if len(row) >= 4:
            country, sex_text, year, rate = row[0], row[1], row[2], float(row[3]) if row[3] != 'NULL' else 0
            sex_code = map_germany_sex(sex_text)
            if sex_code in ('M', 'F') and 2013 <= int(year) <= 2023:
                key = (sex_code, year)
                pop = population_dict.get(key, 0)
                absolute_deaths = (rate / 100_000) * pop if pop > 0 else 0
                liver_dict[key] = absolute_deaths
    
    for key, deaths in liver_dict.items():
        sex_code, year = key
        # Apply 48% attributable fraction for alcohol→cirrhosis (global studies)
        attributable_deaths = deaths * 0.48
        # Store total cirrhosis deaths, then AF-calculated attributable deaths
        data['alcohol_cirrhosis'].append(('DEU', sex_code, 'ALL', year, deaths, attributable_deaths))
    
    print(f"    Extracted Germany: Smoking→LC={len(data['smoking_lung_cancer'])}, BMI→CVD={len(data['bmi_cardiovascular'])}, Pollution→Resp={len(data['pollution_respiratory'])}, Alcohol→Cirrhosis={len(data['alcohol_cirrhosis'])}")
    
    return data

def extract_sweden_risk_disease(cursor, sql_content):
    """Extract RISK→DISEASE data from Sweden by joining faktor_data and disease_data."""
    print("  Extracting Sweden data from faktor_data and disease_data tables...")
    
    # Sweden disease IDs:
    # 12 = Lung cancer (C34)
    # 41 = Ischemic heart diseases (I20-I25)
    # 52 = Chronic lower respiratory (J40-J47)
    # 57 = Liver cirrhosis (K74)
    
    # Sweden faktor IDs:
    # 1 = Smoking
    # 2 = Alcohol
    # 3 = Air pollution
    
    def map_sweden_gender(gender_id):
        """Map Sweden gender_id to sex code."""
        if gender_id == '1':
            return 'M'
        elif gender_id == '2':
            return 'F'
        elif gender_id == '3':
            return 'B'
        return None
    
    data = {
        'smoking_lung_cancer': [],
        'bmi_cardiovascular': [],
        'pollution_respiratory': [],
        'alcohol_cirrhosis': []
    }
    
    # Parse disease_data - structure: id, year_id, disease_id, region_id, gender_id, total_cases, death_cases
    disease_rows = parse_sql_inserts(sql_content, 'disease_data')
    
    # Parse faktor_data - structure: country_region, year_id, gender_id, faktor_id, hfa_code, name, value_pct
    faktor_rows = parse_sql_inserts(sql_content, 'faktor_data')
    
    print(f"    Parsed Sweden tables: disease_data={len(disease_rows)}, faktor_data={len(faktor_rows)}")
    
    # Build disease dictionary by (year_id, gender_id, disease_id)
    # Use only Male (1) and Female (2) - avoid Both (3) to prevent duplication
    disease_dict = {}
    for row in disease_rows:
        if len(row) >= 7:
            year_id, disease_id, region_id, gender_id, total_cases, death_cases = row[1], row[2], row[3], row[4], row[5], row[6]
            
            # ONLY use gender_id=1 (Male) or 2 (Female) to prevent triple-counting
            if gender_id not in ('1', '2'):
                continue
                
            deaths = float(death_cases) if death_cases and death_cases != 'NULL' else 0
            if deaths > 0:
                key = (year_id, gender_id, disease_id)
                disease_dict[key] = disease_dict.get(key, 0) + deaths
    
    # Build faktor dictionary by (year_id, gender_id, faktor_id)
    # Use only Male (1) and Female (2)
    faktor_dict = {}
    for row in faktor_rows:
        if len(row) >= 7:
            country, year_id, gender_id, faktor_id, hfa_code, name, value_pct = row[0], row[1], row[2], row[3], row[4], row[5], row[6]
            
            # ONLY use gender_id=1 (Male) or 2 (Female)
            if gender_id not in ('1', '2'):
                continue
                
            value = float(value_pct) if value_pct and value_pct != 'NULL' else 0
            if value > 0:
                key = (year_id, gender_id, faktor_id)
                faktor_dict[key] = faktor_dict.get(key, 0) + value
    
    # Parse year table to map year_id to actual year
    year_rows = parse_sql_inserts(sql_content, 'rok')
    year_map = {}
    for row in year_rows:
        if len(row) >= 2:
            year_id, year = row[0], row[1]
            year_map[year_id] = year
    
    # Join disease data with faktor data
    # NOTE: Sweden disease_data contains TOTAL deaths, not attributable deaths
    # We apply attributable fractions (AF) based on epidemiological literature:
    # - Smoking → LC: AF = 0.75 (70-80% of LC deaths attributable to smoking)
    # - BMI → CVD: AF = 0.15 (10-20% of CVD attributable to obesity)
    # - Pollution → Resp: AF = 0.20 (15-25% of resp deaths from air pollution)
    # - Alcohol → Cirrhosis: AF = 0.55 (50-60% of cirrhosis from alcohol)
    
    # Smoking (faktor=1) → Lung cancer (disease=12)
    for (year_id, gender_id, disease_id), deaths in disease_dict.items():
        if disease_id != '12':  # Only lung cancer
            continue
        year = year_map.get(year_id)
        if not year or int(year) < 2013 or int(year) > 2023:
            continue
        sex_code = map_sweden_gender(gender_id)
        if not sex_code:
            continue
        
        # Apply 75% attributable fraction for smoking→LC
        attributable_deaths = deaths * 0.75
        # Store total deaths in lung_cancer_deaths, AF-adjusted in attributable_deaths
        data['smoking_lung_cancer'].append(('SWE', sex_code, 'ALL', year, deaths, attributable_deaths))
    
    # High BMI → Cardiovascular (disease=41, no direct BMI faktor - skip or use proxy)
    for (year_id, gender_id, disease_id), deaths in disease_dict.items():
        if disease_id != '41':  # Only ischemic heart
            continue
        year = year_map.get(year_id)
        if not year or int(year) < 2013 or int(year) > 2023:
            continue
        sex_code = map_sweden_gender(gender_id)
        if not sex_code:
            continue
        
        # Apply 15% attributable fraction for BMI→CVD
        attributable_deaths = deaths * 0.15
        # Store total CVD deaths, then AF-adjusted attributable deaths
        data['bmi_cardiovascular'].append(('SWE', sex_code, 'ALL', year, deaths, attributable_deaths))
    
    # Air pollution (faktor=3) → Respiratory (disease=52)
    for (year_id, gender_id, disease_id), deaths in disease_dict.items():
        if disease_id != '52':  # Only chronic respiratory
            continue
        year = year_map.get(year_id)
        if not year or int(year) < 2013 or int(year) > 2023:
            continue
        sex_code = map_sweden_gender(gender_id)
        if not sex_code:
            continue
        
        # Apply 20% attributable fraction for pollution→respiratory
        attributable_deaths = deaths * 0.20
        # Store total respiratory deaths, then AF-adjusted attributable deaths
        data['pollution_respiratory'].append(('SWE', sex_code, 'ALL', year, deaths, attributable_deaths))
    
    # Alcohol (faktor=2) → Cirrhosis (disease=57)
    for (year_id, gender_id, disease_id), deaths in disease_dict.items():
        if disease_id != '57':  # Only liver cirrhosis
            continue
        year = year_map.get(year_id)
        if not year or int(year) < 2013 or int(year) > 2023:
            continue
        sex_code = map_sweden_gender(gender_id)
        if not sex_code:
            continue
        
        # Apply 55% attributable fraction for alcohol→cirrhosis
        attributable_deaths = deaths * 0.55
        # Store total cirrhosis deaths, then AF-adjusted attributable deaths
        data['alcohol_cirrhosis'].append(('SWE', sex_code, 'ALL', year, deaths, attributable_deaths))
    
    print(f"    Extracted Sweden: Smoking→LC={len(data['smoking_lung_cancer'])}, BMI→CVD={len(data['bmi_cardiovascular'])}, Pollution→Resp={len(data['pollution_respiratory'])}, Alcohol→Cirrhosis={len(data['alcohol_cirrhosis'])}")
    
    return data

def extract_switzerland_risk_disease(cursor):
    """Extract RISK→DISEASE data from Switzerland CSV files."""
    print("  Extracting Switzerland data from CSV files (total + attributable deaths)...")
    import pandas as pd
    
    # Switzerland has TWO CSV files:
    # 1. IHME-GBD_2023_DATA-94d9786b-1.csv: Total disease deaths (no risk factor)
    # 2. IHME-GBD_2023_DATA-cea2d4bb-1.csv: Attributable deaths (with risk factor rei_id)
    
    attributable_csv = 'data_csv/IHME-GBD_2023_DATA-cea2d4bb-1.csv'
    total_csv = 'data_csv/IHME-GBD_2023_DATA-94d9786b-1.csv'
    
    try:
        df_attributable = pd.read_csv(attributable_csv)
        df_total = pd.read_csv(total_csv)
    except FileNotFoundError as e:
        print(f"    ERROR: Switzerland CSV file not found: {e}")
        return {}

    # Filter for required data: Deaths, Number metric, years 2013-2023
    df_attributable = df_attributable[(df_attributable['measure_name'] == 'Deaths') & 
                                       (df_attributable['metric_name'] == 'Number') & 
                                       (df_attributable['year'].between(2013, 2023))]
    
    df_total = df_total[(df_total['measure_name'] == 'Deaths') & 
                        (df_total['metric_name'] == 'Number') & 
                        (df_total['year'].between(2013, 2023))]

    # Filter out 'Both' sex to avoid duplication
    df_attributable = df_attributable[df_attributable['sex_name'].isin(['Male', 'Female'])]
    df_total = df_total[df_total['sex_name'].isin(['Male', 'Female'])]

    print(f"    Filtered: {len(df_attributable)} attributable rows, {len(df_total)} total rows")

    # Map age groups
    def map_swiss_age(age_name):
        if age_name in ['<5 years', '5-14 years']:
            return '0-14'
        elif age_name in ['15-49 years', '15-19 years', '20-24 years', '25-29 years', '30-34 years', '35-39 years', '40-44 years', '45-49 years']:
            return '15-49'
        elif age_name in ['50-69 years']:
            return '50-69'
        elif age_name in ['70+ years', '70-74 years', '75-79 years', '80+ years']:
            return '70+'
        elif 'all ages' in age_name.lower():
            return 'ALL'
        return None

    df_attributable['age_group'] = df_attributable['age_name'].apply(map_swiss_age)
    df_attributable = df_attributable.dropna(subset=['age_group'])
    
    df_total['age_group'] = df_total['age_name'].apply(map_swiss_age)
    df_total = df_total.dropna(subset=['age_group'])

    # Map sex names to codes
    df_attributable['sex_code'] = df_attributable['sex_name'].map({'Male': 'M', 'Female': 'F'})
    df_total['sex_code'] = df_total['sex_name'].map({'Male': 'M', 'Female': 'F'})

    data = {
        'smoking_lung_cancer': [],
        'bmi_cardiovascular': [],
        'pollution_respiratory': [],
        'alcohol_cirrhosis': []
    }

    # Define mappings from CSV names to our facts
    # Format: (risks for attributable, causes for both attributable and total)
    fact_mappings = {
        'smoking_lung_cancer': (['Smoking'], ['Tracheal, bronchus, and lung cancer']),
        'bmi_cardiovascular': (['High body-mass index'], ['Cardiovascular diseases', 'Ischemic heart disease']),
        'pollution_respiratory': (['Particulate matter pollution'], ['Chronic respiratory diseases', 'Chronic obstructive pulmonary disease']),
        'alcohol_cirrhosis': (['High alcohol use'], ['Cirrhosis and other chronic liver diseases'])
    }

    for fact, (risks, causes) in fact_mappings.items():
        # Extract attributable deaths (from risk→disease CSV)
        attr_df = df_attributable[df_attributable['rei_name'].isin(risks) & df_attributable['cause_name'].isin(causes)]
        attr_grouped = attr_df.groupby(['year', 'sex_code', 'age_group'])['val'].sum().reset_index()
        attr_dict = {(row['year'], row['sex_code'], row['age_group']): row['val'] for _, row in attr_grouped.iterrows()}
        
        # Extract total disease deaths (from disease-only CSV)
        total_df = df_total[df_total['cause_name'].isin(causes)]
        total_grouped = total_df.groupby(['year', 'sex_code', 'age_group'])['val'].sum().reset_index()
        
        # Combine: total deaths + attributable deaths
        for _, row in total_grouped.iterrows():
            year = str(row['year'])
            sex_code = row['sex_code']
            age_group = row['age_group']
            total_deaths = row['val']
            
            # Get corresponding attributable deaths
            attributable_deaths = attr_dict.get((row['year'], sex_code, age_group), 0)
            
            # Append tuple: (country, sex, age, year, disease_deaths, attributable_deaths)
            # Switzerland has both total and attributable from IHME CSVs
            data[fact].append(('CHE', sex_code, age_group, year, total_deaths, attributable_deaths))

    print(f"    Extracted Switzerland: Smoking→LC={len(data['smoking_lung_cancer'])}, BMI→CVD={len(data['bmi_cardiovascular'])}, Pollution→Resp={len(data['pollution_respiratory'])}, Alcohol→Cirrhosis={len(data['alcohol_cirrhosis'])}")
    
    return data
    
    csv_files = glob.glob('/data/data_csv/IHME-GBD_2023_DATA-*.csv')
    if not csv_files:
        print("    WARNING: No Swiss CSV files found in /data/data_csv/")
        return data
    
    print(f"    Found {len(csv_files)} CSV files to process")
    
    # Risk IDs from GBD: 99=Smoking, 102=Alcohol, 108=BMI, 85=Air pollution
    # Cause IDs: 426=Lung cancer, 493=Ischemic heart disease, 509=COPD/Respiratory, 521=Cirrhosis
    
    aggregated = {}
    
    for csv_file in csv_files:
        print(f"    Processing {csv_file}")
        df = pd.read_csv(csv_file, low_memory=False)
        
        # Filter: location='Swiss Confederation', measure='Deaths', year 2014-2018
        df = df[
            (df['location_name'].str.contains('Swiss', case=False, na=False)) &
            (df['measure_name'] == 'Deaths') &
            (df['year'] >= 2014) &
            (df['year'] <= 2018)
        ]
        
        if df.empty:
            continue
        
        # Check if this is risk→disease data (has rei_id or risk_id) or disease-only data
        if 'rei_id' not in df.columns and 'risk_id' not in df.columns:
            print(f"      Skipping (no rei_id/risk_id column)")
            continue
        
        # Use rei_id if available, otherwise risk_id
        risk_col = 'rei_id' if 'rei_id' in df.columns else 'risk_id'
        
        # Map sex
        df['sex_code'] = df['sex_id'].map({1: 'M', 2: 'F', 3: 'B'})
        
        # Map age (similar to USA)
        def map_swiss_age(age_id):
            if age_id in [2, 3, 4]:  # 0-14 years
                return '0-14'
            elif age_id in range(8, 18):  # 15-49 years
                return '15-49'
            elif age_id in range(18, 22):  # 50-69 years
                return '50-69'
            elif age_id in range(22, 26):  # 70+ years
                return '70+'
            else:
                return None
        
        df['age_code'] = df['age_id'].apply(map_swiss_age)
        df = df.dropna(subset=['sex_code', 'age_code'])
        
        # Aggregate by (risk, sex, age, year)
        for _, row in df.iterrows():
            risk_id = str(row.get(risk_col, ''))
            cause_id = str(row.get('cause_id', ''))
            sex_code = row['sex_code']
            age_code = row['age_code']
            year = str(int(row['year']))
            deaths = float(row['val']) if pd.notna(row['val']) else 0
            
            if risk_id == '99' and cause_id == '426':  # Smoking → Lung cancer
                key = ('smoking', 'CHE', sex_code, age_code, year)
                aggregated[key] = aggregated.get(key, 0) + deaths
            elif risk_id == '108' and cause_id == '493':  # BMI → Cardiovascular
                key = ('bmi', 'CHE', sex_code, age_code, year)
                aggregated[key] = aggregated.get(key, 0) + deaths
            elif risk_id == '380' and cause_id == '509':  # Particulate matter pollution → Respiratory (COPD)
                key = ('pollution', 'CHE', sex_code, age_code, year)
                aggregated[key] = aggregated.get(key, 0) + deaths
            elif risk_id == '102' and cause_id == '521':  # Alcohol → Cirrhosis
                key = ('alcohol', 'CHE', sex_code, age_code, year)
                aggregated[key] = aggregated.get(key, 0) + deaths
    
    # Convert to list format
    for key, deaths in aggregated.items():
        risk_type, country, sex, age, year = key
        if risk_type == 'smoking':
            data['smoking_lung_cancer'].append((country, sex, age, year, deaths, deaths))
        elif risk_type == 'bmi':
            data['bmi_cardiovascular'].append((country, sex, age, year, deaths, deaths))
        elif risk_type == 'pollution':
            data['pollution_respiratory'].append((country, sex, age, year, deaths, deaths))
        elif risk_type == 'alcohol':
            data['alcohol_cirrhosis'].append((country, sex, age, year, deaths, deaths))
    
    print(f"    Extracted Switzerland: Smoking→LC={len(data['smoking_lung_cancer'])}, BMI→CVD={len(data['bmi_cardiovascular'])}, Pollution→Resp={len(data['pollution_respiratory'])}, Alcohol→Cirrhosis={len(data['alcohol_cirrhosis'])}")
    
    return data

def insert_fact_data(cursor, fact_table, columns, data):
    """Insert data into fact table."""
    if not data:
        print(f"    No data to insert into {fact_table}")
        return 0
    
    print(f"    Resolving dimensions for {len(data)} rows...")
    
    # Resolve dimension IDs
    final_data = []
    failed_count = 0
    for i, row in enumerate(data):
        if len(row) != 6:
            print(f"      ERROR: Row {i} has {len(row)} values instead of 6: {row}")
            failed_count += 1
            continue
        country_code, sex_code, age_code, year, col1, col2 = row
        
        country_id = get_dimension_id(cursor, 'dim_country', 'country_code', country_code)
        sex_id = get_dimension_id(cursor, 'dim_sex', 'sex_code', sex_code)
        age_group_id = get_dimension_id(cursor, 'dim_age_group', 'age_group_code', age_code)
        year_id = get_dimension_id(cursor, 'dim_year', 'year', int(year))
        
        if not all([country_id, sex_id, age_group_id, year_id]):
            failed_count += 1
            if failed_count <= 3:  # Show first 3 failures
                print(f"      FAILED row {i}: country={country_code}→{country_id}, sex={sex_code}→{sex_id}, age={age_code}→{age_group_id}, year={year}→{year_id}")
            continue
        
        final_data.append((country_id, sex_id, age_group_id, year_id, col1, col2))
    
    if failed_count > 0:
        print(f"      Total failed: {failed_count} rows")
    
    if not final_data:
        print(f"    No valid data after dimension resolution for {fact_table}")
        return 0
    
    # Bulk insert
    placeholders = ','.join(['%s'] * len(columns))
    insert_query = f"INSERT INTO {fact_table} ({','.join(columns)}) VALUES ({placeholders})"
    
    cursor.executemany(insert_query, final_data)
    print(f"    Inserted {len(final_data)} rows into {fact_table}")
    return len(final_data)

def main():
    print("="*80)
    print("EXTRACTING RISK→DISEASE RELATIONSHIPS FROM ALL 4 COUNTRIES")
    print("="*80)
    
    conn = psycopg2.connect(**PG_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Collect data from all 4 countries
        all_data = {
            'smoking_lung_cancer': [],
            'bmi_cardiovascular': [],
            'pollution_respiratory': [],
            'alcohol_cirrhosis': []
        }
        
        # 1. USA - fact_disease_risk (has attributable deaths!)
        print("\n[1/4] USA - Direct risk→disease attribution")
        with open(SQL_FILES['USA'], 'r', encoding='utf-8', errors='ignore') as f:
            usa_data = extract_usa_risk_disease(cursor, f.read())
            for key in all_data.keys():
                all_data[key].extend(usa_data[key])
        
        # 2. Germany - Join lm_* with dm_* tables
        print("\n[2/4] Germany - Correlation approach")
        with open(SQL_FILES['DEU'], 'r', encoding='utf-8', errors='ignore') as f:
            deu_data = extract_germany_risk_disease(cursor, f.read())
            for key in all_data.keys():
                all_data[key].extend(deu_data[key])
        
        # 3. Sweden - disease_data and faktor_data tables
        print("\n[3/4] Sweden - Health registry data")
        with open(SQL_FILES['SWE'], 'r', encoding='utf-8', errors='ignore') as f:
            swe_data = extract_sweden_risk_disease(cursor, f.read())
            for key in all_data.keys():
                all_data[key].extend(swe_data[key])
        
        # 4. Switzerland - PostgreSQL lm_* and dm_* tables
        print("\n[4/4] Switzerland - PostgreSQL tables")
        che_data = extract_switzerland_risk_disease(cursor)
        for key in all_data.keys():
            all_data[key].extend(che_data[key])
        
        # Insert into fact tables
        print("\n" + "="*80)
        print("INSERTING INTO FACT TABLES")
        print("="*80)
        
        total = 0
        
        print("\n[1/4] fact_smoking_lung_cancer")
        total += insert_fact_data(
            cursor, 'fact_smoking_lung_cancer',
            ['country_id', 'sex_id', 'age_group_id', 'year_id', 
             'lung_cancer_deaths', 'attributable_deaths'],
            all_data['smoking_lung_cancer']
        )
        
        print("\n[2/4] fact_bmi_cardiovascular")
        total += insert_fact_data(
            cursor, 'fact_bmi_cardiovascular',
            ['country_id', 'sex_id', 'age_group_id', 'year_id',
             'cvd_deaths', 'attributable_deaths'],
            all_data['bmi_cardiovascular']
        )
        
        print("\n[3/4] fact_pollution_respiratory")
        total += insert_fact_data(
            cursor, 'fact_pollution_respiratory',
            ['country_id', 'sex_id', 'age_group_id', 'year_id',
             'respiratory_deaths', 'attributable_deaths'],
            all_data['pollution_respiratory']
        )
        
        print("\n[4/4] fact_alcohol_cirrhosis")
        total += insert_fact_data(
            cursor, 'fact_alcohol_cirrhosis',
            ['country_id', 'sex_id', 'age_group_id', 'year_id',
             'cirrhosis_deaths', 'attributable_deaths'],
            all_data['alcohol_cirrhosis']
        )
        
        conn.commit()
        
        print("\n" + "="*80)
        print(f"✅ SUCCESS! Inserted {total} total rows across 4 RISK→DISEASE fact tables")
        print(f"✅ Each fact table contains data from ALL 4 countries (CHE, DEU, NOR, USA)")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    main()

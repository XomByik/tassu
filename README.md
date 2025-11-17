# TASSU

Analýza vzťahov medzi rizikovými faktormi a chorobami vo 4 krajinách (2013-2023).

## 📊 Prehľad

Projekt obsahuje **PostgreSQL data warehouse** so **star schémou** pre analýzu 4 merateľných faktov (úmrtia na choroby pripisované rizikovým faktorom):

1. **Smoking → Lung Cancer** (Fajčenie → Rakovina pľúc)
2. **High BMI → Cardiovascular Disease** (Obezita → Srdcové choroby)
3. **Air Pollution → Respiratory Disease** (Znečistenie → Respiračné choroby)
4. **Alcohol → Liver Cirrhosis** (Alkohol → Cirhóza pečene)

### Krajiny a obdobie:
- 🇨🇭 **Švajčiarsko** (CHE): 2013-2023 (11 rokov)
- 🇩🇪 **Nemecko** (DEU): 2013-2020 (8 rokov)
- 🇸🇪 **Švédsko** (SWE): 2013-2023 (11 rokov)
- 🇺🇸 **USA**: 2014-2023 (10 rokov)

**Celkom: 656 záznamov** (164 na každú fact tabuľku)

---

## 📁 Štruktúra Projektu

```
tassu/
├── docker-compose.yml           # Orchestrácia 5 kontajnerov (4 DB + ETL)
├── Dockerfile                   # Python ETL kontajner
├── requirements.txt             # Python závislosti
├── extract_risk_disease.py      # Hlavný ETL skript
├── run_etl.sh                   # Bash skript (ETL + zobrazenie výsledkov)
├── verify_2013_2023.sql        # Verifikačný query
├── README.md                    # Táto dokumentácia
├── VALIDATION_REPORT.md         # Validácia proti CDC/WHO/IHME
├── init/
│   └── schema.sql              # Star schema (dimension + fact tables)
├── databazy_ine_krajiny/
│   ├── usa.sql                 # USA source data
│   ├── germany.sql             # Nemecko source data
│   └── sweden.sql              # Švédsko source data (Norway → Sweden)
└── data_csv/
    ├── IHME-GBD_2023_DATA-94d9786b-1.csv    # Švajčiarsko smoking→LC
    └── IHME-GBD_2023_DATA-cea2d4bb-1.csv    # Švajčiarsko ostatné páry
```

---
```

## 🚀 Rýchly Štart

### 1. Klonovanie projektu
```bash
git clone <repository-url>
cd tassu
```

### 2. Spustenie celého projektu (jeden príkaz!)
```bash
docker-compose up
```

**Čo sa automaticky vykoná:**
- ✅ Spustia sa 4 source databázy (USA, Germany, Sweden) + data warehouse
- ✅ Vytvorí sa star schema (4 dimenzie + 4 fact tabuľky)
- ✅ Spustí sa Python ETL skript (extrakcia z 4 krajín)
- ✅ Načíta sa 656 záznamov do fact tabuliek
- ✅ **Automaticky sa zobrazia výsledky pre všetky 4 páry riziko→choroba**

**Očakávaný výstup:**
```
📊 Displaying results for all 4 RISK→DISEASE fact tables:
============================================================
 country_name  | year | smoking_lc | bmi_cvd | pollution_resp | alcohol_cirr
---------------+------+------------+---------+----------------+--------------
 Germany       | 2013 |      29397 |   62996 |          17214 |         9957
 Germany       | 2014 |      28935 |   58026 |          15730 |         9421
 ...
 United States | 2023 |      93577 |  131235 |          19020 |        26996
(40 rows)

✅ All done! Total records by table:
 total_records |         table_name
---------------+----------------------------
           164 | fact_smoking_lung_cancer
           164 | fact_bmi_cardiovascular
           164 | fact_pollution_respiratory
           164 | fact_alcohol_cirrhosis
           656 | TOTAL
```

**Poznámka:** Prvé spustenie trvá ~60-90 sekúnd (inicializácia databáz + ETL). Netreba inštalovať Python ani závislosti lokálne - všetko beží v Docker kontajneroch!

### Pozadie vs Foreground
```bash
# Foreground (vidíš priebeh):
docker-compose up

# Background (na pozadí):
docker-compose up -d
docker logs -f tassu_etl  # Zobraz ETL progress
```

---

## 💻 Manuálne SQL Dotazy

Po spustení môžeš priamo dotazovať warehouse:

```bash
docker exec -it tassu_postgres psql -U tassu_user -d tassu_db
```

**V psql konzole:**
```sql
-- Krajiny
SELECT * FROM dim_country;

-- Počet záznamov
SELECT COUNT(*) FROM fact_smoking_lung_cancer;

-- Trend pre USA
SELECT y.year, 
       ROUND(SUM(f.lung_cancer_deaths), 0) as lc_deaths
FROM fact_smoking_lung_cancer f
JOIN dim_country c ON f.country_id = c.country_id
JOIN dim_year y ON f.year_id = y.year_id
WHERE c.country_code = 'USA'
GROUP BY y.year
ORDER BY y.year;

-- Exit
\q
```

---

## 🗄️ Star Schema - Data Warehouse

### Dimension Tables (Dimenzie)

#### `dim_country` - Krajiny
```sql
country_id | country_code | country_name
-----------|--------------|---------------
1          | CHE          | Switzerland
2          | DEU          | Germany
3          | SWE          | Sweden
4          | USA          | United States
```

#### `dim_sex` - Pohlavie
```sql
sex_id | sex_code | sex_name
-------|----------|----------
1      | M        | Male
2      | F        | Female
3      | B        | Both
```

#### `dim_age_group` - Vekové skupiny (WHO štandard)
```sql
age_group_id | age_group_code | age_group_name | age_from | age_to
-------------|----------------|----------------|----------|--------
1            | 0-14           | 0-14 years     | 0        | 14
2            | 15-49          | 15-49 years    | 15       | 49
3            | 50-69          | 50-69 years    | 50       | 69
4            | 70+            | 70+ years      | 70       | NULL
5            | ALL            | All ages       | 0        | NULL
```

#### `dim_year` - Roky
```sql
year_id | year
--------|------
1       | 2013
2       | 2014
...     | ...
11      | 2023
```

---

### Fact Tables (Faktové tabuľky)

#### 1. `fact_smoking_lung_cancer` - Fajčenie → Rakovina pľúc
```sql
Stĺpce:
- fact_id (PK)
- country_id (FK) → dim_country
- sex_id (FK) → dim_sex
- age_group_id (FK) → dim_age_group
- year_id (FK) → dim_year
- lung_cancer_deaths (úmrtia na LC)
- attributable_deaths (úmrtia pripisateľné fajčeniu)
```

#### 2. `fact_bmi_cardiovascular` - BMI → Kardiovaskulárne choroby
```sql
Stĺpce:
- fact_id (PK)
- country_id (FK)
- sex_id (FK)
- age_group_id (FK)
- year_id (FK)
- cvd_deaths (CVD úmrtia)
- attributable_deaths (pripisateľné BMI)
```

#### 3. `fact_pollution_respiratory` - Znečistenie → Respiračné choroby
```sql
Stĺpce:
- fact_id (PK)
- country_id (FK)
- sex_id (FK)
- age_group_id (FK)
- year_id (FK)
- respiratory_deaths (celkové úmrtia na respiračné choroby)
- attributable_deaths (pripisateľné znečisteniu)
```

#### 4. `fact_alcohol_cirrhosis` - Alkohol → Cirhóza pečene
```sql
Stĺpce:
- fact_id (PK)
- country_id (FK)
- sex_id (FK)
- age_group_id (FK)
- year_id (FK)
- cirrhosis_deaths (celkové úmrtia na cirhózu)
- attributable_deaths (pripisateľné alkoholu)
```

---

## 📚 Zdroje Dát

### 🇺🇸 USA - usa_health_db (MySQL)
**Súbor:** `databazy_ine_krajiny/usa.sql`

**Tabuľka:** `fact_disease_risk`
- **Zdroje:** IHME Global Burden of Disease (GBD) Study, CDC
- **Obdobie:** 2014-2023
- **Výpočet celkového počtu úmrtí:** Dáta obsahujú priame spojenie medzi rizikom a chorobou
- **Kľúčové polia:**
  - `risk_id`: 99=Smoking, 108=High BMI, 85=Air pollution, 102=Alcohol
  - `cause_id`: 426=Lung cancer, 493=IHD, 498=Stroke, 509=COPD, 521=Cirrhosis
  - `measure_id`: 1=Deaths
  - `metric_id`: 1=Number (nie Rate)

**Príklad extrakcie:**
```python
# Smoking (risk_id=99) → Lung Cancer (cause_id=426)
WHERE risk_id = 99 AND cause_id = 426 AND measure_id = 1 AND metric_id = 1
```

---

### 🇩🇪 Nemecko - deu_health (MySQL)
**Súbor:** `databazy_ine_krajiny/germany.sql`

**Tabuľky:** 
- `dm_lung_cancer_sdr` (SDR - Standardized Death Rate)
- `dm_ischaemic_heart_sdr`
- `dm_chronic_lover_respiratory_sdr`
- `dm_liver_disiasee_sdr`
- `population` (pre konverziu SDR → absolútne čísla)

**Zdroje:** IHME Global Burden of Disease (GBD) Study, WHO
**Obdobie:** 2013-2020
**Výpočet celkového počtu úmrtí:** SDR (Standardized Death Rate per 100k) × populácia = absolútne úmrtia
**Poznámka:** SDR zabezpečuje porovnateľnosť naprieč vekom a populáciami

**Príklad výpočtu:**
```python
# SDR = 25.5 deaths per 100k
# Population = 83 million
# Absolute deaths = (25.5 / 100000) × 83,000,000 = 21,165
```

---

### 🇸🇪 Švédsko - health_sweden_db (PostgreSQL)
**Súbor:** `databazy_ine_krajiny/sweden.sql`

**Tabuľky:**
- `disease_data` (úmrtia podľa chorôb)
- `faktor_data` (rizikové faktory)
- `rok` (mapovanie rokov)

**Zdroje:** Socialstyrelsen (Swedish National Board of Health and Welfare), WHO
**Obdobie:** 2013-2023
**Metodológia:** Národné zdravotné registry - **total deaths** × attributable fraction
**Attributable fractions aplikované:**
- Smoking → LC: **75%** (70-80% všetkých umrtí na LC sú pripisateľné fajčeniu)
- BMI → CVD: **15%** (10-20% všetkých umrtí na CVD sú pripisateľné obezite)
- Pollution → Respiratory: **20%** (15-25% všetkých umrtí na respiračné ochorenia sú pripisateľné PM2.5)
- Alcohol → Cirrhosis: **55%** (50-60% všetkých umrtí na cirhózu sú pripisateľné alkoholu)

**Poznámka:** Švédske dáta obsahujú celkové úmrtia na choroby, nie priamo pripísateľné úmrtia na daný rizokový faktor. Skript aplikuje "attributable fractions" pre správny výpočet.

---

### 🇨🇭 Švajčiarsko - IHME GBD 2023 CSV
**Súbory:** 
- `data_csv/IHME-GBD_2023_DATA-94d9786b-1.csv` (Smoking→LC)
- `data_csv/IHME-GBD_2023_DATA-cea2d4bb-1.csv` (ostatné páry)

**Zdroj:** IHME Global Burden of Disease Study (GDB), WHO
**Obdobie:** 2013-2023
**Výpočet celkového počtu úmrtí:** Dáta obsahujú priame spojenie medzi rizikom a chorobou

**Filter v ETL:**
```python
df = df[
    (df['measure_name'] == 'Deaths') & 
    (df['metric_name'] == 'Number') &
    (df['year'].between(2013, 2023))
]
```

---

## 📊 Príklad Dát (rok 2017)

| Krajina       | Smoking→LC | BMI→CVD  | Pollution→Resp | Alcohol→Cirr | Typ dát |
|---------------|------------|----------|----------------|--------------|---------|
| Germany       | 27,528     | 56,380   | 17,746         | 9,592        | Attributable (AF applied) |
| Sweden        | 8,513      | 5,311    | 1,922          | 539          | Attributable (AF applied) |
| Switzerland   | 2,485      | 2,244    | 190            | 398          | Attributable (IHME) |
| United States | 103,272    | 118,210  | 23,303         | 23,802       | Attributable (IHME) |

---

## 🔍 Kvalita a Kompletnosť Dát

### Stĺpce vo Faktových Tabuľkách

Každá fact tabuľka obsahuje tieto metriky:

#### `fact_smoking_lung_cancer`
- ✅ `lung_cancer_deaths` - **Vždy vyplnené**: Total LC deaths (všetky úmrtia na rakovinu pľúc)
- ✅ `attributable_deaths` - **Vždy vyplnené**: LC deaths spôsobené fajčením (USA/CHE priamo z IHME, DEU/SWE vypočítané cez AF)

#### Podobne pre ostatné fact tabuľky...
- `fact_bmi_cardiovascular`: cvd_deaths (total), attributable_deaths (BMI-caused)
- `fact_pollution_respiratory`: respiratory_deaths (total), attributable_deaths (PM2.5-caused)
- `fact_alcohol_cirrhosis`: cirrhosis_deaths (total), attributable_deaths (alcohol-caused)

### Dostupnosť Attributable Deaths

| Krajina | Smoking→LC | BMI→CVD | Pollution→Resp | Alcohol→Cirr | Zdroj |
|---------|-----------|---------|----------------|--------------|-------|
| 🇺🇸 USA | ✅ Priamo | ✅ Priamo | ✅ Priamo | ✅ Priamo | IHME GBD (fact_disease_risk) |
| 🇨🇭 Švajčiarsko | ✅ Priamo | ✅ Priamo | ✅ Priamo | ✅ Priamo | IHME GBD CSV (rei_id) |
| 🇸🇪 Švédsko | ✅ AF 75% | ✅ AF 15% | ✅ AF 20% | ✅ AF 55% | Total × AF (AF z epidem. štúdie) |
| 🇩🇪 Nemecko | ✅ AF 80% | ✅ AF 15% | ✅ AF 20% | ✅ AF 48% | Total × AF (AF z RKI, GBD 2019) |

**AF (Attributable Fraction)** = Podiel chorôb pripisateľný rizikovému faktoru podľa epidemiologických štúdií.

---

## 📊 Príklad Dát - Detail (Smoking→LC 2017, Female)

```sql
SELECT c.country_code, 
       f.lung_cancer_deaths as total_lc,
       f.attributable_deaths as attr_lc
FROM fact_smoking_lung_cancer f
JOIN dim_country c ON f.country_id = c.country_id
JOIN dim_year y ON f.year_id = y.year_id
WHERE y.year = 2017 AND sex_code = 'F';
```

| Code | Total LC | Attributable LC | Note |
|------|----------|-----------------|------|
| DEU  | 9,201    | 7,361           | AF = 80% (RKI) |
| SWE  | 3,742    | 2,807           | AF = 75% |
| CHE  | 892      | 679             | IHME priamo |
| USA  | 44,056   | 31,124          | IHME priamo |

**Total LC deaths** = Všetky úmrtia na rakovinu pľúc (všetky príčiny)  
**Attributable LC deaths** = Úmrtia na rakovinu pľúc spôsobené fajčením

---

## 💻 SQL Príklady Analýz

### 1. Trend fajčenia → rakovina pľúc v čase
```sql
SELECT 
    c.country_name,
    y.year,
    ROUND(SUM(f.lung_cancer_deaths), 0) as lc_deaths
FROM fact_smoking_lung_cancer f
JOIN dim_country c ON f.country_id = c.country_id
JOIN dim_year y ON f.year_id = y.year_id
GROUP BY c.country_name, y.year
ORDER BY c.country_name, y.year;
```

### 2. Porovnanie rizikových faktorov v jednej krajine
```sql
SELECT 
    y.year,
    SUM(f1.lung_cancer_deaths) as smoking_lc,
    SUM(f2.cvd_deaths) as bmi_cvd,
    SUM(f3.respiratory_deaths) as pollution_resp,
    SUM(f4.cirrhosis_deaths) as alcohol_cirr
FROM dim_year y
LEFT JOIN fact_smoking_lung_cancer f1 
    ON y.year_id = f1.year_id AND f1.country_id = 4 -- USA
LEFT JOIN fact_bmi_cardiovascular f2 
    ON y.year_id = f2.year_id AND f2.country_id = 4
LEFT JOIN fact_pollution_respiratory f3 
    ON y.year_id = f3.year_id AND f3.country_id = 4
LEFT JOIN fact_alcohol_cirrhosis f4 
    ON y.year_id = f4.year_id AND f4.country_id = 4
WHERE y.year BETWEEN 2014 AND 2023
GROUP BY y.year
ORDER BY y.year;
```

### 3. Gender breakdown - fajčenie podľa pohlavia
```sql
SELECT 
    c.country_name,
    s.sex_name,
    SUM(f.lung_cancer_deaths) as total_lc_deaths,
    SUM(f.attributable_deaths) as attributable_lc_deaths
FROM fact_smoking_lung_cancer f
JOIN dim_country c ON f.country_id = c.country_id
JOIN dim_sex s ON f.sex_id = s.sex_id
WHERE s.sex_code IN ('M', 'F')
GROUP BY c.country_name, s.sex_name
ORDER BY c.country_name, total_lc_deaths DESC;
```

### 4. Per-capita analýza
```sql
WITH pop AS (
    SELECT 'USA' as code, 326000000 as population
    UNION ALL SELECT 'DEU', 83000000
    UNION ALL SELECT 'SWE', 10500000
    UNION ALL SELECT 'CHE', 8500000
)
SELECT 
    c.country_name,
    ROUND(SUM(f.lung_cancer_deaths), 0) as lc_deaths,
    ROUND(SUM(f.lung_cancer_deaths) * 1000000.0 / p.population, 0) as deaths_per_million
FROM fact_smoking_lung_cancer f
JOIN dim_country c ON f.country_id = c.country_id
JOIN dim_year y ON f.year_id = y.year_id
JOIN pop p ON c.country_code = p.code
WHERE y.year = 2017
GROUP BY c.country_name, p.population
ORDER BY deaths_per_million DESC;
```

### 5. Attributable vs Total Deaths - porovnanie
```sql
-- Ukázať rozdiel medzi total a attributable deaths
SELECT 
    c.country_name,
    y.year,
    SUM(f.lung_cancer_deaths) as total_lc_deaths,
    SUM(f.attributable_deaths) as attributable_lc_deaths,
    CASE 
        WHEN SUM(f.attributable_deaths) IS NOT NULL 
        THEN ROUND(100.0 * SUM(f.attributable_deaths) / NULLIF(SUM(f.lung_cancer_deaths), 0), 1)
        ELSE NULL
    END as attributable_percentage
FROM fact_smoking_lung_cancer f
JOIN dim_country c ON f.country_id = c.country_id  
JOIN dim_year y ON f.year_id = y.year_id
WHERE y.year = 2017
GROUP BY c.country_name, y.year
ORDER BY c.country_name;
```

**Výstup:**
```
 country_name  | total_lc_deaths | attributable_lc_deaths | attributable_%
---------------+-----------------+------------------------+---------------
 Germany       |      27,528     |         NULL           |     NULL
 Sweden        |      10,940     |         8,513          |     77.8%
 Switzerland   |       2,485     |         2,485          |    100.0%
 United States |     103,272     |       103,272          |    100.0%
```

**Interpretácia:**
- **Nemecko**: Máme len total deaths, attributable nie sú dostupné
- **Švédsko**: Total = 10,940 (všetky LC), Attributable = 8,513 (77.8% AF aplikované)
- **USA/Švajčiarsko**: IHME priamo dáva attributable, total deaths nie sú v databáze

---

## 🛠️ Technológie

- **PostgreSQL 15** - Data warehouse
- **MySQL 8.0** - Source databázy (USA, Nemecko, Švédsko)
- **Python 3.11** - ETL skripty (v Docker kontajneri)
- **pandas** - CSV processing (Švajčiarsko IHME dáta)
- **psycopg2** - PostgreSQL connector
- **mysql-connector-python** - MySQL connector
- **Docker & Docker Compose** - Kompletná kontajnerizácia (žiadna lokálna inštalácia!)

---

## ✅ Validácia Dát

Všetky dáta boli overené proti oficiálnym zdrojom:
- **CDC** (USA Centers for Disease Control)
- **WHO** (World Health Organization)
- **IHME GBD** (Institute for Health Metrics and Evaluation - Global Burden of Disease)
- **RKI** (Robert Koch Institut - Nemecko)
- **Socialstyrelsen** (Švédsko)
- **BAG/FOPH** (Swiss Federal Office of Public Health)

Detaily: [VALIDATION_REPORT.md](VALIDATION_REPORT.md)

### Kľúčové overenia (rok 2017):
✅ **USA Smoking→LC**: 103k (CDC: ~100-110k attributable)  
✅ **USA Alcohol→Cirrhosis**: 24k (CDC: ~23-26k attributable, 50-60% z total 45k)  
✅ **Germany Smoking→LC**: 28k (RKI: ~25-30k estimate)  
✅ **Switzerland Total Smoking Deaths**: 2.5k LC + ostatné = ~9.5k total (BAG: 9.5k validated)  

---

## 🔍 Dôležité Poznámky

### Attributable vs Total Deaths
**Attributable deaths** = Úmrtia ktoré by **nenastali**, keby rizikový faktor neexistoval.

**Príklad:**
- Total lung cancer deaths USA 2017: **~142,000**
- Smoking-attributable LC deaths: **~103,000** (73%)
- Non-smoking LC (radon, genetics, etc.): **~39,000** (27%)

### Metodologické rozdiely:
- **USA + Švajčiarsko**: Priame IHME GBD attributable estimates
- **Nemecko**: SDR rates × population conversion
- **Švédsko**: Total disease deaths × attributable fractions (75%, 15%, 20%, 55%)

---

## 🧪 Testovanie a Vývoj

### Rýchle testovanie po clone:
```bash
git clone <repository-url>
cd tassu
docker-compose up  # Pozri automatický výstup s dátami
```

### Manuálne SQL dotazy:
```bash
docker exec -it tassu_postgres psql -U tassu_user -d tassu_db

# V psql:
\dt                              # Zoznam tabuliek
SELECT * FROM dim_country;       # Krajiny
SELECT COUNT(*) FROM fact_smoking_lung_cancer;  # Počet záznamov
```

### Re-spustenie ETL (po zmenách):
```bash
# Vyčistenie a opätovné načítanie dát
docker exec -it tassu_postgres psql -U tassu_user -d tassu_db -c "TRUNCATE fact_smoking_lung_cancer, fact_bmi_cardiovascular, fact_pollution_respiratory, fact_alcohol_cirrhosis RESTART IDENTITY CASCADE;"

# Spustenie len ETL kontajnera
docker-compose up etl
```

**Očakávaný výsledok:**
- 4 dimension tables (country, sex, age_group, year)
- 4 fact tables (656 total rows, 164 per table)
- Automatické zobrazenie 40 riadkov (všetky krajiny × roky)

---

## 📞 Ďalšie Informácie

- **Data Model:** Star schema s 4 dimension tables + 4 fact tables
- **Granularita:** Country × Sex × Age Group × Year
- **Metriky:** Attributable deaths (kauzálne pripisateľné úmrtia)
- **Časové pokrytie:** 2013-2023 (rôzne podľa krajiny)
- **Update frequency:** Statické dáta (no refresh mechanism)

**Poznámka:** Projekt slúži na analýzu historických trendov, nie real-time monitoring.

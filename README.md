# Tassu - Swiss Health Database

PostgreSQL databáza pre analýzu WHO zdravotných dát pre Švajčiarsko.

## Rýchly štart

```bash
# 1. Klonuj repozitár
git clone https://github.com/XomByik/tassu.git
cd tassu

# 2. Spusti databázu a automatický import dát
docker-compose up -d

# 3. Sleduj progress importu
docker-compose logs -f python-app
```

**Hotovo!** Po spustení `docker-compose up -d` sa automaticky:
- Vytvorí PostgreSQL databáza
- Vytvoria sa všetky tabuľky
- Importuje sa **25 384 záznamov** z 6 WHO CSV súborov

---

## Štruktúra projektu

```
tassu/
├── docker-compose.yml      # Docker konfigurácia
├── Dockerfile              # Python aplikácia
├── requirements.txt        # Python závislosti
├── import_data.py          # Import skript pre WHO dáta
├── data_csv/               # WHO CSV súbory (6 datasetov)
│   ├── health_indicators_che.csv
│   ├── air_pollution_indicators_che.csv
│   ├── environment_and_health_indicators_che.csv
│   ├── global_information_system_on_alcohol_and_health_indicators_che.csv
│   ├── health_financing_indicators_che.csv
│   └── nutrition_indicators_che.csv
└── init/
    └── 01_create_tables.sql # Databázová schéma
```

---

## Databázová štruktúra

### 1. Demografia

**demograficke_skupiny** (231 záznamov)
- Vekové skupiny: 0-17, 18-34, 35-49, 50-64, 65+, všetky
- Pohlavie: muž, žena, všetky

### 2. Choroby

**kategorie_chorob** → **choroby** → **vyskyt_chorob**

**kategorie_chorob** (7 kategórií):
- Infekčné choroby (HIV, hepatitída, tuberkulóza...)
- Metabolické ochorenia (cukrovka...)
- Neuropsychiatrické poruchy (depresia, alzheimer...)
- Rakoviny
- Respiračné ochorenia (astma, COPD...)
- Zdravie matiek a detí (novorodenecká úmrtnosť...)
- Ostatné ochorenia

**choroby** (562 chorôb) - Konkrétne ochorenia s WHO GHO kódmi

**vyskyt_chorob** (12 818 meraní) - Výskyt chorôb v čase
- Obsahuje `typ_merania`: mortality (úmrtnosť), incidence (výskyt), prevalence (rozšírenosť), cases (počet prípadov)
- Jeden typ choroby môže mať viacero typov meraní

### 3. Životný štýl

**zivotny_styl** → **zivotny_styl_data**

**zivotny_styl** (208 faktorov):
- Alkohol (65 faktorov) - napr. "Heavy episodic drinking", "Alcohol abstainers", "Average daily intake"
- Fajčenie (116 faktorov) - napr. prevalencia, cena cigariet, legislatíva
- Vakcinácia (10 faktorov) - napr. pokrytie MCV1, HepB3, HPV
- Výživa (17 faktorov) - napr. BMI, obezita, anémia, malnutrícia

**zivotny_styl_data** (7 005 meraní)

### 4. Environmentálne faktory

**environmentalne_faktory** (5 285 meraní)
- Znečistenie ovzdušia (PM2.5, PM10, ambient/household air pollution)
- Kvalita vzduchu

### 5. Financovanie

**financovanie_zdravotnictva** (276 meraní)
- Výdavky na zdravotníctvo (OOP - out-of-pocket, GGHE-D - government, PVT-D - private, CHE - current health expenditure)

---

## Vzťahy medzi tabuľkami

```
kategorie_chorob (1) ──→ (N) choroby (1) ──→ (N) vyskyt_chorob ←── (N) demograficke_skupiny
                                                                            ↑
zivotny_styl (1) ────────────────────→ (N) zivotny_styl_data ──────────────┤
                                                                            │
environmentalne_faktory ────────────────────────────────────────────────────┤
```

---

## Pripojenie na databázu

### Cez pgAdmin4

- **Host:** `localhost`
- **Port:** `5433`
- **Database:** `tassu_db`
- **User:** `tassu_user`
- **Password:** `tassu_password`

### Cez psql v Docker kontajneri

```bash
docker exec -it tassu_postgres psql -U tassu_user -d tassu_db
```

---

## Docker príkazy

### Základné operácie

```bash
# Spusti všetky služby
docker-compose up -d

# Sleduj logy
docker-compose logs -f

# Sleduj logy PostgreSQL
docker-compose logs -f postgres

# Sleduj logy Python importu
docker-compose logs -f python-app

# Zastav všetky kontajnery
docker-compose down

# Reštartuj služby
docker-compose restart
```

### Vyčistenie a rebuild

```bash
# Zastav a vymaž databázu
docker-compose down -v

# Kompletné vyčistenie (kontajnery, obrazy, volumes)
docker-compose down -v --rmi all --remove-orphans

# Rebuild Python obrazu bez cache
docker-compose build --no-cache python-app

# Reštart databázy a reimport dát
docker-compose down -v && docker-compose up -d
```

### Backup a restore

```bash
# Backup databázy
docker exec tassu_postgres pg_dump -U tassu_user tassu_db > backup_$(date +%Y%m%d).sql

# Restore databázy
cat backup_20241027.sql | docker exec -i tassu_postgres psql -U tassu_user -d tassu_db
```

---

## Import skript

Import skript (`import_data.py`) automaticky:
- Načíta všetky WHO CSV súbory
- Kategorizuje zdravotné indikátory do správnych tabuliek
- Parsuje demografické informácie (vek, pohlavie)
- Importuje dáta do databázy
- Vytvára prepojenia medzi tabuľkami
- Loguje progress a štatistiky

**Kategorizácia dát:**
- **Choroby:** Infekčné choroby, metabolické ochorenia, neuropsychiatrické poruchy, rakoviny, respiračné ochorenia, zdravie matiek a detí
  - Každá choroba môže mať viacero typov meraní: mortality (úmrtnosť), incidence (výskyt), prevalence (rozšírenosť), cases (počet prípadov)
- **Životný štýl:** Alkohol, fajčenie, vakcinácia (preventívne opatrenia), výživa (BMI, anémia, obezita)
- **Environment:** Znečistenie ovzdušia, kvalita vzduchu
- **Financovanie:** Výdavky na zdravotníctvo

---

## Riešenie problémov

### PostgreSQL sa nespustí

```bash
# Skontroluj logy
docker-compose logs postgres

# Reštartuj kontajner
docker-compose restart postgres
```

### Import zlyhá

```bash
# Sleduj import logy
docker-compose logs -f python-app

# Ručne spusti import
docker-compose run --rm python-app python import_data.py
```

### Databáza neobsahuje dáta

```bash
# Reštart databázy a reimport
docker-compose down -v
docker-compose up -d
docker-compose logs -f python-app
```

---

## WHO Dáta - zdroje

Dáta pochádzajú z WHO Global Health Observatory (GHO):
- [WHO Global Health Observatory](https://www.who.int/data/gho)
- [GHO Data Repository](https://www.who.int/data/gho/data/indicators)

CSV súbory pre Švajčiarsko (CHE) obsahujú celkovo **25 384 záznamov** z rokov 2000-2024:
- health_indicators_che.csv: 17 011 záznamov
- air_pollution_indicators_che.csv: 2 517 záznamov
- environment_and_health_indicators_che.csv: 2 768 záznamov
- global_information_system_on_alcohol_and_health_indicators_che.csv: 919 záznamov
- health_financing_indicators_che.csv: 276 záznamov
- nutrition_indicators_che.csv: 1 893 záznamov

---

## Technológie

- **Databáza:** PostgreSQL 15
- **Import:** Python 3.11, pandas, SQLAlchemy
- **Orchestrácia:** Docker, Docker Compose

---

## Licencia

MIT

## Autor

XomByik - [GitHub](https://github.com/XomByik/tassu)

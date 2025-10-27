# Tassu - Swiss Health Database# Tassu - Swiss Health Database



PostgreSQL databáza pre analýzu WHO zdravotných indikátorov pre Švajčiarsko.PostgreSQL databáza pre analýzu WHO zdravotných indikátorov pre Švajčiarsko.



## Štruktúra projektu



```## Štruktúra projektu

tassu/

├── docker-compose.yml      # Docker konfigurácia```

├── Dockerfile              # Python aplikáciatassu/

├── requirements.txt        # Python závislosti├── docker-compose.yml      # Docker konfigurácia

├── import_data.py          # Import skript pre WHO dáta├── Dockerfile              # Python aplikácia

├── data_csv/               # WHO CSV súbory (6 datasetov)├── requirements.txt        # Python závislosti

│   ├── health_indicators_che.csv├── import_data.py          # Import skript pre WHO dáta

│   ├── air_pollution_indicators_che.csv├── data_csv/               # WHO CSV súbory (6 datasetov)

│   ├── environment_and_health_indicators_che.csv│   ├── health_indicators_che.csv

│   ├── global_information_system_on_alcohol_and_health_indicators_che.csv│   ├── air_pollution_indicators_che.csv

│   ├── health_financing_indicators_che.csv│   ├── environment_and_health_indicators_che.csv

│   └── nutrition_indicators_che.csv│   ├── global_information_system_on_alcohol_and_health_indicators_che.csv

└── init/│   ├── health_financing_indicators_che.csv

    └── 01_create_tables.sql # Databázová schéma│   └── nutrition_indicators_che.csv

```└── init/

    └── 01_create_tables.sql # Databázová schéma

## Rýchly štart```



```bash

# 1. Klonuj repozitár

git clone https://github.com/XomByik/tassu.git## Databázová štruktúra### 1. Stiahnutie projektu do WSL

cd tassu



# 2. Spusti databázu a automatický import dát

docker-compose up -d### Hlavné tabuľky:```bash



# 3. Sleduj progress importu- **kategorie_indikatorov** - Kategórie zdravotných indikátorov (choroby, rizikové faktory, environmentálne faktory...)# Klonuj repozitár

docker-compose logs -f python-app

- **zdravotne_indikatory** - WHO GHO indikátory (úmrtnosť, fajčenie, obezita, vakcinácia...)git clone https://github.com/XomByik/tassu.git

# 4. Pripoj sa na databázu

docker exec -it tassu_postgres psql -U tassu_user -d tassu_db- **demograficke_skupiny** - Vekové skupiny, pohlavie, dimension types

```

- **merania_indikatorov** - Hlavná tabuľka s nameranými hodnotami# Prejdi do priečinka

**Hotovo!** Po `docker-compose up -d` sa automaticky:

- Vytvorí PostgreSQL databázacd tassu

- Vytvoria sa všetky tabuľky

- Importujú sa WHO dáta zo všetkých CSV súborov### Špecializované tabuľky:```



## Databázová štruktúra- **environmentalne_faktory** - Znečistenie ovzdušia, kvalita vzduchu



### Hlavné tabuľky- **zdravotne_financovanie** - Výdavky na zdravotníctvo, financovanie### 2. Spustenie



**kategorie_indikatorov**- **vyzivovacie_indikatory** - BMI, anémia, malnutrícia

- Kategórie zdravotných indikátorov (úmrtnosť, choroby, rizikové faktory, environmentálne faktory...)

- 15 kategórií (napr. "Úmrtnosť", "Alkohol", "Fajčenie a tabak", "Obezita")- **alkoholove_indikatory** - Spotreba alkoholu, úmrtnosť na alkohol```bash



**zdravotne_indikatory**# Spusti všetky služby (PostgreSQL + Python)

- WHO GHO indikátory s unikátnymi kódmi

- 760 indikátorov (napr. "WHOSIS_000001" - Life expectancy at birth)## Inštalácia a spusteniedocker-compose up -d

- Prepojenie: `kategoria_id` → `kategorie_indikatorov.id`



**demograficke_skupiny**

- Vekové skupiny, pohlavie, dimension types### 1. Stiahnutie projektu do WSL# Sleduj logy

- 231 demografických skupín (napr. "0-17 rokov, muži", "65+ rokov, ženy")

docker-compose logs -f

**merania_indikatorov**

- Hlavná tabuľka s nameranými hodnotami v čase```bash```

- 10,976 záznamov meraní

- Prepojenia:# Klonuj repozitár

  - `indikator_id` → `zdravotne_indikatory.id`

  - `demograficka_skupina_id` → `demograficke_skupiny.id`git clone https://github.com/XomByik/tassu.git### 3. Zastavenie

- Obsahuje: hodnota, rok, dolná/horná hranica, krajina, región



### Špecializované tabuľky

# Prejdi do priečinka```bash

**environmentalne_faktory**

- Znečistenie ovzdušia, kvalita vzduchucd tassu# Zastav všetky kontajnery

- 1,063 záznamov

- Prepojenie: `indikator_id` → `zdravotne_indikatory.id````docker-compose down



**zdravotne_financovanie**

- Výdavky na zdravotníctvo, financovanie (OOP, GGHE-D, PVT-D, CHE)

- 276 záznamov### 2. Spustenie databázy# Zastav a vymaž volumes (databáza sa vymaže!)

- Prepojenie: `indikator_id` → `zdravotne_indikatory.id`

docker-compose down -v

**vyzivovacie_indikatory**

- BMI, anémia, malnutrícia```bash```

- 1,203 záznamov

- Prepojenia:# Spusti PostgreSQL databázu

  - `indikator_id` → `zdravotne_indikatory.id`

  - `demograficka_skupina_id` → `demograficke_skupiny.id`docker-compose up -d postgres### 4. Odstránenie obrazov



**alkoholove_indikatory**

- Spotreba alkoholu, úmrtnosť na alkohol, typy alkoholu (víno, pivo, liehoviny)

- 907 záznamov# Sleduj logy```bash

- Prepojenia:

  - `indikator_id` → `zdravotne_indikatory.id`docker-compose logs -f postgres# Odstráň všetky obrazy projektu

  - `demograficka_skupina_id` → `demograficke_skupiny.id`

```docker-compose down --rmi all

### Vzťahy medzi tabuľkami



```

kategorie_indikatorov (1) ──→ (N) zdravotne_indikatory### 3. Stiahnutie WHO dát# Alebo odstráň len lokálne zostavené obrazy

                                        ↓

                                        │ (1)docker-compose down --rmi local

                                        │

                                        ├──→ (N) merania_indikatorov ←── (N) demograficke_skupinyStiahni WHO dáta pre Švajčiarsko z [WHO GHO Data Repository](https://www.who.int/data/gho):

                                        │

                                        ├──→ (N) environmentalne_faktory ←── (N) demograficke_skupiny# Kompletné vyčistenie (kontajnery, obrazy, volumes, siete)

                                        │

                                        ├──→ (N) zdravotne_financovaniePotrebné CSV súbory (umiestnite do root priečinka projektu):docker-compose down -v --rmi all --remove-orphans

                                        │

                                        ├──→ (N) vyzivovacie_indikatory ←── (N) demograficke_skupiny- `health_indicators_che.csv````

                                        │

                                        └──→ (N) alkoholove_indikatory ←── (N) demograficke_skupiny- `air_pollution_indicators_che.csv`

```

- `environment_and_health_indicators_che.csv`## Pripojenie na databázu

## Pripojenie na databázu

- `global_information_system_on_alcohol_and_health_indicators_che.csv`

**PostgreSQL údaje:**

- Host: `localhost`- `health_financing_indicators_che.csv`### Cez pgAdmin4:

- Port: `5433`

- Database: `tassu_db`- `nutrition_indicators_che.csv`- **Host:** `localhost`

- User: `tassu_user`

- Password: `tassu_password`- **Port:** `5433`



**Pripojenie cez psql:**### 4. Import dát do databázy- **Database:** `tassu_db`

```bash

docker exec -it tassu_postgres psql -U tassu_user -d tassu_db- **User:** `tassu_user`

```

```bash- **Password:** `tassu_password`

**Pripojenie cez pgAdmin4:**

- Použite vyššie uvedené údaje# Nainštaluj Python závislosti

- URL: `postgresql://tassu_user:tassu_password@localhost:5433/tassu_db`

pip install -r requirements.txt### Cez psql v Docker kontajneri:

## Užitočné príkazy

```bash

```bash

# Zobraz bežiace kontajnery# Spusti import skriptdocker exec -it tassu_postgres psql -U tassu_user -d tassu_db

docker-compose ps

python import_data.py```

# Sleduj logy

docker-compose logs -f```



# Zastav všetky služby## Užitočné príkazy

docker-compose down

Alebo cez Docker:

# Reštart databázy a reimport dát

docker-compose down -v```bash

docker-compose up -d

```bash# Zobraz bežiace kontajnery

# Backup databázy

docker exec tassu_postgres pg_dump -U tassu_user tassu_db > backup.sql# Zostavy Python aplikáciudocker-compose ps



# Restore databázydocker-compose build python-app

cat backup.sql | docker exec -i tassu_postgres psql -U tassu_user -d tassu_db

```# Zobraz logy PostgreSQL



## Riešenie problémov# Spusti import v kontajneridocker-compose logs postgres



**Databáza sa nespúšťa:**docker-compose run --rm python-app python import_data.py

```bash

docker-compose logs postgres```# Zobraz logy Python aplikácie

docker-compose restart postgres

```docker-compose logs python-app



**Import zlyháva:**### 5. Zastavenie a vyčistenie

```bash

# Skontroluj logy# Reštartuj služby

docker-compose logs python-app

```bashdocker-compose restart

# Ručne spusti import

docker-compose run --rm python-app python import_data.py# Zastav všetky kontajnery

```

docker-compose down# Rebuild Python obrazu bez cache

**Vyčistenie a nový štart:**

```bashdocker-compose build --no-cache python-app

docker-compose down -v --rmi all

docker-compose up -d# Zastav a vymaž volumes (databáza sa vymaže!)

```

docker-compose down -v# Spusti len PostgreSQL (bez Python)

## WHO Dáta

docker-compose up -d postgres

Dáta pochádzajú z WHO Global Health Observatory (GHO):

- [WHO GHO Data Repository](https://www.who.int/data/gho/data/indicators)# Kompletné vyčistenie```

- CSV súbory pre Švajčiarsko (CHE)

- Celkovo ~25,000 záznamov z rokov 2000-2024docker-compose down -v --rmi all --remove-orphans



## Autor```## Databázová štruktúra



XomByik - [GitHub](https://github.com/XomByik/tassu)


## Pripojenie na databázu- **kategorie_chorob** - Kategórie civilizačných chorôb

- **choroby** - Konkrétne choroby s ICD-10 kódmi

### Cez pgAdmin4:- **demograficke_skupiny** - Vekové skupiny a pohlavie

- **Host:** `localhost`- **vyskyt_chorob** - Hlavná tabuľka s výskytom chorôb

- **Port:** `5433`- **zivotny_styl_faktory** - Faktory životného štýlu (alkohol, fajčenie, šport...)

- **Database:** `tassu_db`- **zivotny_styl_data** - Dáta o životnom štýle populácie

- **User:** `tassu_user`- **ekonomicke_indikatory** - Ekonomické ukazovatele (HDP, platy...)

- **Password:** `tassu_password`- **environmentalne_faktory** - Environmentálne faktory (počasie, kvalita vzduchu...)


### Cez psql v Docker kontajneri:
```bash
docker exec -it tassu_postgres psql -U tassu_user -d tassu_db
```

## Príklady SQL dotazov

### 1. Základné štatistiky
```sql
-- Počty záznamov v jednotlivých tabuľkách
SELECT 
    (SELECT COUNT(*) FROM kategorie_indikatorov) as kategorie,
    (SELECT COUNT(*) FROM zdravotne_indikatory) as indikatory,
    (SELECT COUNT(*) FROM demograficke_skupiny) as demografie,
    (SELECT COUNT(*) FROM merania_indikatorov) as merania,
    (SELECT COUNT(*) FROM environmentalne_faktory) as environmentalne,
    (SELECT COUNT(*) FROM zdravotne_financovanie) as financovanie,
    (SELECT COUNT(*) FROM vyzivovacie_indikatory) as vyzivovacie,
    (SELECT COUNT(*) FROM alkoholove_indikatory) as alkoholove;
```

### 2. Top kategórie podľa počtu meraní
```sql
SELECT 
    k.nazov, 
    k.typ, 
    COUNT(m.id) as pocet_merani
FROM kategorie_indikatorov k
JOIN zdravotne_indikatory i ON i.kategoria_id = k.id
LEFT JOIN merania_indikatorov m ON m.indikator_id = i.id
GROUP BY k.id, k.nazov, k.typ
ORDER BY pocet_merani DESC
LIMIT 10;
```

### 3. Časový vývoj úmrtnosti
```sql
SELECT 
    zi.nazov,
    mi.rok,
    mi.hodnota_cislo,
    ds.vekova_skupina,
    ds.pohlavie
FROM merania_indikatorov mi
JOIN zdravotne_indikatory zi ON mi.indikator_id = zi.id
JOIN demograficke_skupiny ds ON mi.demograficka_skupina_id = ds.id
JOIN kategorie_indikatorov k ON zi.kategoria_id = k.id
WHERE k.nazov LIKE '%mortali%'
ORDER BY mi.rok DESC, zi.nazov
LIMIT 20;
```

### 4. Environmentálne faktory
```sql
SELECT 
    zi.nazov as indikator,
    ef.rok,
    ef.hodnota_cislo,
    ef.typ_znecistenia
FROM environmentalne_faktory ef
JOIN zdravotne_indikatory zi ON ef.indikator_id = zi.id
WHERE ef.rok >= 2015
ORDER BY ef.rok DESC
LIMIT 20;
```

### 5. Analýza výživy a obezity
```sql
SELECT 
    zi.nazov,
    vi.rok,
    vi.hodnota_cislo,
    vi.typ_merania,
    ds.vekova_skupina,
    ds.pohlavie
FROM vyzivovacie_indikatory vi
JOIN zdravotne_indikatory zi ON vi.indikator_id = zi.id
JOIN demograficke_skupiny ds ON vi.demograficka_skupina_id = ds.id
WHERE zi.nazov LIKE '%BMI%' OR zi.nazov LIKE '%obesity%'
ORDER BY vi.rok DESC, ds.vekova_skupina;
```

## Užitočné príkazy

```bash
# Zobraz bežiace kontajnery
docker-compose ps

# Zobraz logy PostgreSQL
docker-compose logs postgres

# Zobraz logy Python aplikácie
docker-compose logs python-app

# Reštartuj služby
docker-compose restart

# Rebuild Python obrazu bez cache
docker-compose build --no-cache python-app

# Spusti len PostgreSQL (bez Python)
docker-compose up -d postgres

# Backup databázy
docker exec tassu_postgres pg_dump -U tassu_user tassu_db > backup_$(date +%Y%m%d).sql

# Restore databázy
cat backup_20241027.sql | docker exec -i tassu_postgres psql -U tassu_user -d tassu_db
```

## Import skript (import_data.py)

Import skript automaticky:
- ✅ Kategorizuje WHO indikátory podľa typu (choroby, rizikové faktory, environmentálne...)
- ✅ Parsuje demografické informácie (vek, pohlavie)
- ✅ Importuje dáta do správnych tabuliek podľa typu
- ✅ Vytvára prepojenia medzi tabuľkami
- ✅ Loguje progress a štatistiky

### Konfigurácia v import_data.py:
```python
DB_USER = 'tassu_user'
DB_PASSWORD = 'tassu_password'
DB_HOST = 'localhost'
DB_PORT = '5433'
DB_NAME = 'tassu_db'
```

## Riešenie problémov

### PostgreSQL sa nespustí
```bash
# Skontroluj logy
docker-compose logs postgres

# Reštartuj kontajner
docker-compose restart postgres
```

### Import zlyhá s chybou pripojenia
```bash
# Skontroluj či PostgreSQL beží
docker-compose ps

# Otestuj pripojenie
docker exec -it tassu_postgres psql -U tassu_user -d tassu_db -c "SELECT 1;"
```

### Python chyby pri importe
```bash
# Nainštaluj závislosti
pip install -r requirements.txt

# Alebo použij Docker
docker-compose build python-app
docker-compose run --rm python-app python import_data.py
```

## WHO Dáta - zdroje

- [WHO Global Health Observatory (GHO)](https://www.who.int/data/gho)
- [GHO Data Repository](https://www.who.int/data/gho/data/indicators)
- [Athena API](https://www.who.int/data/gho/info/athena-api)

## Licencia

MIT

## Autori

XomByik - Swiss Health Data Analysis Project

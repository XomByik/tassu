# Swiss Health Database (Tassu)# Technológie a systémy spracovania údajov



PostgreSQL databáza pre analýzu WHO zdravotných indikátorov pre Švajčiarsko.PostgreSQL databáza pre analýzu civilizačných chorôb vo Švajčiarsku.



## Štruktúra projektu## Štruktúra projektu



- `docker-compose.yml` - Docker konfigurácia- `docker-compose.yml` - Docker konfigurácia

- `Dockerfile` - Python aplikácia  - `Dockerfile` - Python konfigurácia

- `init/` - SQL skripty pre inicializáciu databázy- `init/` - SQL skripty pre inicializáciu databázy

  - `01_create_tables.sql` - Schéma databázy- `app.py` - Python aplikácia

- `app.py` - Python aplikácia- `requirements.txt` - Python závislosti

- `import_data.py` - Import skript pre WHO dáta

- `requirements.txt` - Python závislosti## Inštalácia a spustenie



## Databázová štruktúra### 1. Stiahnutie projektu do WSL



### Hlavné tabuľky:```bash

- **kategorie_indikatorov** - Kategórie zdravotných indikátorov (choroby, rizikové faktory, environmentálne faktory...)# Klonuj repozitár

- **zdravotne_indikatory** - WHO GHO indikátory (úmrtnosť, fajčenie, obezita, vakcinácia...)git clone https://github.com/XomByik/tassu.git

- **demograficke_skupiny** - Vekové skupiny, pohlavie, dimension types

- **merania_indikatorov** - Hlavná tabuľka s nameranými hodnotami# Prejdi do priečinka

cd tassu

### Špecializované tabuľky:```

- **environmentalne_faktory** - Znečistenie ovzdušia, kvalita vzduchu

- **zdravotne_financovanie** - Výdavky na zdravotníctvo, financovanie### 2. Spustenie

- **vyzivovacie_indikatory** - BMI, anémia, malnutrícia

- **alkoholove_indikatory** - Spotreba alkoholu, úmrtnosť na alkohol```bash

# Spusti všetky služby (PostgreSQL + Python)

## Inštalácia a spusteniedocker-compose up -d



### 1. Stiahnutie projektu do WSL# Sleduj logy

docker-compose logs -f

```bash```

# Klonuj repozitár

git clone https://github.com/XomByik/tassu.git### 3. Zastavenie



# Prejdi do priečinka```bash

cd tassu# Zastav všetky kontajnery

```docker-compose down



### 2. Spustenie databázy# Zastav a vymaž volumes (databáza sa vymaže!)

docker-compose down -v

```bash```

# Spusti PostgreSQL databázu

docker-compose up -d postgres### 4. Odstránenie obrazov



# Sleduj logy```bash

docker-compose logs -f postgres# Odstráň všetky obrazy projektu

```docker-compose down --rmi all



### 3. Stiahnutie WHO dát# Alebo odstráň len lokálne zostavené obrazy

docker-compose down --rmi local

Stiahni WHO dáta pre Švajčiarsko z [WHO GHO Data Repository](https://www.who.int/data/gho):

# Kompletné vyčistenie (kontajnery, obrazy, volumes, siete)

Potrebné CSV súbory (umiestnite do root priečinka projektu):docker-compose down -v --rmi all --remove-orphans

- `health_indicators_che.csv````

- `air_pollution_indicators_che.csv`

- `environment_and_health_indicators_che.csv`## Pripojenie na databázu

- `global_information_system_on_alcohol_and_health_indicators_che.csv`

- `health_financing_indicators_che.csv`### Cez pgAdmin4:

- `nutrition_indicators_che.csv`- **Host:** `localhost`

- **Port:** `5433`

### 4. Import dát do databázy- **Database:** `tassu_db`

- **User:** `tassu_user`

```bash- **Password:** `tassu_password`

# Nainštaluj Python závislosti

pip install -r requirements.txt### Cez psql v Docker kontajneri:

```bash

# Spusti import skriptdocker exec -it tassu_postgres psql -U tassu_user -d tassu_db

python import_data.py```

```

## Užitočné príkazy

Alebo cez Docker:

```bash

```bash# Zobraz bežiace kontajnery

# Zostavy Python aplikáciudocker-compose ps

docker-compose build python-app

# Zobraz logy PostgreSQL

# Spusti import v kontajneridocker-compose logs postgres

docker-compose run --rm python-app python import_data.py

```# Zobraz logy Python aplikácie

docker-compose logs python-app

### 5. Zastavenie a vyčistenie

# Reštartuj služby

```bashdocker-compose restart

# Zastav všetky kontajnery

docker-compose down# Rebuild Python obrazu bez cache

docker-compose build --no-cache python-app

# Zastav a vymaž volumes (databáza sa vymaže!)

docker-compose down -v# Spusti len PostgreSQL (bez Python)

docker-compose up -d postgres

# Kompletné vyčistenie```

docker-compose down -v --rmi all --remove-orphans

```## Databázová štruktúra



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

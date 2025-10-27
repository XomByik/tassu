# Tassu - Swiss Health Database

PostgreSQL databáza pre analýzu WHO zdravotných indikátorov pre Švajčiarsko.

## Rýchly štart

```bash
# 1. Klonuj repozitár
git clone https://github.com/XomByik/tassu.git
cd tassu

# 2. Spusti databázu a automatický import dát
docker-compose up -d

# 3. Sleduj progress importu
docker-compose logs -f python-app

# 4. Pripoj sa na databázu
docker exec -it tassu_postgres psql -U tassu_user -d tassu_db
```

**Hotovo!** Po `docker-compose up -d` sa automaticky:
- Vytvorí PostgreSQL databáza
- Vytvoria sa všetky tabuľky
- Importujú sa WHO dáta zo všetkých CSV súborov

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

### Hlavné tabuľky

| Tabuľka | Popis | Počet záznamov |
|---------|-------|----------------|
| **kategorie_indikatorov** | Kategórie zdravotných indikátorov | 15 |
| **zdravotne_indikatory** | WHO GHO indikátory (úmrtnosť, fajčenie, obezita...) | 760 |
| **demograficke_skupiny** | Vekové skupiny, pohlavie, dimension types | 231 |
| **merania_indikatorov** | Hlavná tabuľka s nameranými hodnotami | 10 976 |

### Špecializované tabuľky

| Tabuľka | Popis | Počet záznamov |
|---------|-------|----------------|
| **environmentalne_faktory** | Znečistenie ovzdušia, kvalita vzduchu | 1 063 |
| **zdravotne_financovanie** | Výdavky na zdravotníctvo (OOP, GGHE-D, CHE) | 276 |
| **vyzivovacie_indikatory** | BMI, anémia, malnutrícia | 1 203 |
| **alkoholove_indikatory** | Spotreba alkoholu, úmrtnosť | 907 |

### Vzťahy medzi tabuľkami

```
kategorie_indikatorov (1) ──→ (N) zdravotne_indikatory
                                        ↓ (1)
                                        │
                                        ├──→ (N) merania_indikatorov ←── (N) demograficke_skupiny
                                        ├──→ (N) environmentalne_faktory ←── (N) demograficke_skupiny
                                        ├──→ (N) zdravotne_financovanie
                                        ├──→ (N) vyzivovacie_indikatory ←── (N) demograficke_skupiny
                                        └──→ (N) alkoholove_indikatory ←── (N) demograficke_skupiny
```

---

## Pripojenie na databázu

### Cez pgAdmin4

- **Host:** `localhost`
- **Port:** `5433`
- **Database:** `tassu_db`
- **User:** `tassu_user`
- **Password:** `tassu_password`
- **URL:** `postgresql://tassu_user:tassu_password@localhost:5433/tassu_db`

### Cez psql v Docker kontajneri

```bash
docker exec -it tassu_postgres psql -U tassu_user -d tassu_db
```

---

## Príklady SQL dotazov

### 1. Základné štatistiky

```sql
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

---

## Užitočné príkazy

### Základné operácie

```bash
# Zobraz bežiace kontajnery
docker-compose ps

# Sleduj logy
docker-compose logs -f

# Sleduj logy konkrétnej služby
docker-compose logs -f postgres
docker-compose logs -f python-app

# Reštartuj služby
docker-compose restart

# Zastav všetky kontajnery
docker-compose down

# Zastav a vymaž volumes (databáza sa vymaže!)
docker-compose down -v
```

### Správa databázy

```bash
# Backup databázy
docker exec tassu_postgres pg_dump -U tassu_user tassu_db > backup_$(date +%Y%m%d).sql

# Restore databázy
cat backup_20241027.sql | docker exec -i tassu_postgres psql -U tassu_user -d tassu_db
```

### Rebuild a vyčistenie

```bash
# Rebuild Python obrazu bez cache
docker-compose build --no-cache python-app

# Spusti len PostgreSQL (bez Python)
docker-compose up -d postgres

# Kompletné vyčistenie (kontajnery, obrazy, volumes)
docker-compose down -v --rmi all --remove-orphans

# Reštart databázy a reimport dát
docker-compose down -v && docker-compose up -d
```

### Manuálny import

```bash
# Nainštaluj Python závislosti
pip install -r requirements.txt

# Spusti import lokálne
python import_data.py

# Alebo cez Docker
docker-compose run --rm python-app python import_data.py
```

---

## Import skript (import_data.py)

Import skript automaticky:
- Kategorizuje WHO indikátory podľa typu (choroby, rizikové faktory, environmentálne...)
- Parsuje demografické informácie (vek, pohlavie)
- Importuje dáta do správnych tabuliek podľa typu
- Vytvára prepojenia medzi tabuľkami
- Loguje progress a štatistiky

### Konfigurácia

```python
DB_USER = 'tassu_user'
DB_PASSWORD = 'tassu_password'
DB_HOST = 'localhost'
DB_PORT = '5433'
DB_NAME = 'tassu_db'
```

---

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

### Databáza neobsahuje dáta

```bash
# Sleduj import logy
docker-compose logs -f python-app

# Ručne spusti import
docker-compose run --rm python-app python import_data.py
```

---

## WHO Dáta - zdroje

Dáta pochádzajú z WHO Global Health Observatory (GHO):
- [WHO Global Health Observatory](https://www.who.int/data/gho)
- [GHO Data Repository](https://www.who.int/data/gho/data/indicators)
- [Athena API](https://www.who.int/data/gho/info/athena-api)

CSV súbory pre Švajčiarsko (CHE) obsahujú celkovo ~25 000 záznamov z rokov 2000-2024.

---

## Licencia

MIT

## Autor

XomByik - [GitHub](https://github.com/XomByik/tassu)

# Technológie a systémy spracovania údajov

PostgreSQL databáza pre analýzu civilizačných chorôb vo Švajčiarsku.

## Štruktúra projektu

- `docker-compose.yml` - Docker konfigurácia
- `Dockerfile` - Python konfigurácia
- `init/` - SQL skripty pre inicializáciu databázy
- `app.py` - Python aplikácia
- `requirements.txt` - Python závislosti

## Inštalácia a spustenie

### 1. Stiahnutie projektu do WSL

```bash
# Klonuj repozitár
git clone https://github.com/XomByik/tassu.git

# Prejdi do priečinka
cd tassu
```

### 2. Spustenie

```bash
# Spusti všetky služby (PostgreSQL + Python)
docker-compose up -d

# Sleduj logy
docker-compose logs -f
```

### 3. Zastavenie

```bash
# Zastav všetky kontajnery
docker-compose down

# Zastav a vymaž volumes (databáza sa vymaže!)
docker-compose down -v
```

### 4. Odstránenie obrazov

```bash
# Odstráň všetky obrazy projektu
docker-compose down --rmi all

# Alebo odstráň len lokálne zostavené obrazy
docker-compose down --rmi local

# Kompletné vyčistenie (kontajnery, obrazy, volumes, siete)
docker-compose down -v --rmi all --remove-orphans
```

## Pripojenie na databázu

### Cez pgAdmin4:
- **Host:** `localhost`
- **Port:** `5433`
- **Database:** `tassu_db`
- **User:** `tassu_user`
- **Password:** `tassu_password`

### Cez psql v Docker kontajneri:
```bash
docker exec -it tassu_postgres psql -U tassu_user -d tassu_db
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
```

## Databázová štruktúra

- **kategorie_chorob** - Kategórie civilizačných chorôb
- **choroby** - Konkrétne choroby s ICD-10 kódmi
- **demograficke_skupiny** - Vekové skupiny a pohlavie
- **vyskyt_chorob** - Hlavná tabuľka s výskytom chorôb
- **zivotny_styl_faktory** - Faktory životného štýlu (alkohol, fajčenie, šport...)
- **zivotny_styl_data** - Dáta o životnom štýle populácie
- **ekonomicke_indikatory** - Ekonomické ukazovatele (HDP, platy...)
- **environmentalne_faktory** - Environmentálne faktory (počasie, kvalita vzduchu...)

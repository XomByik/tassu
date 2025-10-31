# GBD 2023 - Švajčiarsko

Dynamická zdravotná databáza s automatickým vytváraním tabuliek.

## Spustenie

```bash
docker-compose up -d      # Spustiť
docker-compose down       # Zastaviť
docker-compose down -v    # Reset databázy
```

Import prebehne automaticky (~30s).

## Štruktúra

3 domény, 143 dynamicky vytvorených tabuliek:

1. **CHOROBY (dm_*)** - 126 tabuliek  
   Konkrétne choroby: diabetes, tuberkulóza, rakovina

2. **PROSTREDIE (em_*)** - 8 tabuliek  
   Riziká: znečistenie ovzdušia, nečistá voda

3. **ŽIVOTNÝ ŠTÝL (lm_*)** - 9 tabuliek  
   Riziká: alkohol, fajčenie, vysoké BMI

## Pripojenie do databázy

```bash
docker exec -it tassu_postgres psql -U tassu_user -d tassu_db
```

## Príklady dotazov

### 1. Koľko úmrtí spôsobených alkoholom v roku 2023?

```sql
SELECT 
  di.cause_name, 
  SUM(la.value) as deaths
FROM lm_high_alcohol_use la
JOIN disease_indicators di ON la.disease_indicator_id = di.indicator_id
WHERE 
  la.measure = 'Deaths' 
  AND la.year = 2023
GROUP BY di.cause_name
ORDER BY deaths DESC
LIMIT 20;
```

### 2. Časový priebeh diabetu

```sql
SELECT year, measure, sex, age, SUM(value) as total
FROM dm_diabetes_mellitus
GROUP BY year, measure, sex, age
ORDER BY year, measure;
```

### 3. Choroby spôsobené fajčením

```sql
SELECT di.cause_name, dg.group_name, SUM(s.value) as deaths
FROM lm_smoking s
JOIN disease_indicators di ON s.disease_indicator_id = di.indicator_id
JOIN disease_groups dg ON di.group_id = dg.group_id
WHERE s.measure = 'Deaths' AND s.year = 2023
GROUP BY di.cause_name, dg.group_name
ORDER BY deaths DESC;
```

### 4. Zoznam tabuliek

```sql
SELECT tablename FROM pg_tables 
WHERE tablename LIKE 'dm_%' OR tablename LIKE 'em_%' OR tablename LIKE 'lm_%'
ORDER BY tablename;
```

## Štatistiky

```
Choroby:      126 tabuliek,  23,646 záznamov
Prostredie:     8 tabuliek,   2,376 záznamov  
Život. štýl:    9 tabuliek,   6,743 záznamov
─────────────────────────────────────────────
CELKOM:       143 tabuliek,  32,765 záznamov
```

Vyfiltrovaných: 11,456 agregátov + 88 cirkulárnych závislostí

## Dáta

IHME Global Burden of Disease Study 2023 (Switzerland, 1990-2023)

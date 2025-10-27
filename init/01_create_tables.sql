-- ========================================
-- DEMOGRAFIA
-- ========================================

-- Demografické skupiny (vek, pohlavie)
CREATE TABLE demograficke_skupiny (
    id SERIAL PRIMARY KEY,
    vekova_skupina VARCHAR(50), -- '0-17', '18-34', '35-49', '50-64', '65+', 'vsetky'
    pohlavie VARCHAR(20) CHECK (pohlavie IN ('muz', 'zena', 'vsetky')),
    dimension_type VARCHAR(50), -- SEX, AGEGROUP, atď.
    dimension_code VARCHAR(100),
    dimension_name VARCHAR(200),
    vytvorene TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vekova_skupina, pohlavie, dimension_type, dimension_code)
);

-- ========================================
-- CHOROBY
-- ========================================

-- Kategórie chorôb (rakovina, respiračné ochorenia, kardiovaskulárne...)
CREATE TABLE kategorie_chorob (
    id SERIAL PRIMARY KEY,
    nazov VARCHAR(200) NOT NULL UNIQUE,
    kod VARCHAR(50) NOT NULL UNIQUE,
    popis TEXT,
    vytvorene TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Konkrétne choroby (COVID-19, rakovina hrubého čreva, astma...)
CREATE TABLE choroby (
    id SERIAL PRIMARY KEY,
    nazov TEXT NOT NULL,
    kod VARCHAR(100) NOT NULL UNIQUE, -- WHO GHO kód
    kategoria_id INTEGER NOT NULL,
    icd_kod VARCHAR(20), -- ICD-10 kód (ak je k dispozícii)
    popis TEXT,
    url TEXT,
    uroven_zavaznosti INTEGER CHECK (uroven_zavaznosti BETWEEN 1 AND 5),
    vytvorene TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (kategoria_id) REFERENCES kategorie_chorob(id)
);

-- Výskyt chorôb - merania v čase
CREATE TABLE vyskyt_chorob (
    id SERIAL PRIMARY KEY,
    choroba_id INTEGER NOT NULL,
    demografie_id INTEGER,
    rok INTEGER NOT NULL,

    -- Hodnoty merania
    hodnota_cislo DECIMAL(20,6),
    hodnota_text VARCHAR(200),
    dolna_hranica DECIMAL(20,6),
    horna_hranica DECIMAL(20,6),
    jednotka VARCHAR(100), -- deaths per 100k, %, cases, atď.

    -- Typ merania (úmrtnosť, incidencia, prevalencia, počet prípadov...)
    typ_merania VARCHAR(100), -- 'mortality', 'incidence', 'prevalence', 'cases'

    -- Metadata
    region_kod VARCHAR(20),
    region_nazov VARCHAR(100),
    krajina_kod VARCHAR(20),
    krajina_nazov VARCHAR(100),
    zdroj_url TEXT,

    vytvorene TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (choroba_id) REFERENCES choroby(id),
    FOREIGN KEY (demografie_id) REFERENCES demograficke_skupiny(id),

    UNIQUE(choroba_id, demografie_id, rok, typ_merania)
);

-- ========================================
-- ŽIVOTNÝ ŠTÝL
-- ========================================

-- Faktory životného štýlu (alkohol, fajčenie, výživa, šport...)
CREATE TABLE zivotny_styl (
    id SERIAL PRIMARY KEY,
    nazov VARCHAR(200) NOT NULL,
    kod VARCHAR(100) NOT NULL UNIQUE, -- WHO GHO kód
    kategoria VARCHAR(100) NOT NULL, -- 'alkohol', 'fajcenie', 'vyziva', 'fyzicka_aktivita'
    popis TEXT,
    url TEXT,
    jednotka VARCHAR(100),
    vytvorene TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dáta o životnom štýle populácie
CREATE TABLE zivotny_styl_data (
    id SERIAL PRIMARY KEY,
    zivotny_styl_id INTEGER NOT NULL,
    demografie_id INTEGER,
    rok INTEGER NOT NULL,

    -- Hodnoty merania
    hodnota_cislo DECIMAL(20,6),
    hodnota_text VARCHAR(200),
    dolna_hranica DECIMAL(20,6),
    horna_hranica DECIMAL(20,6),

    -- Špecifické atribúty
    typ_alkoholu VARCHAR(100), -- wine, beer, spirits (pre alkohol)
    typ_merania VARCHAR(200), -- consumption, prevalence (pre alkohol)
    severity VARCHAR(50), -- mild, moderate, severe (pre výživu)

    zdroj_url TEXT,
    vytvorene TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (zivotny_styl_id) REFERENCES zivotny_styl(id),
    FOREIGN KEY (demografie_id) REFERENCES demograficke_skupiny(id)

    -- Poznámka: Bez UNIQUE constraint kvôli NULL hodnotám v typ_alkoholu
    -- Duplicity sú možné, ale reálne by nemali nastať
);

-- ========================================
-- ENVIRONMENTÁLNE FAKTORY
-- ========================================

-- Environmentálne faktory (znečistenie ovzdušia, kvalita vody...)
CREATE TABLE environmentalne_faktory (
    id SERIAL PRIMARY KEY,
    nazov TEXT NOT NULL,
    kod VARCHAR(100) NOT NULL, -- WHO GHO kód
    rok INTEGER NOT NULL,
    demografie_id INTEGER,

    -- Hodnoty merania
    hodnota_cislo DECIMAL(20,6),
    hodnota_text VARCHAR(200),
    dolna_hranica DECIMAL(20,6),
    horna_hranica DECIMAL(20,6),

    -- Špecifické pre environment
    typ VARCHAR(100), -- air_pollution, water_quality, climate, atď.
    typ_znecistenia VARCHAR(100), -- PM2.5, PM10, ambient air, household air
    jednotka VARCHAR(100), -- μg/m³, ppm, atď.

    zdroj_url TEXT,
    vytvorene TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (demografie_id) REFERENCES demograficke_skupiny(id),

    UNIQUE(kod, rok, demografie_id)
);

-- ========================================
-- FINANCOVANIE ZDRAVOTNÍCTVA
-- ========================================

-- Výdavky na zdravotníctvo
CREATE TABLE financovanie_zdravotnictva (
    id SERIAL PRIMARY KEY,
    nazov TEXT NOT NULL,
    kod VARCHAR(100) NOT NULL, -- WHO GHO kód
    rok INTEGER NOT NULL,

    -- Finančné hodnoty
    hodnota_cislo DECIMAL(20,6),
    hodnota_text VARCHAR(200),

    -- Špecifické pre financovanie
    typ_vydavku VARCHAR(100), -- OOP (out-of-pocket), GGHE-D (government), PVT-D (private), CHE (current health expenditure)
    jednotka VARCHAR(100), -- %, USD, % of GDP

    region_kod VARCHAR(20),
    region_nazov VARCHAR(100),
    krajina_kod VARCHAR(20),
    krajina_nazov VARCHAR(100),
    zdroj_url TEXT,

    vytvorene TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(kod, rok, typ_vydavku)
);

-- ========================================
-- INDEXY PRE OPTIMALIZÁCIU
-- ========================================

-- Indexy pre choroby
CREATE INDEX idx_choroby_kategoria ON choroby(kategoria_id);
CREATE INDEX idx_choroby_kod ON choroby(kod);
CREATE INDEX idx_vyskyt_choroba_rok ON vyskyt_chorob(choroba_id, rok);
CREATE INDEX idx_vyskyt_demografie_rok ON vyskyt_chorob(demografie_id, rok);
CREATE INDEX idx_vyskyt_krajina_rok ON vyskyt_chorob(krajina_kod, rok);

-- Indexy pre životný štýl
CREATE INDEX idx_zivotny_styl_kategoria ON zivotny_styl(kategoria);
CREATE INDEX idx_zivotny_styl_kod ON zivotny_styl(kod);
CREATE INDEX idx_zivotny_styl_data_zs_rok ON zivotny_styl_data(zivotny_styl_id, rok);
CREATE INDEX idx_zivotny_styl_data_demografie_rok ON zivotny_styl_data(demografie_id, rok);

-- Indexy pre environment
CREATE INDEX idx_env_kod_rok ON environmentalne_faktory(kod, rok);
CREATE INDEX idx_env_typ ON environmentalne_faktory(typ);

-- Indexy pre financovanie
CREATE INDEX idx_fin_kod_rok ON financovanie_zdravotnictva(kod, rok);
CREATE INDEX idx_fin_typ_vydavku ON financovanie_zdravotnictva(typ_vydavku);

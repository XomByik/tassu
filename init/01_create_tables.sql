-- Kategórie zdravotných indikátorov
CREATE TABLE kategorie_indikatorov (
    id SERIAL PRIMARY KEY,
    nazov VARCHAR(200) NOT NULL UNIQUE,
    kod VARCHAR(50) NOT NULL UNIQUE,
    typ VARCHAR(50) NOT NULL, -- 'choroba', 'rizikovy_faktor', 'environmentalny', 'financovanie', 'vyzivovacie'
    popis TEXT,
    vytvorene TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Zdravotné indikátory (choroby, rizikové faktory, atď.)
CREATE TABLE zdravotne_indikatory (
    id SERIAL PRIMARY KEY,
    gho_kod VARCHAR(100) NOT NULL UNIQUE, -- WHO GHO kód
    nazov TEXT NOT NULL,
    url TEXT,
    kategoria_id INTEGER NOT NULL,
    jednotka VARCHAR(100), -- %, per 1000, deaths, cases, atď.
    popis TEXT,
    uroven_zavaznosti INTEGER CHECK (uroven_zavaznosti BETWEEN 1 AND 5),
    vytvorene TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (kategoria_id) REFERENCES kategorie_indikatorov(id)
);

-- Demografické skupiny
CREATE TABLE demograficke_skupiny (
    id SERIAL PRIMARY KEY,
    vekova_skupina VARCHAR(50), -- '0-17', '18-34', '35-49', '50-64', '65+', 'vsetky'
    pohlavie VARCHAR(20) CHECK (pohlavie IN ('muz', 'zena', 'vsetky')),
    dimension_type VARCHAR(50), -- SEX, AGEGROUP, ALCOHOLTYPE, atď.
    dimension_code VARCHAR(100),
    dimension_name VARCHAR(200),
    vytvorene TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vekova_skupina, pohlavie, dimension_type, dimension_code)
);

-- Hlavná tabuľka - merania zdravotných indikátorov
CREATE TABLE merania_indikatorov (
    id SERIAL PRIMARY KEY,
    indikator_id INTEGER NOT NULL,
    demograficka_skupina_id INTEGER,
    rok INTEGER NOT NULL,
    
    -- Hodnoty merania
    hodnota_cislo DECIMAL(20,6), -- numerická hodnota
    hodnota_text VARCHAR(200), -- textová hodnota (napr. "Data not available")
    dolna_hranica DECIMAL(20,6),
    horna_hranica DECIMAL(20,6),
    
    -- Metadata
    region_kod VARCHAR(20),
    region_nazov VARCHAR(100),
    krajina_kod VARCHAR(20),
    krajina_nazov VARCHAR(100),
    zdroj_url TEXT,
    
    vytvorene TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (indikator_id) REFERENCES zdravotne_indikatory(id),
    FOREIGN KEY (demograficka_skupina_id) REFERENCES demograficke_skupiny(id),
    
    UNIQUE(indikator_id, demograficka_skupina_id, rok)
);

-- Environmentálne faktory (znečistenie ovzdušia, klíma)
CREATE TABLE environmentalne_faktory (
    id SERIAL PRIMARY KEY,
    indikator_id INTEGER NOT NULL,
    rok INTEGER NOT NULL,
    demograficka_skupina_id INTEGER,
    
    -- Hodnoty
    hodnota_cislo DECIMAL(20,6),
    hodnota_text VARCHAR(200),
    dolna_hranica DECIMAL(20,6),
    horna_hranica DECIMAL(20,6),
    
    -- Špecifické pre environmentálne dáta
    typ_znecistenia VARCHAR(100), -- ambient air, household air, atď.
    merna_jednotka VARCHAR(100),
    
    zdroj_dat TEXT,
    vytvorene TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (indikator_id) REFERENCES zdravotne_indikatory(id),
    FOREIGN KEY (demograficka_skupina_id) REFERENCES demograficke_skupiny(id),
    
    UNIQUE(indikator_id, rok, demograficka_skupina_id)
);

-- Zdravotné financovanie
CREATE TABLE zdravotne_financovanie (
    id SERIAL PRIMARY KEY,
    indikator_id INTEGER NOT NULL,
    rok INTEGER NOT NULL,
    
    -- Finančné hodnoty
    hodnota_cislo DECIMAL(20,6),
    hodnota_text VARCHAR(200),
    
    -- Špecifické pre financovanie
    typ_vydavku VARCHAR(100), -- OOP, GGHE-D, PVT-D, CHE, atď.
    merna_jednotka VARCHAR(100), -- %, USD, atď.
    
    region_kod VARCHAR(20),
    region_nazov VARCHAR(100),
    zdroj_dat TEXT,
    vytvorene TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (indikator_id) REFERENCES zdravotne_indikatory(id),
    
    UNIQUE(indikator_id, rok)
);

-- Výživové indikátory
CREATE TABLE vyzivovacie_indikatory (
    id SERIAL PRIMARY KEY,
    indikator_id INTEGER NOT NULL,
    rok INTEGER NOT NULL,
    demograficka_skupina_id INTEGER,
    
    -- Hodnoty
    hodnota_cislo DECIMAL(20,6),
    hodnota_text VARCHAR(200),
    dolna_hranica DECIMAL(20,6),
    horna_hranica DECIMAL(20,6),
    
    -- Špecifické pre výživu
    typ_merania VARCHAR(100), -- BMI, anaemia, malnutrition, atď.
    severity VARCHAR(50), -- mild, moderate, severe
    
    zdroj_dat TEXT,
    vytvorene TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (indikator_id) REFERENCES zdravotne_indikatory(id),
    FOREIGN KEY (demograficka_skupina_id) REFERENCES demograficke_skupiny(id),
    
    UNIQUE(indikator_id, rok, demograficka_skupina_id)
);

-- Alkoholové indikátory
CREATE TABLE alkoholove_indikatory (
    id SERIAL PRIMARY KEY,
    indikator_id INTEGER NOT NULL,
    rok INTEGER NOT NULL,
    demograficka_skupina_id INTEGER,
    
    -- Hodnoty
    hodnota_cislo DECIMAL(20,6),
    hodnota_text VARCHAR(200),
    dolna_hranica DECIMAL(20,6),
    horna_hranica DECIMAL(20,6),
    
    -- Špecifické pre alkohol
    typ_alkoholu VARCHAR(100), -- wine, beer, spirits, all types
    typ_merania VARCHAR(200), -- consumption, prevalence, mortality, atď.
    
    zdroj_dat TEXT,
    vytvorene TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (indikator_id) REFERENCES zdravotne_indikatory(id),
    FOREIGN KEY (demograficka_skupina_id) REFERENCES demograficke_skupiny(id),
    
    UNIQUE(indikator_id, rok, demograficka_skupina_id)
);

-- Indexy pre optimalizáciu dotazov
CREATE INDEX idx_merania_indikator_rok ON merania_indikatorov(indikator_id, rok);
CREATE INDEX idx_merania_demog_rok ON merania_indikatorov(demograficka_skupina_id, rok);
CREATE INDEX idx_merania_krajina_rok ON merania_indikatorov(krajina_kod, rok);
CREATE INDEX idx_environmentalne_indikator_rok ON environmentalne_faktory(indikator_id, rok);
CREATE INDEX idx_financovanie_indikator_rok ON zdravotne_financovanie(indikator_id, rok);
CREATE INDEX idx_vyzivovacie_indikator_rok ON vyzivovacie_indikatory(indikator_id, rok);
CREATE INDEX idx_alkoholove_indikator_rok ON alkoholove_indikatory(indikator_id, rok);
CREATE INDEX idx_indikatory_kategoria ON zdravotne_indikatory(kategoria_id);
CREATE INDEX idx_indikatory_gho_kod ON zdravotne_indikatory(gho_kod);
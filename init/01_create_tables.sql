-- Kategórie chorôb
CREATE TABLE kategorie_chorob (
    id SERIAL PRIMARY KEY,
    nazov VARCHAR(100) NOT NULL UNIQUE,
    kod VARCHAR(20) NOT NULL UNIQUE,
    popis TEXT,
    vytvorene TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Konkrétne choroby
CREATE TABLE choroby (
    id SERIAL PRIMARY KEY,
    nazov VARCHAR(200) NOT NULL,
    icd_kod VARCHAR(20), -- ICD-10 kódy
    kategoria_id INTEGER NOT NULL,
    popis TEXT,
    uroven_zavaznosti INTEGER CHECK (uroven_zavaznosti BETWEEN 1 AND 5),
    vytvorene TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (kategoria_id) REFERENCES kategorie_chorob(id)
);

-- Demografické skupiny
CREATE TABLE demograficke_skupiny (
    id SERIAL PRIMARY KEY,
    vekova_skupina VARCHAR(20) NOT NULL, -- '0-17', '18-34', '35-49', '50-64', '65+'
    pohlavie VARCHAR(10) NOT NULL CHECK (pohlavie IN ('muz', 'zena', 'vsetky')),
    vytvorene TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vekova_skupina, pohlavie)
);

-- Životný štýl faktory
CREATE TABLE zivotny_styl_faktory (
    id SERIAL PRIMARY KEY,
    nazov_faktora VARCHAR(100) NOT NULL UNIQUE,
    jednotka_merania VARCHAR(50) NOT NULL,
    popis TEXT,
    vytvorene TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ekonomické indikátory (celoštátne)
CREATE TABLE ekonomicke_indikatory (
    id SERIAL PRIMARY KEY,
    rok INTEGER NOT NULL UNIQUE,
    hdp_na_obyvatela DECIMAL(12,2),
    priemerny_plat DECIMAL(12,2),
    miera_chudoby DECIMAL(5,2), -- percentá
    miera_nezamestnanosti DECIMAL(5,2),
    vytvorene TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Environmentálne faktory (celoštátne priemery)
CREATE TABLE environmentalne_faktory (
    id SERIAL PRIMARY KEY,
    rok INTEGER NOT NULL,
    mesiac INTEGER CHECK (mesiac BETWEEN 1 AND 12),
    priemerna_teplota DECIMAL(5,2),
    vlhkost DECIMAL(5,2),
    index_kvality_vzduchu DECIMAL(6,2),
    zrazky DECIMAL(8,2),
    vytvorene TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(rok, mesiac)
);

-- Korelácie medzi výskytom chorôb a ekonomickými faktormi
CREATE TABLE korelacia_choroby_ekonomika (
    id SERIAL PRIMARY KEY,
    choroba_id INTEGER NOT NULL,
    ekonomicky_indikator_id INTEGER NOT NULL,
    korelacny_koeficient DECIMAL(5,4) NOT NULL, -- -1.0 to 1.0
    p_hodnota DECIMAL(10,8),
    uroven_spolahliv DECIMAL(5,2),
    poznamky TEXT,
    vytvorene TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (choroba_id) REFERENCES choroby(id) ON DELETE CASCADE,
    FOREIGN KEY (ekonomicky_indikator_id) REFERENCES ekonomicke_indikatory(id) ON DELETE CASCADE,
    UNIQUE(choroba_id, ekonomicky_indikator_id)
);

-- Korelácie medzi výskytom chorôb a environmentálnymi faktormi
CREATE TABLE korelacia_choroby_prostredie (
    id SERIAL PRIMARY KEY,
    choroba_id INTEGER NOT NULL,
    rok INTEGER NOT NULL,
    mesiac INTEGER CHECK (mesiac BETWEEN 1 AND 12),
    korelacia_teplota DECIMAL(5,4),
    korelacia_vlhkost DECIMAL(5,4),
    korelacia_kvalita_vzduchu DECIMAL(5,4),
    korelacia_zrazky DECIMAL(5,4),
    poznamky TEXT,
    vytvorene TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (choroba_id) REFERENCES choroby(id) ON DELETE CASCADE,
    UNIQUE(choroba_id, rok, mesiac)
);

-- Hlavná tabuľka - výskyt chorôb (celoštátne)
CREATE TABLE vyskyt_chorob (
    id SERIAL PRIMARY KEY,
    choroba_id INTEGER NOT NULL,
    demograficka_skupina_id INTEGER NOT NULL,
    rok INTEGER NOT NULL,
    mesiac INTEGER CHECK (mesiac BETWEEN 1 AND 12),
    
    -- Štatistiky
    celkovy_pocet_pripadov INTEGER NOT NULL DEFAULT 0,
    nove_pripady INTEGER NOT NULL DEFAULT 0,
    pocet_umrti INTEGER NOT NULL DEFAULT 0,
    pocet_vyliecenych INTEGER DEFAULT 0,
    pocet_hospitalizovanych INTEGER DEFAULT 0,
    
    -- Zdroj dát
    zdroj_dat VARCHAR(200) NOT NULL, -- WHO, Swiss Federal Statistical Office, etc.
    kvalita_dat INTEGER CHECK (kvalita_dat BETWEEN 1 AND 5),
    
    vytvorene TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    aktualizovane TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (choroba_id) REFERENCES choroby(id),
    FOREIGN KEY (demograficka_skupina_id) REFERENCES demograficke_skupiny(id),
    
    UNIQUE(choroba_id, demograficka_skupina_id, rok, mesiac)
);

-- Životný štýl dáta (celoštátne pre demografické skupiny)
CREATE TABLE zivotny_styl_data (
    id SERIAL PRIMARY KEY,
    demograficka_skupina_id INTEGER NOT NULL,
    faktor_id INTEGER NOT NULL,
    rok INTEGER NOT NULL,
    
    -- Hodnoty
    priemerna_hodnota DECIMAL(12,4) NOT NULL,
    minimalna_hodnota DECIMAL(12,4),
    maximalna_hodnota DECIMAL(12,4),
    velkost_vzorky INTEGER,
    
    zdroj_dat VARCHAR(200),
    vytvorene TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (demograficka_skupina_id) REFERENCES demograficke_skupiny(id),
    FOREIGN KEY (faktor_id) REFERENCES zivotny_styl_faktory(id),
    
    UNIQUE(demograficka_skupina_id, faktor_id, rok)
);

-- Indexy pre optimalizáciu dotazov
CREATE INDEX idx_vyskyt_chorob_choroba_rok ON vyskyt_chorob(choroba_id, rok);
CREATE INDEX idx_vyskyt_chorob_demog_rok ON vyskyt_chorob(demograficka_skupina_id, rok);
CREATE INDEX idx_zivotny_styl_data_demog_rok ON zivotny_styl_data(demograficka_skupina_id, rok);
CREATE INDEX idx_environmentalne_faktory_rok ON environmentalne_faktory(rok);
CREATE INDEX idx_korelacia_choroby_ekonomika_choroba ON korelacia_choroby_ekonomika(choroba_id);
CREATE INDEX idx_korelacia_choroby_prostredie_choroba ON korelacia_choroby_prostredie(choroba_id, rok);
-- ============================================================
-- GBD 2023 SWITZERLAND - ROZMEROVÁ DATABÁZA
-- 3 Domény: CHOROBY, PROSTREDIE, ŽIVOTNÝ ŠTÝL
-- Dynamické vytvorenie faktových tabuliek cez Python
-- ============================================================

-- ============================================================
-- DOMÉNA 1: CHOROBY
-- ============================================================

CREATE TABLE disease_groups (
    group_id SERIAL PRIMARY KEY,
    group_code VARCHAR(50) UNIQUE NOT NULL,
    group_name VARCHAR(100) NOT NULL
);

CREATE TABLE disease_indicators (
    indicator_id SERIAL PRIMARY KEY,
    cause_id INT UNIQUE NOT NULL,
    cause_name VARCHAR(255) NOT NULL,
    group_id INT REFERENCES disease_groups(group_id),
    table_name VARCHAR(100) UNIQUE NOT NULL
);

-- ============================================================
-- DOMÉNA 2: PROSTREDIE
-- ============================================================

CREATE TABLE environment_groups (
    group_id SERIAL PRIMARY KEY,
    group_code VARCHAR(50) UNIQUE NOT NULL,
    group_name VARCHAR(100) NOT NULL
);

CREATE TABLE environment_indicators (
    indicator_id SERIAL PRIMARY KEY,
    rei_id INT UNIQUE NOT NULL,
    rei_name VARCHAR(255) NOT NULL,
    group_id INT REFERENCES environment_groups(group_id),
    table_name VARCHAR(100) NOT NULL
);

-- ============================================================
-- DOMÉNA 3: ŽIVOTNÝ ŠTÝL
-- ============================================================

CREATE TABLE lifestyle_groups (
    group_id SERIAL PRIMARY KEY,
    group_code VARCHAR(50) UNIQUE NOT NULL,
    group_name VARCHAR(100) NOT NULL
);

CREATE TABLE lifestyle_indicators (
    indicator_id SERIAL PRIMARY KEY,
    rei_id INT UNIQUE NOT NULL,
    rei_name VARCHAR(255) NOT NULL,
    group_id INT REFERENCES lifestyle_groups(group_id),
    table_name VARCHAR(100) NOT NULL
);

-- ============================================================
-- STORED PROCEDURES
-- ============================================================

-- Dynamické vytvorenie disease tabuľky
CREATE OR REPLACE FUNCTION create_disease_table(p_table_name VARCHAR)
RETURNS VOID AS $$
BEGIN
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %I (
            country VARCHAR(3) DEFAULT ''CHE'',
            sex VARCHAR(20) NOT NULL,
            age VARCHAR(50) NOT NULL,
            year INT NOT NULL,
            indicator_id INT NOT NULL,
            measure VARCHAR(20) NOT NULL,
            value INT NOT NULL,
            PRIMARY KEY (country, sex, age, year, indicator_id, measure)
        )', p_table_name);
    
    EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%I_year ON %I(year)', p_table_name, p_table_name);
END;
$$ LANGUAGE plpgsql;

-- Dynamické vytvorenie environment tabuľky
CREATE OR REPLACE FUNCTION create_environment_table(p_table_name VARCHAR)
RETURNS VOID AS $$
BEGIN
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %I (
            country VARCHAR(3) DEFAULT ''CHE'',
            sex VARCHAR(20) NOT NULL,
            age VARCHAR(50) NOT NULL,
            year INT NOT NULL,
            disease_indicator_id INT NOT NULL,
            env_indicator_id INT NOT NULL,
            measure VARCHAR(20) NOT NULL,
            value INT NOT NULL,
            PRIMARY KEY (country, sex, age, year, disease_indicator_id, env_indicator_id, measure)
        )', p_table_name);
    
    EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%I_year ON %I(year)', p_table_name, p_table_name);
END;
$$ LANGUAGE plpgsql;

-- Dynamické vytvorenie lifestyle tabuľky
CREATE OR REPLACE FUNCTION create_lifestyle_table(p_table_name VARCHAR)
RETURNS VOID AS $$
BEGIN
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %I (
            country VARCHAR(3) DEFAULT ''CHE'',
            sex VARCHAR(20) NOT NULL,
            age VARCHAR(50) NOT NULL,
            year INT NOT NULL,
            disease_indicator_id INT NOT NULL,
            lifestyle_indicator_id INT NOT NULL,
            measure VARCHAR(20) NOT NULL,
            value INT NOT NULL,
            PRIMARY KEY (country, sex, age, year, disease_indicator_id, lifestyle_indicator_id, measure)
        )', p_table_name);
    
    EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%I_year ON %I(year)', p_table_name, p_table_name);
END;
$$ LANGUAGE plpgsql;

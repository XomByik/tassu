-- Star Schema pre 4 RIZIKO→CHOROBA páry
-- Krajiny: Švajčiarsko (CHE), Nemecko (DEU), Švédsko (SWE), USA (USA)
-- Roky: 2013-2023
-- Páry: Smoking→Lung Cancer, High BMI→CVD, Air Pollution→Respiratory, Alcohol→Cirrhosis

-- ============================================================
-- DIMENSION TABLES
-- ============================================================

-- Dimension: Krajiny
DROP TABLE IF EXISTS dim_country CASCADE;
CREATE TABLE dim_country (
    country_id SERIAL PRIMARY KEY,
    country_code VARCHAR(3) UNIQUE NOT NULL,
    country_name VARCHAR(100) NOT NULL
);

INSERT INTO dim_country (country_code, country_name) VALUES
('CHE', 'Switzerland'),
('DEU', 'Germany'),
('SWE', 'Sweden'),
('USA', 'United States');

-- Dimension: Pohlavie
DROP TABLE IF EXISTS dim_sex CASCADE;
CREATE TABLE dim_sex (
    sex_id SERIAL PRIMARY KEY,
    sex_code VARCHAR(10) UNIQUE NOT NULL,
    sex_name VARCHAR(50) NOT NULL
);

INSERT INTO dim_sex (sex_code, sex_name) VALUES
('M', 'Male'),
('F', 'Female'),
('B', 'Both');

-- Dimension: Vekové skupiny (WHO štandard)
DROP TABLE IF EXISTS dim_age_group CASCADE;
CREATE TABLE dim_age_group (
    age_group_id SERIAL PRIMARY KEY,
    age_group_code VARCHAR(20) UNIQUE NOT NULL,
    age_group_name VARCHAR(100) NOT NULL,
    age_from INTEGER,
    age_to INTEGER
);

INSERT INTO dim_age_group (age_group_code, age_group_name, age_from, age_to) VALUES
('0-14', '0-14 years', 0, 14),
('15-49', '15-49 years', 15, 49),
('50-69', '50-69 years', 50, 69),
('70+', '70+ years', 70, NULL),
('ALL', 'All ages', 0, NULL);

-- Dimension: Roky
DROP TABLE IF EXISTS dim_year CASCADE;
CREATE TABLE dim_year (
    year_id SERIAL PRIMARY KEY,
    year INTEGER UNIQUE NOT NULL
);

INSERT INTO dim_year (year) VALUES
(2013), (2014), (2015), (2016), (2017), (2018), (2019), (2020), (2021), (2022), (2023);

-- ============================================================
-- FACT TABLES - RISK→DISEASE RELATIONSHIPS
-- ============================================================

-- FACT 1: Smoking → Lung Cancer
DROP TABLE IF EXISTS fact_smoking_lung_cancer CASCADE;
CREATE TABLE fact_smoking_lung_cancer (
    fact_id SERIAL PRIMARY KEY,
    country_id INTEGER NOT NULL REFERENCES dim_country(country_id),
    sex_id INTEGER NOT NULL REFERENCES dim_sex(sex_id),
    age_group_id INTEGER NOT NULL REFERENCES dim_age_group(age_group_id),
    year_id INTEGER NOT NULL REFERENCES dim_year(year_id),
    lung_cancer_deaths NUMERIC(15, 2),      -- úmrtia na rakovinu pľúc
    attributable_deaths NUMERIC(15, 2),     -- úmrtia pripisateľné fajčeniu
    UNIQUE(country_id, sex_id, age_group_id, year_id)
);

CREATE INDEX idx_smoking_lc_country ON fact_smoking_lung_cancer(country_id);
CREATE INDEX idx_smoking_lc_year ON fact_smoking_lung_cancer(year_id);

-- FACT 2: High BMI → Cardiovascular Disease
DROP TABLE IF EXISTS fact_bmi_cardiovascular CASCADE;
CREATE TABLE fact_bmi_cardiovascular (
    fact_id SERIAL PRIMARY KEY,
    country_id INTEGER NOT NULL REFERENCES dim_country(country_id),
    sex_id INTEGER NOT NULL REFERENCES dim_sex(sex_id),
    age_group_id INTEGER NOT NULL REFERENCES dim_age_group(age_group_id),
    year_id INTEGER NOT NULL REFERENCES dim_year(year_id),
    cvd_deaths NUMERIC(15, 2),              -- úmrtia na kardiovaskulárne choroby
    attributable_deaths NUMERIC(15, 2),     -- úmrtia pripisateľné vysokému BMI
    UNIQUE(country_id, sex_id, age_group_id, year_id)
);

CREATE INDEX idx_bmi_cvd_country ON fact_bmi_cardiovascular(country_id);
CREATE INDEX idx_bmi_cvd_year ON fact_bmi_cardiovascular(year_id);

-- FACT 3: Air Pollution → Respiratory Disease
DROP TABLE IF EXISTS fact_pollution_respiratory CASCADE;
CREATE TABLE fact_pollution_respiratory (
    fact_id SERIAL PRIMARY KEY,
    country_id INTEGER NOT NULL REFERENCES dim_country(country_id),
    sex_id INTEGER NOT NULL REFERENCES dim_sex(sex_id),
    age_group_id INTEGER NOT NULL REFERENCES dim_age_group(age_group_id),
    year_id INTEGER NOT NULL REFERENCES dim_year(year_id),
    respiratory_deaths NUMERIC(15, 2),      -- úmrtia na respiračné choroby
    attributable_deaths NUMERIC(15, 2),     -- úmrtia pripisateľné znečisteniu
    UNIQUE(country_id, sex_id, age_group_id, year_id)
);

CREATE INDEX idx_pollution_resp_country ON fact_pollution_respiratory(country_id);
CREATE INDEX idx_pollution_resp_year ON fact_pollution_respiratory(year_id);

-- FACT 4: High Alcohol → Liver Cirrhosis
DROP TABLE IF EXISTS fact_alcohol_cirrhosis CASCADE;
CREATE TABLE fact_alcohol_cirrhosis (
    fact_id SERIAL PRIMARY KEY,
    country_id INTEGER NOT NULL REFERENCES dim_country(country_id),
    sex_id INTEGER NOT NULL REFERENCES dim_sex(sex_id),
    age_group_id INTEGER NOT NULL REFERENCES dim_age_group(age_group_id),
    year_id INTEGER NOT NULL REFERENCES dim_year(year_id),
    cirrhosis_deaths NUMERIC(15, 2),        -- úmrtia na cirhózu pečene
    attributable_deaths NUMERIC(15, 2),     -- úmrtia pripisateľné alkoholu
    UNIQUE(country_id, sex_id, age_group_id, year_id)
);

CREATE INDEX idx_alcohol_cirr_country ON fact_alcohol_cirrhosis(country_id);
CREATE INDEX idx_alcohol_cirr_year ON fact_alcohol_cirrhosis(year_id);

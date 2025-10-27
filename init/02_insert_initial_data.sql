-- Kategórie chorôb
INSERT INTO kategorie_chorob (nazov, kod, popis) VALUES
('Rakovina', 'C00-C97', 'Zhubné nádory'),
('Srdcovo-cievne choroby', 'I00-I99', 'Choroby obehovej sústavy'),
('Respiračné choroby', 'J00-J99', 'Choroby dýchacej sústavy'),
('Endokrinné choroby', 'E00-E89', 'Endokrinné, výživové a metabolické choroby'),
('Duševné zdravie', 'F00-F99', 'Duševné a behaviorálne poruchy'),
('Neurologické choroby', 'G00-G99', 'Choroby nervového systému');

-- Konkrétne choroby
INSERT INTO choroby (nazov, icd_kod, kategoria_id, uroven_zavaznosti) VALUES
-- Rakovina
('Rakovina pľúc', 'C78', 1, 5),
('Rakovina prsníka', 'C50', 1, 4),
('Kolorektálna rakovina', 'C18-C20', 1, 4),
('Rakovina prostaty', 'C61', 1, 3),
-- Kardiovaskulárne
('Infarkt myokardu', 'I21', 2, 5),
('Hypertenzia', 'I10', 2, 2),
('Mozgová príhoda', 'I64', 2, 4),
-- Respiračné
('COVID-19', 'U07.1', 3, 3),
('Chrípka', 'J11', 3, 2),
('Astma', 'J45', 3, 2),
('COPD', 'J44', 3, 4),
-- Endokrinné
('Cukrovka 1. typu', 'E10', 4, 3),
('Cukrovka 2. typu', 'E11', 4, 3),
-- Duševné zdravie
('Ťažká depresia', 'F32', 5, 3),
('Úzkostné poruchy', 'F41', 5, 2),
-- Neurologické
('Alzheimerova choroba', 'G30', 6, 5),
('Parkinsonova choroba', 'G20', 6, 4);

-- Demografické skupiny
INSERT INTO demograficke_skupiny (vekova_skupina, pohlavie) VALUES
('0-17', 'muz'), ('0-17', 'zena'),
('18-34', 'muz'), ('18-34', 'zena'),
('35-49', 'muz'), ('35-49', 'zena'),
('50-64', 'muz'), ('50-64', 'zena'),
('65+', 'muz'), ('65+', 'zena'),
('vsetky', 'vsetky'); -- pre celkové štatistiky

-- Životný štýl faktory
INSERT INTO zivotny_styl_faktory (nazov_faktora, jednotka_merania, popis) VALUES
('Spotreba alkoholu', 'litre/rok', 'Ročná spotreba alkoholu na obyvateľa'),
('Miera fajčenia', 'percentá', 'Percento obyvateľstva ktoré fajčí'),
('Užívanie drog', 'percentá', 'Percento obyvateľstva užívajúce drogy'),
('Fyzická aktivita', 'hodiny/týždeň', 'Priemerné hodiny fyzickej aktivity týždenne'),
('Priemerné BMI', 'kg/m²', 'Priemerný index telesnej hmotnosti'),
('Spánok', 'hodiny/deň', 'Priemerné hodiny spánku denne'),
('Úroveň stresu', 'škála 1-10', 'Subjektívne hodnotená úroveň stresu');

-- Ekonomické indikátory (testovacie dáta 2015-2024)
INSERT INTO ekonomicke_indikatory (rok, hdp_na_obyvatela, priemerny_plat, miera_chudoby, miera_nezamestnanosti) VALUES
(2015, 82500.00, 6500.00, 6.7, 3.2),
(2016, 83200.00, 6580.00, 6.5, 3.3),
(2017, 84100.00, 6650.00, 6.4, 3.1),
(2018, 85300.00, 6750.00, 6.3, 2.9),
(2019, 86800.00, 6820.00, 6.1, 2.8),
(2020, 84500.00, 6900.00, 6.8, 4.1), -- COVID-19 vplyv
(2021, 86200.00, 7050.00, 6.6, 3.5),
(2022, 88500.00, 7200.00, 6.3, 2.9),
(2023, 90100.00, 7380.00, 6.0, 2.7),
(2024, 91500.00, 7520.00, 5.8, 2.6);

-- Environmentálne faktory (vzorové dáta pre 2023-2024)
INSERT INTO environmentalne_faktory (rok, mesiac, priemerna_teplota, vlhkost, index_kvality_vzduchu, zrazky) VALUES
-- 2023
(2023, 1, 2.5, 75.0, 45.2, 68.5),
(2023, 2, 3.8, 72.0, 42.8, 55.3),
(2023, 3, 7.2, 68.5, 38.5, 62.1),
(2023, 4, 11.5, 65.0, 35.2, 72.8),
(2023, 5, 16.8, 62.5, 32.1, 85.5),
(2023, 6, 20.3, 60.0, 30.5, 95.2),
(2023, 7, 23.5, 58.5, 28.8, 102.3),
(2023, 8, 22.8, 59.0, 31.2, 98.7),
(2023, 9, 18.5, 63.5, 35.8, 78.5),
(2023, 10, 13.2, 68.0, 40.5, 68.2),
(2023, 11, 7.8, 72.5, 44.2, 75.8),
(2023, 12, 3.2, 76.0, 48.5, 82.3),
-- 2024
(2024, 1, 1.8, 77.0, 47.5, 72.1),
(2024, 2, 4.2, 73.5, 43.2, 58.9),
(2024, 3, 8.1, 69.0, 39.8, 65.5),
(2024, 4, 12.3, 64.5, 34.8, 70.2),
(2024, 5, 17.5, 61.0, 31.5, 88.3),
(2024, 6, 21.2, 59.5, 29.8, 92.8);
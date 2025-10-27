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
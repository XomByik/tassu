-- Comprehensive verification query for 2013-2023 data
-- Uses UNION ALL to avoid cartesian product from multiple LEFT JOINs

WITH smoking_data AS (
  SELECT c.country_name, y.year, SUM(f.lung_cancer_deaths) AS value
  FROM fact_smoking_lung_cancer f
  JOIN dim_country c ON f.country_id = c.country_id
  JOIN dim_year y ON f.year_id = y.year_id
  WHERE c.country_code IN ('DEU', 'SWE', 'CHE', 'USA')
  GROUP BY c.country_name, y.year
),
bmi_data AS (
  SELECT c.country_name, y.year, SUM(f.cvd_deaths) AS value
  FROM fact_bmi_cardiovascular f
  JOIN dim_country c ON f.country_id = c.country_id
  JOIN dim_year y ON f.year_id = y.year_id
  WHERE c.country_code IN ('DEU', 'SWE', 'CHE', 'USA')
  GROUP BY c.country_name, y.year
),
pollution_data AS (
  SELECT c.country_name, y.year, SUM(f.respiratory_deaths) AS value
  FROM fact_pollution_respiratory f
  JOIN dim_country c ON f.country_id = c.country_id
  JOIN dim_year y ON f.year_id = y.year_id
  WHERE c.country_code IN ('DEU', 'SWE', 'CHE', 'USA')
  GROUP BY c.country_name, y.year
),
alcohol_data AS (
  SELECT c.country_name, y.year, SUM(f.cirrhosis_deaths) AS value
  FROM fact_alcohol_cirrhosis f
  JOIN dim_country c ON f.country_id = c.country_id
  JOIN dim_year y ON f.year_id = y.year_id
  WHERE c.country_code IN ('DEU', 'SWE', 'CHE', 'USA')
  GROUP BY c.country_name, y.year
)
SELECT 
  COALESCE(s.country_name, b.country_name, p.country_name, a.country_name) AS country_name,
  COALESCE(s.year, b.year, p.year, a.year) AS year,
  ROUND(COALESCE(s.value, 0), 0) AS smoking_lc,
  ROUND(COALESCE(b.value, 0), 0) AS bmi_cvd,
  ROUND(COALESCE(p.value, 0), 0) AS pollution_resp,
  ROUND(COALESCE(a.value, 0), 0) AS alcohol_cirr
FROM smoking_data s
FULL OUTER JOIN bmi_data b ON s.country_name = b.country_name AND s.year = b.year
FULL OUTER JOIN pollution_data p ON COALESCE(s.country_name, b.country_name) = p.country_name 
                                 AND COALESCE(s.year, b.year) = p.year
FULL OUTER JOIN alcohol_data a ON COALESCE(s.country_name, b.country_name, p.country_name) = a.country_name 
                                AND COALESCE(s.year, b.year, p.year) = a.year
WHERE COALESCE(s.year, b.year, p.year, a.year) BETWEEN 2013 AND 2023
ORDER BY country_name, year;

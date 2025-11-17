#!/bin/bash
set -e

echo "⏳ Waiting for databases to initialize (60 seconds)..."
sleep 60

echo ""
echo "🧹 Cleaning up existing data..."
psql -h postgres -U tassu_user -d tassu_db -c "TRUNCATE fact_smoking_lung_cancer, fact_bmi_cardiovascular, fact_pollution_respiratory, fact_alcohol_cirrhosis RESTART IDENTITY CASCADE;" 2>/dev/null || echo "Tables are empty or don't exist yet."

echo ""
echo "🚀 Starting ETL process..."
python extract_risk_disease.py

echo ""
echo "📊 Displaying results for all 4 RISK→DISEASE fact tables:"
echo "============================================================"
echo ""
echo "Columns:"
echo "  - total_* = Total deaths from disease/disease category"
echo "  - attr_*  = Attributable deaths from risk factor"
echo ""
echo "Diseases:"
echo "  - Lung Cancer (LC)"
echo "  - Cardiovascular Disease (CVD) - Ischemic heart disease + Stroke"
echo "  - Respiratory Disease (Resp) - COPD + Lower respiratory infections"
echo "  - Liver Cirrhosis (Cirr)"
echo ""

psql -h postgres -U tassu_user -d tassu_db <<-EOSQL
    SELECT 
        c.country_name,
        y.year,
        COALESCE(ROUND(lc.total_lc, 0), 0) as total_lc,
        COALESCE(ROUND(lc.attr_lc, 0), 0) as attr_lc,
        COALESCE(ROUND(cv.total_cvd, 0), 0) as total_cvd,
        COALESCE(ROUND(cv.attr_cvd, 0), 0) as attr_cvd,
        COALESCE(ROUND(rp.total_resp, 0), 0) as total_resp,
        COALESCE(ROUND(rp.attr_resp, 0), 0) as attr_resp,
        COALESCE(ROUND(ac.total_cirr, 0), 0) as total_cirr,
        COALESCE(ROUND(ac.attr_cirr, 0), 0) as attr_cirr
    FROM dim_country c
    CROSS JOIN dim_year y
    LEFT JOIN (
        SELECT country_id, year_id, 
               SUM(lung_cancer_deaths) as total_lc,
               SUM(attributable_deaths) as attr_lc
        FROM fact_smoking_lung_cancer
        GROUP BY country_id, year_id
    ) lc ON c.country_id = lc.country_id AND y.year_id = lc.year_id
    LEFT JOIN (
        SELECT country_id, year_id,
               SUM(cvd_deaths) as total_cvd,
               SUM(attributable_deaths) as attr_cvd
        FROM fact_bmi_cardiovascular
        GROUP BY country_id, year_id
    ) cv ON c.country_id = cv.country_id AND y.year_id = cv.year_id
    LEFT JOIN (
        SELECT country_id, year_id,
               SUM(respiratory_deaths) as total_resp,
               SUM(attributable_deaths) as attr_resp
        FROM fact_pollution_respiratory
        GROUP BY country_id, year_id
    ) rp ON c.country_id = rp.country_id AND y.year_id = rp.year_id
    LEFT JOIN (
        SELECT country_id, year_id,
               SUM(cirrhosis_deaths) as total_cirr,
               SUM(attributable_deaths) as attr_cirr
        FROM fact_alcohol_cirrhosis
        GROUP BY country_id, year_id
    ) ac ON c.country_id = ac.country_id AND y.year_id = ac.year_id
    WHERE lc.total_lc IS NOT NULL OR cv.total_cvd IS NOT NULL 
        OR rp.total_resp IS NOT NULL OR ac.total_cirr IS NOT NULL
    ORDER BY c.country_name, y.year;
EOSQL

echo ""
echo "✅ All done! Total records by table:"
psql -h postgres -U tassu_user -d tassu_db <<-EOSQL
    SELECT COUNT(*) as total_records, 'fact_smoking_lung_cancer' as table_name 
    FROM fact_smoking_lung_cancer 
    UNION ALL 
    SELECT COUNT(*), 'fact_bmi_cardiovascular' 
    FROM fact_bmi_cardiovascular 
    UNION ALL 
    SELECT COUNT(*), 'fact_pollution_respiratory' 
    FROM fact_pollution_respiratory 
    UNION ALL 
    SELECT COUNT(*), 'fact_alcohol_cirrhosis' 
    FROM fact_alcohol_cirrhosis 
    UNION ALL 
    SELECT SUM(cnt), 'TOTAL' 
    FROM (
        SELECT COUNT(*) as cnt FROM fact_smoking_lung_cancer 
        UNION ALL SELECT COUNT(*) FROM fact_bmi_cardiovascular 
        UNION ALL SELECT COUNT(*) FROM fact_pollution_respiratory 
        UNION ALL SELECT COUNT(*) FROM fact_alcohol_cirrhosis
    ) t;
EOSQL

echo ""
echo "🎉 Data warehouse is ready! You can now query the database."

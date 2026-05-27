  ========================================================================================
   PROJECT: International Debt Analysis System
  ======================================================================================== 

 -----------------------------------------------------------------------------------------
   PART 1: RELATIONAL DATABASE STRUCTURAL CONSTRAINTS
   (Note: These were executed dynamically via Python/SQLAlchemy during data ingestion)
-----------------------------------------------------------------------------------------
-- Apply Primary Keys to Dimension Tables
ALTER TABLE countries_metadata ADD PRIMARY KEY ("Country Code");
ALTER TABLE indicators_metadata ADD PRIMARY KEY ("Series Code");

-- Clean orphaned records to ensure referential integrity
DELETE FROM debt_data 
WHERE "Country Code" NOT IN (SELECT "Country Code" FROM countries_metadata)
   OR "Series Code" NOT IN (SELECT "Series Code" FROM indicators_metadata);

-- Apply Foreign Keys to Fact Table
ALTER TABLE debt_data 
ADD CONSTRAINT fk_country FOREIGN KEY ("Country Code") REFERENCES countries_metadata("Country Code") ON DELETE CASCADE;

ALTER TABLE debt_data 
ADD CONSTRAINT fk_indicator FOREIGN KEY ("Series Code") REFERENCES indicators_metadata("Series Code") ON DELETE CASCADE;


 -----------------------------------------------------------------------------------------
   PART 2: BASIC ANALYTICAL QUERIES (1-10)
 -----------------------------------------------------------------------------------------
-- 1. Retrieve all distinct country names from the dataset.
SELECT DISTINCT "Country Name" FROM debt_data;

-- 2. Count the total number of countries available.
SELECT COUNT(DISTINCT "Country Code") AS total_countries FROM debt_data;

-- 3. Find the total number of indicators present.
SELECT COUNT(DISTINCT "Series Code") AS total_indicators FROM debt_data;

-- 4. Display the first 10 records of the dataset.
SELECT * FROM debt_data LIMIT 10;

-- 5. Calculate the total global debt.
SELECT SUM("Value") AS total_global_debt FROM debt_data;

-- 6. List all unique indicator names.
SELECT DISTINCT "Series Name" FROM debt_data;

-- 7. Find the number of records for each country.
SELECT "Country Name", COUNT(*) AS record_count 
FROM debt_data 
GROUP BY "Country Name";

-- 8. Display all records where debt is greater than 1 billion USD.
SELECT * FROM debt_data WHERE "Value" > 1000000000;

-- 9. Find the minimum, maximum, and average debt values.
SELECT MIN("Value") AS min_debt, MAX("Value") AS max_debt, AVG("Value") AS avg_debt 
FROM debt_data;

-- 10. Count total number of records in the dataset.
SELECT COUNT(*) AS total_records FROM debt_data;


 -----------------------------------------------------------------------------------------
   PART 3: INTERMEDIATE ANALYTICAL QUERIES (11-20)
 ----------------------------------------------------------------------------------------- 
-- 11. Find the total debt for each country.
SELECT "Country Name", SUM("Value") AS total_debt 
FROM debt_data 
GROUP BY "Country Name";

-- 12. Display the top 10 countries with the highest total debt.
SELECT "Country Name", SUM("Value") AS total_debt 
FROM debt_data 
GROUP BY "Country Name" 
ORDER BY total_debt DESC 
LIMIT 10;

-- 13. Find the average debt per country.
SELECT "Country Name", AVG("Value") AS average_debt 
FROM debt_data 
GROUP BY "Country Name";

-- 14. Calculate total debt for each indicator.
SELECT "Series Code", "Series Name", SUM("Value") AS total_debt 
FROM debt_data 
GROUP BY "Series Code", "Series Name";

-- 15. Identify the indicator contributing the highest total debt.
SELECT "Series Code", "Series Name", SUM("Value") AS total_debt 
FROM debt_data 
GROUP BY "Series Code", "Series Name" 
ORDER BY total_debt DESC 
LIMIT 1;

-- 16. Find the country with the lowest total debt.
SELECT "Country Name", SUM("Value") AS total_debt 
FROM debt_data 
GROUP BY "Country Name" 
ORDER BY total_debt ASC 
LIMIT 1;

-- 17. Calculate total debt for each country and indicator combination.
SELECT "Country Name", "Series Name", SUM("Value") AS combined_debt 
FROM debt_data 
GROUP BY "Country Name", "Series Name";

-- 18. Count how many indicators each country has.
SELECT "Country Name", COUNT(DISTINCT "Series Code") AS indicator_count 
FROM debt_data 
GROUP BY "Country Name";

-- 19. Display countries whose total debt is above the global average.
SELECT "Country Name", SUM("Value") AS total_debt 
FROM debt_data 
GROUP BY "Country Name" 
HAVING SUM("Value") > (
    SELECT AVG(country_debt) 
    FROM (SELECT SUM("Value") AS country_debt FROM debt_data GROUP BY "Country Code") AS subquery
);

-- 20. Rank countries based on total debt (highest to lowest).
SELECT "Country Name", SUM("Value") AS total_debt,
       DENSE_RANK() OVER (ORDER BY SUM("Value") DESC) AS debt_rank
FROM debt_data 
GROUP BY "Country Name";


 -----------------------------------------------------------------------------------------
   PART 4: ADVANCED ANALYTICAL QUERIES (21-30)
 ----------------------------------------------------------------------------------------- 
-- 21. Find the top 5 indicators contributing most to global debt.
SELECT "Series Name", SUM("Value") AS total_contribution 
FROM debt_data 
GROUP BY "Series Name" 
ORDER BY total_contribution DESC 
LIMIT 5;

-- 22. Calculate percentage contribution of each country to total global debt.
SELECT "Country Name", SUM("Value") AS country_debt,
       (SUM("Value") / (SELECT SUM("Value") FROM debt_data) * 100) AS percentage_contribution
FROM debt_data 
GROUP BY "Country Name"
ORDER BY percentage_contribution DESC;

-- 23. Identify the top 3 countries for each indicator based on debt.
WITH RankedDebt AS (
    SELECT "Series Name", "Country Name", "Value",
           ROW_NUMBER() OVER (PARTITION BY "Series Name" ORDER BY "Value" DESC) AS rn
    FROM debt_data
)
SELECT "Series Name", "Country Name", "Value"
FROM RankedDebt
WHERE rn <= 3;

-- 24. Find the difference between maximum and minimum debt for each country.
SELECT "Country Name", (MAX("Value") - MIN("Value")) AS debt_variance 
FROM debt_data 
GROUP BY "Country Name";

-- 25. Create a view for the top 10 countries with highest debt.
CREATE OR REPLACE VIEW view_top_10_highest_debt_countries AS
SELECT "Country Name", SUM("Value") AS total_debt 
FROM debt_data 
GROUP BY "Country Name" 
ORDER BY total_debt DESC 
LIMIT 10;

-- 26. Categorize countries into High, Medium, Low Debt based on estimated thresholds.
SELECT "Country Name", SUM("Value") AS total_debt,
       CASE 
           WHEN SUM("Value") > 500000000000 THEN 'High Debt'
           WHEN SUM("Value") BETWEEN 100000000000 AND 500000000000 THEN 'Medium Debt'
           ELSE 'Low Debt'
       END AS debt_category
FROM debt_data 
GROUP BY "Country Name";

-- 27. Use window functions to calculate cumulative debt per country.
SELECT "Country Name", "Series Code", "Value",
       SUM("Value") OVER (PARTITION BY "Country Name" ORDER BY "Value" ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_debt
FROM debt_data;

-- 28. Find indicators where average debt is higher than overall average debt.
SELECT "Series Name", AVG("Value") AS avg_indicator_debt
FROM debt_data
GROUP BY "Series Name"
HAVING AVG("Value") > (SELECT AVG("Value") FROM debt_data);

-- 29. Identify countries contributing more than 5% of global debt.
SELECT "Country Name", SUM("Value") AS total_debt
FROM debt_data
GROUP BY "Country Name"
HAVING (SUM("Value") / (SELECT SUM("Value") FROM debt_data) * 100) > 5.0;

-- 30. Find the most dominant indicator (highest contribution) for each country.
WITH CountryIndicatorMax AS (
    SELECT "Country Name", "Series Name", SUM("Value") AS indicator_total,
           ROW_NUMBER() OVER(PARTITION BY "Country Name" ORDER BY SUM("Value") DESC) as rn
    FROM debt_data
    GROUP BY "Country Name", "Series Name"
)
SELECT "Country Name", "Series Name", indicator_total AS dominant_debt_value
FROM CountryIndicatorMax
WHERE rn = 1;
-- D_GEOGRAPHY: one row per zip prefix. Sources: GEOLOCATION (+ zips used by customers/sellers but absent there).
WITH geo AS (
    SELECT geolocation_zip_code_prefix AS zip,
           lower(trim(strip_accents(geolocation_city))) AS city,
           geolocation_state AS state,
           geolocation_lat AS lat, geolocation_lng AS lng
    FROM {sdl}.GEOLOCATION
), geo_name AS (       -- most frequent (city,state) spelling per zip; deterministic tie-break
    SELECT zip, city, state FROM (SELECT zip, city, state, count(*) n FROM geo GROUP BY ALL)
    QUALIFY row_number() OVER (PARTITION BY zip ORDER BY n DESC, city, state) = 1
), geo_pt AS (         -- median is robust to the stray points outside Brazil present in the source
    SELECT zip, median(lat) AS latitude, median(lng) AS longitude
    FROM geo
    WHERE lat BETWEEN -34 AND 6 AND lng BETWEEN -74 AND -34      -- Brazil bounding box (recommendation)
    GROUP BY zip
), other_zip AS (      -- zips referenced by customers/sellers that have no geolocation row
    SELECT zip, city, state FROM (
        SELECT customer_zip_code_prefix AS zip, lower(trim(strip_accents(customer_city))) AS city, customer_state AS state FROM {sdl}.CUSTOMERS
        UNION ALL
        SELECT seller_zip_code_prefix, lower(trim(strip_accents(seller_city))), seller_state FROM {sdl}.SELLERS)
    WHERE zip NOT IN (SELECT zip FROM geo_name)
    QUALIFY row_number() OVER (PARTITION BY zip ORDER BY city, state) = 1
), u AS (
    SELECT n.zip, n.city, n.state, p.latitude, p.longitude FROM geo_name n LEFT JOIN geo_pt p USING (zip)
    UNION ALL
    SELECT zip, city, state, NULL, NULL FROM other_zip
)
SELECT CAST(zip AS INTEGER)                                        AS zip_code_prefix,
       city,
       state,
       CASE WHEN state IN ('AC','AP','AM','PA','RO','RR','TO') THEN 'North'
            WHEN state IN ('AL','BA','CE','MA','PB','PE','PI','RN','SE') THEN 'Northeast'
            WHEN state IN ('DF','GO','MT','MS') THEN 'Central-West'
            WHEN state IN ('ES','MG','RJ','SP') THEN 'Southeast'
            WHEN state IN ('PR','RS','SC') THEN 'South'
            ELSE 'Unknown' END                                      AS region,
       latitude,
       longitude,
       latitude IS NOT NULL                                         AS has_coordinates
FROM u

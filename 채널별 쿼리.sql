/* Expedia 날자별 예약 건 수 */
SELECT 
    DATE(create_date) AS order_date,
    order_type,
    
    COUNT(*) AS order_count,
    SUM(original_amount)
FROM 
    allmytourdb.order_product
WHERE 
    order_type IN ('expedia', 'expediab2b')
AND 
	 order_product_status IN ( 'confirm' )
GROUP BY 
    DATE(create_date)
ORDER BY 
    order_date DESC
LIMIT 10;


/* hotelbeds 날자별 예약 건 수 */    
SELECT 
    DATE(create_date) AS order_date,
    order_type, 
    COUNT(*) AS order_count,
    SUM(original_amount)
FROM 
    allmytourdb.order_product
WHERE 
    order_type IN ('hotelbeds')
AND 
	 order_product_status IN ( 'confirm' )
GROUP BY 
    DATE(create_date), order_type
ORDER BY 
    order_date DESC
LIMIT 10;

/* Trip 날자별 예약 건 수 */  
SELECT
 DATE(bmo_create_data) AS order_date
, 'TRIP'
, bmo_booking_status
, COUNT(*) AS order_count
, SUM(bmo_tot_amount_after_tax)
FROM allmytourdb.booking_master_offer
WHERE bmo_booking_top_status = 1
AND bmo_booking_status = 'New'
AND bmo_sup_code = 'AMTSUPCT0001'
GROUP BY DATE(bmo_create_data)
ORDER BY bmo_create_data DESC
;

-- Meituan 날자별 누적 예약 상황 
SELECT
 DATE(bmo_create_data) AS order_date
, 'MEITUAN'
, bmo_booking_status
, COUNT(*) AS order_count
, SUM(bmo_tot_amount_after_tax)
FROM allmytourdb.booking_master_offer
WHERE bmo_booking_top_status = 1
AND bmo_sup_code = 'AMTSUPME0003'
AND bmo_booking_status = 'BOOKING'
GROUP BY DATE(bmo_create_data)
ORDER BY bmo_create_data DESC
LIMIT 10;

-- FLIGGY 날자별 누적 예약 상황 
SELECT
 DATE(bmo_create_data) AS order_date
, 'FLIGGY'
, bmo_booking_status
, COUNT(*) AS order_count
, SUM(bmo_tot_amount_after_tax)
FROM allmytourdb.booking_master_offer
WHERE bmo_booking_top_status = 1
AND bmo_booking_status = 'CONFIRMED'
AND bmo_sup_code = 'AMTSUPFL0004'
GROUP BY DATE(bmo_create_data)
ORDER BY bmo_create_data DESC
LIMIT 10;

-- DIDA 날자별 누적 예약 상황 
SELECT
 DATE(bmo_create_data) AS order_date
, 'DIDA'
, bmo_booking_status
, COUNT(*) AS order_count
, SUM(bmo_tot_amount_after_tax)
FROM allmytourdb.booking_master_offer
WHERE bmo_booking_top_status = 1
AND bmo_booking_status = 'Confirmed'
AND bmo_sup_code = 'AMTSUPDI0005'
GROUP BY DATE(bmo_create_data)
ORDER BY bmo_create_data DESC
LIMIT 10;

-- AGODA 날자별 누적 예약 상황 
SELECT
 DATE(bmo_create_data) AS order_date
, 'AGODA'
, bmo_booking_status
, COUNT(*) AS order_count
, SUM(bmo_tot_amount_after_tax)
FROM allmytourdb.booking_master_offer
WHERE bmo_booking_top_status = 1
AND bmo_booking_status = 'BOOKING'
AND bmo_sup_code = 'AMTSUPAG0007'
GROUP BY DATE(bmo_create_data)
ORDER BY bmo_create_data DESC
LIMIT 10
;

-- ELONG 날자별 누적 예약 상황 
SELECT
 DATE(bmo_create_data) AS order_date
, 'ELONG'
, bmo_booking_status
, COUNT(*) AS order_count
, SUM(bmo_tot_amount_after_tax)
FROM allmytourdb.booking_master_offer
WHERE bmo_booking_top_status = 1
AND bmo_booking_status = 'Confirmed'
AND bmo_sup_code = 'AMTSUPEL0009'
GROUP BY DATE(bmo_create_data)
ORDER BY bmo_create_data DESC
LIMIT 10
;

-- PKFare 날자별 누적 예약 상황 
SELECT
 DATE(bmo_create_data) AS order_date
, 'PKFARE'
, bmo_booking_status
, COUNT(*) AS order_count
, SUM(bmo_tot_amount_after_tax)
FROM allmytourdb.booking_master_offer
WHERE bmo_booking_top_status = 1
AND bmo_booking_status = 'BOOKING'
AND bmo_sup_code = 'AMTSUPPK0008'
GROUP BY DATE(bmo_create_data)
ORDER BY bmo_create_data DESC
LIMIT 10
;


-- 다보
SELECT 
    DATE(create_date) AS order_date,
    order_type,
    
    COUNT(*) AS order_count,
    SUM(original_amount)

FROM 
    allmytourdb.order_product
WHERE 
    order_type IN ('dabo')
AND 
	 order_product_status IN ( 'confirm' )
GROUP BY 
    DATE(create_date)
ORDER BY 
    order_date DESC
LIMIT 10;

-- 누아 (nuuaapi)
SELECT 
    DATE(create_date) AS order_date,
    order_type,
    COUNT(*) AS order_count,
    SUM(original_amount)

FROM 
    allmytourdb.order_product
WHERE 
    order_type IN ('nuuaapi')
AND 
	 order_product_status IN ( 'confirm' )
GROUP BY 
    DATE(create_date)
ORDER BY 
    order_date DESC
LIMIT 10;

-- 하이오티 (hiot)
SELECT 
    DATE(create_date) AS order_date,
    order_type,
    COUNT(*) AS order_count,
    SUM(original_amount)

FROM 
    allmytourdb.order_product
WHERE 
    order_type IN ('hiot')
AND 
	 order_product_status IN ( 'confirm' )
GROUP BY 
    DATE(create_date)
ORDER BY 
    order_date DESC
LIMIT 10;


-- 호텔스컴바인 날자별, 클릭대비 예약 전환율 쿼리.
SELECT 
    derived.reg_day,
    SUM(derived.click_count) AS click_count,
    SUM(derived.click_count) * 1400  AS click_amound_KRW,
    SUM(derived.booking_count) AS booking_count,
    ROUND(
        IFNULL(SUM(derived.booking_count) / NULLIF(SUM(derived.click_count), 0), 0) * 100,
        2
    ) AS conversion_rate_percent
FROM (
    -- 클릭 수 집계
    SELECT 
        reg_day,
        COUNT(*) AS click_count,
        0 AS booking_count
    FROM allmytourdb.log_kayak_click_id
    GROUP BY reg_day

    UNION ALL

    -- 예약 수 집계
    SELECT 
        reg_day,
        0 AS click_count,
        COUNT(*) AS booking_count
    FROM allmytourdb.order_product_kayak_mapping
    GROUP BY reg_day
) AS derived
GROUP BY derived.reg_day
ORDER BY derived.reg_day DESC;

-- 전체 total
/*
SELECT
	 DATE(op.create_date) AS DATE,
	 ifnull(op.order_type,'-') as channelName,
    op.order_channel_idx AS channelId,
    cc.code_name AS channel_name,
    count(op.order_channel_idx) AS booking_count
FROM allmytourdb.order_product op
INNER JOIN allmytourdb.common_code cc ON cc.code_id = op.order_channel_idx AND cc.parent_idx = 1
WHERE create_date >= DATE_SUB(DATE(NOW()), INTERVAL 1 DAY) 
    AND create_date < DATE(NOW())
    and op.order_product_status IN ('pending', 'confirmWip', 'confirm')
GROUP BY op.order_channel_idx
ORDER BY booking_count desc
;
*/
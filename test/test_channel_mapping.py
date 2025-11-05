# test_channel_mapping.py
"""채널명 매핑 확인 스크립트"""

from config.configdb import get_db_connection
import pandas as pd

def check_channel_mapping():
    """common_code와 실제 데이터의 채널명 매핑 확인"""
    
    engine = get_db_connection()
    
    print("="*60)
    print("채널명 매핑 확인")
    print("="*60)
    
    # 1. common_code에서 '트립' 관련 채널 확인
    print("\n[1. Common Code에서 '트립' 관련 채널]")
    query1 = """
    SELECT code_id, code_name
    FROM common_code
    WHERE parent_idx = 1
        AND (code_name LIKE '%트립%' OR code_name LIKE '%Trip%')
    ORDER BY code_name
    """
    df1 = pd.read_sql(query1, engine)
    if not df1.empty:
        for _, row in df1.iterrows():
            print(f"  code_id: {row['code_id']}, code_name: {row['code_name']}")
    else:
        print("  없음")
    
    # 2. order_product에서 해당 채널이 실제로 어떤 이름으로 나오는지 확인
    if not df1.empty:
        print("\n[2. Order Product에서 해당 채널의 실제 데이터]")
        code_ids = df1['code_id'].tolist()
        code_ids_str = ','.join([str(cid) for cid in code_ids])
        
        query2 = f"""
        SELECT DISTINCT
            op.order_channel_idx,
            cc.code_name as common_code_name,
            op.order_type,
            COUNT(*) as cnt
        FROM order_product op
        LEFT JOIN common_code cc ON cc.code_id = op.order_channel_idx AND cc.parent_idx = 1
        WHERE op.order_channel_idx IN ({code_ids_str})
            AND op.create_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        GROUP BY op.order_channel_idx, cc.code_name, op.order_type
        ORDER BY cnt DESC
        LIMIT 10
        """
        df2 = pd.read_sql(query2, engine)
        if not df2.empty:
            for _, row in df2.iterrows():
                print(f"  order_channel_idx: {row['order_channel_idx']}, "
                      f"common_code_name: {row['common_code_name']}, "
                      f"order_type: {row['order_type']}, "
                      f"건수: {row['cnt']}")
        else:
            print("  최근 30일 데이터 없음")
    
    # 3. booking_master_offer에서 Trip 채널 확인
    print("\n[3. Booking Master Offer에서 Trip 채널]")
    query3 = """
    SELECT DISTINCT
        bmo_sup_code,
        COUNT(*) as cnt
    FROM booking_master_offer
    WHERE bmo_sup_code = 'AMTSUPCT0001'
        AND bmo_create_data >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
    GROUP BY bmo_sup_code
    """
    df3 = pd.read_sql(query3, engine)
    if not df3.empty:
        for _, row in df3.iterrows():
            print(f"  bmo_sup_code: {row['bmo_sup_code']}, 건수: {row['cnt']}")
    else:
        print("  최근 30일 Trip 데이터 없음")
    
    # 4. 실제 쿼리 결과에서 어떤 채널명이 나오는지 확인
    print("\n[4. 실제 통합 쿼리 결과의 채널명]")
    query4 = """
    WITH all_bookings AS (
        SELECT 
            DATE(op.create_date) as booking_date,
            op.order_num as booking_id,
            op.order_type as channel_code,
            COALESCE(cc.code_name, op.order_type) as channel_name,
            'order_product' as source_table
        FROM order_product op
        LEFT JOIN common_code cc 
            ON cc.code_id = op.order_channel_idx 
            AND cc.parent_idx = 1
        WHERE op.create_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            AND op.create_date < CURDATE()
            AND op.order_product_status = 'confirm'
        
        UNION ALL
        
        SELECT 
            DATE(bmo.bmo_create_data) as booking_date,
            COALESCE(bmo.bmo_bh_no, bmo.bmo_hotelconfirm_no) as booking_id,
            bmo.bmo_sup_code as channel_code,
            CASE bmo.bmo_sup_code
                WHEN 'AMTSUPCT0001' THEN 'Trip'
                WHEN 'AMTSUPME0003' THEN 'Meituan'
                WHEN 'AMTSUPFL0004' THEN 'Fliggy'
                WHEN 'AMTSUPDI0005' THEN 'Dida'
                WHEN 'AMTSUPAG0007' THEN 'Agoda'
                WHEN 'AMTSUPEL0009' THEN 'Elong'
                WHEN 'AMTSUPPK0008' THEN 'PKFare'
                ELSE bmo.bmo_sup_code
            END as channel_name,
            'booking_master_offer' as source_table
        FROM booking_master_offer bmo
        WHERE bmo.bmo_create_data >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            AND bmo.bmo_create_data < CURDATE()
            AND bmo.bmo_booking_top_status = 1
    )
    SELECT DISTINCT
        channel_name,
        channel_code,
        source_table,
        COUNT(*) as cnt
    FROM all_bookings
    WHERE channel_name LIKE '%트립%' OR channel_name LIKE '%Trip%'
    GROUP BY channel_name, channel_code, source_table
    ORDER BY cnt DESC
    """
    df4 = pd.read_sql(query4, engine)
    if not df4.empty:
        for _, row in df4.iterrows():
            print(f"  channel_name: {row['channel_name']}, "
                  f"channel_code: {row['channel_code']}, "
                  f"source_table: {row['source_table']}, "
                  f"건수: {row['cnt']}")
    else:
        print("  최근 30일 Trip 관련 데이터 없음")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    check_channel_mapping()


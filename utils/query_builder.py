# utils/query_builder.py
"""동적 쿼리 생성 모듈"""

import sys
import os
# 프로젝트 루트 디렉토리를 path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from config.channels import CHANNEL_CONFIG, get_channel_status_conditions

def build_integrated_query(start_date, end_date, selected_channels=None):
    """
    통합 쿼리 생성
    
    Args:
        start_date: 시작일 (YYYY-MM-DD)
        end_date: 종료일 (YYYY-MM-DD)
        selected_channels: 선택된 채널 리스트 (None이면 전체)
    
    Returns:
        SQL 쿼리 문자열
    """
    
    # booking_master_offer 상태 조건 생성
    bmo_conditions = []
    for sup_code, config in CHANNEL_CONFIG['booking_master_offer'].items():
        condition = f"(bmo.bmo_sup_code = '{sup_code}' AND bmo.bmo_booking_status = '{config['status']}')"
        bmo_conditions.append(condition)
    bmo_condition_sql = " OR ".join(bmo_conditions)
    
    # CASE WHEN 구문 생성 (채널명 매핑)
    bmo_case_sql = "CASE bmo.bmo_sup_code\n"
    for sup_code, config in CHANNEL_CONFIG['booking_master_offer'].items():
        bmo_case_sql += f"        WHEN '{sup_code}' THEN '{config['name']}'\n"
    bmo_case_sql += "        ELSE bmo.bmo_sup_code\n    END"
    
    # 채널 필터 조건
    channel_filter = ""
    if selected_channels and '전체' not in selected_channels:
        # 선택된 채널명을 코드로 변환
        channel_codes_op = []
        channel_codes_bmo = []
        
        for channel_name in selected_channels:
            # order_product 채널 찾기
            for order_type, config in CHANNEL_CONFIG['order_product'].items():
                if config['name'] == channel_name:
                    channel_codes_op.append(order_type)
            
            # booking_master_offer 채널 찾기
            for sup_code, config in CHANNEL_CONFIG['booking_master_offer'].items():
                if config['name'] == channel_name:
                    channel_codes_bmo.append(sup_code)
        
        # 필터 추가는 각 서브쿼리에서 처리
    
    query = f"""
    WITH all_bookings AS (
        -- order_product 테이블 데이터
        SELECT 
            DATE(op.create_date) as booking_date,
            op.order_num as booking_id,
            op.order_type as channel_code,
            COALESCE(cc.code_name, op.order_type, 
                CASE op.order_type
                    WHEN 'expedia' THEN 'Expedia'
                    WHEN 'expediab2b' THEN 'Expedia B2B'
                    WHEN 'hotelbeds' THEN 'Hotelbeds'
                    WHEN 'dabo' THEN '다보'
                    WHEN 'nuuaapi' THEN '누아'
                    WHEN 'hiot' THEN '하이오티'
                    ELSE op.order_type
                END
            ) as channel_name,
            op.original_amount as amount,
            'order_product' as source_table
        FROM order_product op
        LEFT JOIN common_code cc 
            ON cc.code_id = op.order_channel_idx 
            AND cc.parent_idx = 1
        WHERE op.create_date >= '{start_date}'
            AND op.create_date <= '{end_date} 23:59:59'
            AND op.create_date < CURDATE()
            AND op.order_product_status = 'confirm'
            {'AND op.order_type IN (' + ','.join([f"'{c}'" for c in channel_codes_op]) + ')' if selected_channels and channel_codes_op else ''}
        
        UNION ALL
        
        -- booking_master_offer 테이블 데이터
        SELECT 
            DATE(bmo.bmo_create_data) as booking_date,
            COALESCE(bmo.bmo_bh_no, bmo.bmo_hotelconfirm_no) as booking_id,
            bmo.bmo_sup_code as channel_code,
            {bmo_case_sql} as channel_name,
            bmo.bmo_tot_amount_after_tax as amount,
            'booking_master_offer' as source_table
        FROM booking_master_offer bmo
        WHERE bmo.bmo_create_data >= '{start_date}'
            AND bmo.bmo_create_data <= '{end_date} 23:59:59'
            AND bmo.bmo_create_data < CURDATE()
            AND bmo.bmo_booking_top_status = 1
            AND ({bmo_condition_sql})
            {'AND bmo.bmo_sup_code IN (' + ','.join([f"'{c}'" for c in channel_codes_bmo]) + ')' if selected_channels and channel_codes_bmo else ''}
    )
    SELECT 
        booking_date,
        channel_name,
        channel_code,
        COUNT(DISTINCT booking_id) as booking_count,
        SUM(amount) as total_amount,
        GROUP_CONCAT(DISTINCT source_table) as data_sources
    FROM all_bookings
    WHERE booking_id IS NOT NULL
    GROUP BY booking_date, channel_name, channel_code
    ORDER BY booking_date DESC, booking_count DESC
    """
    
    return query

def build_summary_query(start_date, end_date):
    """
    요약 통계 쿼리 생성
    
    Args:
        start_date: 시작일
        end_date: 종료일
    
    Returns:
        SQL 쿼리 문자열
    """
    
    query = f"""
    SELECT 
        COUNT(DISTINCT order_num) as total_bookings,
        SUM(original_amount) as total_revenue,
        COUNT(DISTINCT order_type) as channel_count,
        COUNT(DISTINCT DATE(create_date)) as active_days
    FROM order_product
    WHERE create_date >= '{start_date}'
        AND create_date <= '{end_date} 23:59:59'
        AND create_date < CURDATE()
        AND order_product_status = 'confirm'
    """
    
    return query

def build_daily_trend_query(start_date, end_date):
    """
    일별 추세 쿼리 생성
    
    Args:
        start_date: 시작일
        end_date: 종료일
    
    Returns:
        SQL 쿼리 문자열
    """
    
    query = f"""
    SELECT 
        DATE(create_date) as date,
        COUNT(DISTINCT order_num) as bookings,
        SUM(original_amount) as revenue
    FROM order_product
    WHERE create_date >= '{start_date}'
        AND create_date <= '{end_date} 23:59:59'
        AND create_date < CURDATE()
        AND order_product_status = 'confirm'
    GROUP BY DATE(create_date)
    ORDER BY date ASC
    """
    
    return query

def build_channel_performance_query(start_date, end_date):
    """
    채널별 성과 쿼리 생성
    """
    
    query = build_integrated_query(start_date, end_date)
    
    # GROUP BY를 채널별로만 수정
    modified_query = query.replace(
        "GROUP BY booking_date, channel_name, channel_code",
        "GROUP BY channel_name, channel_code"
    ).replace(
        "booking_date,",
        ""
    ).replace(
        "ORDER BY booking_date DESC, booking_count DESC",
        "ORDER BY booking_count DESC"
    )
    
    return modified_query

# 테스트 함수
if __name__ == "__main__":
    # 테스트용 날짜
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)
    
    print("="*60)
    print("📝 쿼리 빌더 테스트")
    print("="*60)
    
    # 통합 쿼리 테스트
    query = build_integrated_query(start_date, end_date)
    print(f"\n[통합 쿼리] ({start_date} ~ {end_date})")
    print("-"*40)
    print(query[:500] + "...")
    
    # 특정 채널 필터 테스트
    selected = ['Expedia', 'Trip']
    query2 = build_integrated_query(start_date, end_date, selected)
    print(f"\n[채널 필터 쿼리] (채널: {', '.join(selected)})")
    print("-"*40)
    print(query2[:500] + "...")
    
    print("\n✅ 쿼리 빌더 준비 완료!")
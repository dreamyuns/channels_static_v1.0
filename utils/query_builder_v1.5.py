# utils/query_builder_v1.5.py
"""동적 쿼리 생성 모듈 v1.5 - order_item.due_price 사용 (입금가)"""

import sys
import os
# 프로젝트 루트 디렉토리를 path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from config.order_status_mapping import (
    ORDER_STATUS_GROUPS,
    get_status_codes_by_group,
    get_all_status_codes
)
from config.master_data_loader import get_all_order_status_codes

def build_integrated_query(start_date, end_date, selected_channels=None, 
                          date_type='orderDate', order_status='전체', sale_type='전체'):
    """
    통합 쿼리 생성 (order_product 테이블만 사용, order_pay JOIN 추가)
    v1.5: order_item.due_price 사용 (입금가)
    
    Args:
        start_date: 시작일 (YYYY-MM-DD)
        end_date: 종료일 (YYYY-MM-DD)
        selected_channels: 선택된 채널 리스트 (None이면 전체)
        date_type: 날짜유형 ('useDate', 'orderDate')
        order_status: 예약상태 ('전체', '확정', '취소') - 항상 '전체'로 고정됨
        sale_type: 판매유형 ('전체', 'b2c', 'b2b')
    
    Returns:
        SQL 쿼리 문자열
    """
    
    # 채널 필터 조건 생성
    channel_filter = ""
    if selected_channels and '전체' not in selected_channels:
        # order_type 필터링
        channel_codes = []
        from config.channels import CHANNEL_CONFIG
        for channel_name in selected_channels:
            for order_type, config in CHANNEL_CONFIG['order_product'].items():
                if config['name'] == channel_name:
                    channel_codes.append(order_type)
        
        if channel_codes:
            status_list = ','.join([f"'{c}'" for c in channel_codes])
            channel_filter = f"AND op.order_type IN ({status_list})"
    
    # 판매유형 필터 조건 생성
    sale_type_filter = ""
    if sale_type and sale_type != '전체':
        sale_type_filter = f"AND pr.sale_type = '{sale_type}'"
    
    # 날짜 조건 생성
    date_condition = ""
    if date_type == 'useDate':
        # 이용일 기준
        date_condition = f"op.checkin_date >= '{start_date}' AND op.checkin_date <= '{end_date}'"
        date_field = "DATE(op.checkin_date)"
    else:  # orderDate (기본값)
        # 구매일 기준
        date_condition = f"op.create_date >= '{start_date}' AND op.create_date <= '{end_date} 23:59:59'"
        date_field = "DATE(op.create_date)"
    
    # 예약상태 조건 생성 (항상 '전체'로 고정)
    status_condition = ""
    if order_status == '전체':
        # order_status 시트의 모든 상태값 사용
        all_statuses = get_all_order_status_codes()
        if all_statuses:
            status_list = ','.join([f"'{s}'" for s in all_statuses])
            status_condition = f"AND op.order_product_status IN ({status_list})"
        else:
            # order_status 시트가 없으면 모든 상태 허용
            status_condition = ""
    
    # 확정/취소 상태 리스트 생성
    confirmed_statuses = get_status_codes_by_group('확정')
    cancelled_statuses = get_status_codes_by_group('취소')
    
    confirmed_list = ','.join([f"'{s}'" for s in confirmed_statuses]) if confirmed_statuses else "''"
    cancelled_list = ','.join([f"'{s}'" for s in cancelled_statuses]) if cancelled_statuses else "''"
    
    query = f"""
    SELECT 
        {date_field} as booking_date,
        -- order_channel_idx 기준으로 channel_name 결정 (같은 order_channel_idx는 하나의 channel_name으로 합침)
        COALESCE((
            SELECT cc.code_name 
            FROM common_code cc 
            WHERE cc.code_id = op.order_channel_idx 
                AND cc.parent_idx = 1 
            ORDER BY cc.idx
            LIMIT 1
        ), op.order_type, 
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
        op.order_channel_idx as channel_idx,
        -- channel_code는 참고용으로만 유지 (그룹화에는 사용하지 않음)
        GROUP_CONCAT(DISTINCT op.order_type ORDER BY op.order_type SEPARATOR ', ') as channel_code,
        -- 판매유형 추가
        COALESCE(pr.sale_type, '') as sale_type,
        COUNT(DISTINCT op.order_num) as booking_count,
        COUNT(DISTINCT op.product_name) as hotel_count,
        -- order_item JOIN으로 인한 중복 방지: terms * room_cnt는 order_product에서 직접 계산
        -- order_item JOIN은 입금가 계산에만 사용되므로, terms * room_cnt는 중복되지 않음
        SUM(COALESCE(op.terms, 1) * COALESCE(op.room_cnt, 0)) as total_rooms,
        SUM(CASE 
            WHEN op.order_product_status IN ({confirmed_list}) 
            THEN COALESCE(op.terms, 1) * COALESCE(op.room_cnt, 0) 
            ELSE 0 
        END) as confirmed_rooms,
        SUM(CASE 
            WHEN op.order_product_status IN ({cancelled_list}) 
            THEN COALESCE(op.terms, 1) * COALESCE(op.room_cnt, 0) 
            ELSE 0 
        END) as cancelled_rooms,
        CASE 
            WHEN SUM(COALESCE(op.terms, 1) * COALESCE(op.room_cnt, 0)) = 0 THEN 0
            ELSE (SUM(CASE 
                WHEN op.order_product_status IN ({cancelled_list}) 
                THEN COALESCE(op.terms, 1) * COALESCE(op.room_cnt, 0) 
                ELSE 0 
            END) / SUM(COALESCE(op.terms, 1) * COALESCE(op.room_cnt, 0))) * 100
        END as cancellation_rate,
        -- v1.5: order_item.due_price 사용 (입금가) - due_price 합계 * room_cnt (terms는 곱하지 않음, 이미 날짜별 row로 합산됨)
        SUM(COALESCE((
            SELECT SUM(oi2.due_price)
            FROM order_item oi2
            WHERE oi2.order_product_idx = op.idx
        ), 0) * COALESCE(op.room_cnt, 1)) as total_deposit,
        -- order_pay는 직접 JOIN하여 사용 (1:1 관계이므로 중복 없음)
        SUM(COALESCE(opay.total_amount, 0)) as total_purchase,
        SUM(COALESCE(opay.total_amount, 0)) - SUM(COALESCE((
            SELECT SUM(oi2.due_price)
            FROM order_item oi2
            WHERE oi2.order_product_idx = op.idx
        ), 0) * COALESCE(op.room_cnt, 1)) as total_profit,
        CASE 
            WHEN SUM(COALESCE((
                SELECT SUM(oi2.due_price)
                FROM order_item oi2
                WHERE oi2.order_product_idx = op.idx
            ), 0) * COALESCE(op.room_cnt, 1)) = 0 THEN 0
            ELSE ((SUM(COALESCE(opay.total_amount, 0)) - SUM(COALESCE((
                SELECT SUM(oi2.due_price)
                FROM order_item oi2
                WHERE oi2.order_product_idx = op.idx
            ), 0) * COALESCE(op.room_cnt, 1))) 
                  / SUM(COALESCE((
                SELECT SUM(oi2.due_price)
                FROM order_item oi2
                WHERE oi2.order_product_idx = op.idx
            ), 0) * COALESCE(op.room_cnt, 1))) * 100
        END as profit_rate
    FROM order_product op
    LEFT JOIN order_pay opay 
        ON op.order_pay_idx = opay.idx
    LEFT JOIN product_rateplan pr
        ON op.rateplan_idx = pr.idx
    WHERE {date_condition}
        AND op.create_date < CURDATE()
        {status_condition}
        {channel_filter}
        {sale_type_filter}
    GROUP BY {date_field}, op.order_channel_idx, channel_name, pr.sale_type
    ORDER BY booking_date DESC, booking_count DESC
    """
    
    return query

def build_summary_query(start_date, end_date, date_type='orderDate', order_status='전체', sale_type='전체'):
    """
    요약 통계 쿼리 생성
    
    Args:
        start_date: 시작일
        end_date: 종료일
        date_type: 날짜유형 ('useDate', 'orderDate')
        order_status: 예약상태 (항상 '전체'로 고정)
        sale_type: 판매유형 ('전체', 'b2c', 'b2b')
    
    Returns:
        SQL 쿼리 문자열
    """
    
    # 날짜 조건 (build_integrated_query와 동일한 로직)
    date_condition = ""
    if date_type == 'useDate':
        date_condition = f"op.checkin_date >= '{start_date}' AND op.checkin_date <= '{end_date}'"
    else:  # orderDate
        date_condition = f"op.create_date >= '{start_date}' AND op.create_date <= '{end_date} 23:59:59'"
    
    # 예약상태 조건 (항상 '전체')
    status_condition = ""
    all_statuses = get_all_order_status_codes()
    if all_statuses:
        status_list = ','.join([f"'{s}'" for s in all_statuses])
        status_condition = f"AND op.order_product_status IN ({status_list})"
    
    # 판매유형 필터 조건 생성
    sale_type_filter = ""
    if sale_type and sale_type != '전체':
        sale_type_filter = f"AND pr.sale_type = '{sale_type}'"
    
    query = f"""
    SELECT 
        COUNT(DISTINCT op.order_num) as total_bookings,
        -- v1.5: order_item.due_price 사용 (입금가) - due_price 합계 * room_cnt (terms는 곱하지 않음, 이미 날짜별 row로 합산됨)
        SUM(COALESCE((
            SELECT SUM(oi2.due_price)
            FROM order_item oi2
            WHERE oi2.order_product_idx = op.idx
        ), 0) * COALESCE(op.room_cnt, 1)) as total_revenue,
        COUNT(DISTINCT op.order_type) as channel_count,
        COUNT(DISTINCT CASE 
            WHEN '{date_type}' = 'useDate' THEN DATE(op.checkin_date)
            ELSE DATE(op.create_date)
        END) as active_days
    FROM order_product op
    LEFT JOIN product_rateplan pr
        ON op.rateplan_idx = pr.idx
    WHERE {date_condition}
        AND op.create_date < CURDATE()
        {status_condition}
        {sale_type_filter}
    """
    
    return query

def build_daily_trend_query(start_date, end_date, date_type='orderDate', order_status='전체', sale_type='전체'):
    """
    일별 추세 쿼리 생성
    
    Args:
        start_date: 시작일
        end_date: 종료일
        date_type: 날짜유형
        order_status: 예약상태 (항상 '전체'로 고정)
        sale_type: 판매유형 ('전체', 'b2c', 'b2b')
    
    Returns:
        SQL 쿼리 문자열
    """
    
    # 날짜 조건
    if date_type == 'useDate':
        date_field = "DATE(op.checkin_date)"
        date_condition = f"op.checkin_date >= '{start_date}' AND op.checkin_date <= '{end_date}'"
    else:  # orderDate
        date_field = "DATE(op.create_date)"
        date_condition = f"op.create_date >= '{start_date}' AND op.create_date <= '{end_date} 23:59:59'"
    
    # 예약상태 조건 (항상 '전체')
    status_condition = ""
    all_statuses = get_all_order_status_codes()
    if all_statuses:
        status_list = ','.join([f"'{s}'" for s in all_statuses])
        status_condition = f"AND op.order_product_status IN ({status_list})"
    
    # 판매유형 필터 조건 생성
    sale_type_filter = ""
    if sale_type and sale_type != '전체':
        sale_type_filter = f"AND pr.sale_type = '{sale_type}'"
    
    query = f"""
    SELECT 
        {date_field} as date,
        COUNT(DISTINCT op.order_num) as bookings,
        -- v1.5: order_item.due_price 사용 (입금가) - due_price 합계 * room_cnt (terms는 곱하지 않음, 이미 날짜별 row로 합산됨)
        SUM(COALESCE((
            SELECT SUM(oi2.due_price)
            FROM order_item oi2
            WHERE oi2.order_product_idx = op.idx
        ), 0) * COALESCE(op.room_cnt, 1)) as revenue
    FROM order_product op
    LEFT JOIN product_rateplan pr
        ON op.rateplan_idx = pr.idx
    WHERE {date_condition}
        AND op.create_date < CURDATE()
        {status_condition}
        {sale_type_filter}
    GROUP BY {date_field}
    ORDER BY date ASC
    """
    
    return query

def build_channel_performance_query(start_date, end_date, date_type='orderDate', order_status='전체', sale_type='전체'):
    """
    채널별 성과 쿼리 생성
    """
    
    query = build_integrated_query(start_date, end_date, None, date_type, order_status, sale_type)
    
    # GROUP BY를 채널별로만 수정
    modified_query = query.replace(
        "GROUP BY booking_date, channel_name, channel_code",
        "GROUP BY channel_name, channel_code"
    ).replace(
        "booking_date, ",
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
    print("📝 쿼리 빌더 테스트 v1.5")
    print("="*60)
    
    # 통합 쿼리 테스트
    print(f"\n[통합 쿼리] ({start_date} ~ {end_date})")
    print("- 날짜유형: 구매일, 예약상태: 전체")
    query = build_integrated_query(start_date, end_date, None, 'orderDate', '전체')
    print(query[:800] + "...")
    
    print("\n✅ 쿼리 빌더 v1.5 준비 완료!")


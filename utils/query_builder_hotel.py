# utils/query_builder_hotel.py
"""숙소별 통계 쿼리 생성 모듈
- 날짜별 + 숙소별 + 채널별 집계
- order_item.due_price 사용 (입금가)
- product 테이블 JOIN
"""

import sys
import os
# 프로젝트 루트 디렉토리를 path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from config.order_status_mapping import (
    get_status_codes_by_group,
    get_all_status_codes
)
from config.master_data_loader import get_all_order_status_codes


def build_hotel_statistics_query(start_date, end_date, selected_hotel_ids=None,
                                 date_type='orderDate', order_status='전체', sale_type='전체'):
    """
    숙소별 통계 쿼리 생성
    날짜별 + 숙소별 + 채널별 집계
    
    Args:
        start_date: 시작일 (YYYY-MM-DD)
        end_date: 종료일 (YYYY-MM-DD)
        selected_hotel_ids: 선택된 숙소 ID 리스트 (None이면 전체)
        date_type: 날짜유형 ('useDate', 'orderDate')
        order_status: 예약상태 (항상 '전체'로 고정)
        sale_type: 판매유형 ('전체', 'b2c', 'b2b')
    
    Returns:
        SQL 쿼리 문자열
    """
    
    # 숙소 필터 조건 생성
    hotel_filter = ""
    if selected_hotel_ids and len(selected_hotel_ids) > 0:
        hotel_ids_str = ','.join([str(hid) for hid in selected_hotel_ids])
        hotel_filter = f"AND op.product_idx IN ({hotel_ids_str})"
    
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
        all_statuses = get_all_order_status_codes()
        if all_statuses:
            status_list = ','.join([f"'{s}'" for s in all_statuses])
            status_condition = f"AND op.order_product_status IN ({status_list})"
        else:
            status_condition = ""
    
    # 확정/취소 상태 리스트 생성
    confirmed_statuses = get_status_codes_by_group('확정')
    cancelled_statuses = get_status_codes_by_group('취소')
    
    confirmed_list = ','.join([f"'{s}'" for s in confirmed_statuses]) if confirmed_statuses else "''"
    cancelled_list = ','.join([f"'{s}'" for s in cancelled_statuses]) if cancelled_statuses else "''"
    
    query = f"""
    SELECT 
        {date_field} as booking_date,
        p.name_kr as hotel_name,
        p.idx as hotel_idx,
        p.product_code as hotel_code,
        -- order_channel_idx 기준으로 channel_name 결정
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
        GROUP_CONCAT(DISTINCT op.order_type ORDER BY op.order_type SEPARATOR ', ') as channel_code,
        -- 판매유형 추가
        COALESCE(pr.sale_type, '') as sale_type,
        COUNT(DISTINCT op.order_num) as booking_count,
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
        -- order_item.due_price 사용 (입금가) - due_price 합계 * room_cnt
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
    LEFT JOIN product p ON op.product_idx = p.idx
    LEFT JOIN order_pay opay 
        ON op.order_pay_idx = opay.idx
    LEFT JOIN product_rateplan pr
        ON op.rateplan_idx = pr.idx
    WHERE {date_condition}
        AND op.create_date < CURDATE()
        {status_condition}
        {hotel_filter}
        {sale_type_filter}
    GROUP BY {date_field}, p.idx, p.name_kr, p.product_code, op.order_channel_idx, channel_name, pr.sale_type
    ORDER BY booking_date DESC, hotel_name ASC, channel_name ASC
    """
    
    return query


def build_hotel_summary_query(start_date, end_date, selected_hotel_ids=None,
                              date_type='orderDate', order_status='전체', sale_type='전체'):
    """
    숙소별 요약 통계 쿼리 생성
    
    Args:
        start_date: 시작일
        end_date: 종료일
        selected_hotel_ids: 선택된 숙소 ID 리스트
        date_type: 날짜유형
        order_status: 예약상태 (항상 '전체'로 고정)
        sale_type: 판매유형 ('전체', 'b2c', 'b2b')
    
    Returns:
        SQL 쿼리 문자열
    """
    
    # 날짜 조건
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
    
    # 숙소 필터
    hotel_filter = ""
    if selected_hotel_ids and len(selected_hotel_ids) > 0:
        hotel_ids_str = ','.join([str(hid) for hid in selected_hotel_ids])
        hotel_filter = f"AND op.product_idx IN ({hotel_ids_str})"
    
    # 판매유형 필터 조건 생성
    sale_type_filter = ""
    if sale_type and sale_type != '전체':
        sale_type_filter = f"AND pr.sale_type = '{sale_type}'"
    
    query = f"""
    SELECT 
        COUNT(DISTINCT op.order_num) as total_bookings,
        SUM(COALESCE((
            SELECT SUM(oi2.due_price)
            FROM order_item oi2
            WHERE oi2.order_product_idx = op.idx
        ), 0) * COALESCE(op.room_cnt, 1)) as total_revenue,
        COUNT(DISTINCT op.product_idx) as hotel_count,
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
        {hotel_filter}
        {sale_type_filter}
    """
    
    return query


# 테스트 함수
if __name__ == "__main__":
    # 테스트용 날짜
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)
    
    print("="*60)
    print("📝 숙소별 통계 쿼리 빌더 테스트")
    print("="*60)
    
    # 테스트 1: 기본 쿼리
    print(f"\n[테스트 1] 기본 쿼리 ({start_date} ~ {end_date})")
    print("- 날짜유형: 구매일, 예약상태: 전체")
    query = build_hotel_statistics_query(start_date, end_date, None, 'orderDate', '전체')
    print(query[:500] + "...")
    
    # 테스트 2: 숙소 필터 포함
    print(f"\n[테스트 2] 숙소 필터 포함")
    print("- 숙소 ID: [1, 2, 3]")
    query = build_hotel_statistics_query(start_date, end_date, [1, 2, 3], 'orderDate', '전체')
    print(query[:500] + "...")
    
    # 테스트 3: 요약 통계 쿼리
    print(f"\n[테스트 3] 요약 통계 쿼리")
    query = build_hotel_summary_query(start_date, end_date, [1, 2, 3], 'orderDate', '전체')
    print(query)
    
    print("\n✅ 숙소별 통계 쿼리 빌더 준비 완료!")


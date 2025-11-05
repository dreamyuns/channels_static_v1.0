# utils/query_builder_v1.1.py
"""동적 쿼리 생성 모듈 v1.1 - order_product 테이블만 사용, 날짜유형/예약상태 필터 추가"""

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
                          date_type='전체', order_status='전체'):
    """
    통합 쿼리 생성 (order_product 테이블만 사용)
    
    Args:
        start_date: 시작일 (YYYY-MM-DD)
        end_date: 종료일 (YYYY-MM-DD)
        selected_channels: 선택된 채널 리스트 (None이면 전체)
        date_type: 날짜유형 ('전체', 'useDate', 'orderDate')
        order_status: 예약상태 ('전체', '확정', '취소')
    
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
    
    # 날짜 조건 생성
    date_condition = ""
    if date_type == '전체':
        # OR 조건: 이용일 또는 구매일 중 하나라도 범위 안에 있으면
        date_condition = f"""(
            (op.checkin_date >= '{start_date}' AND op.checkin_date <= '{end_date}')
            OR 
            (op.create_date >= '{start_date}' AND op.create_date <= '{end_date} 23:59:59')
        )"""
    elif date_type == 'useDate':
        # 이용일 기준
        date_condition = f"op.checkin_date >= '{start_date}' AND op.checkin_date <= '{end_date}'"
    elif date_type == 'orderDate':
        # 구매일 기준
        date_condition = f"op.create_date >= '{start_date}' AND op.create_date <= '{end_date} 23:59:59'"
    else:
        # 기본값: 구매일
        date_condition = f"op.create_date >= '{start_date}' AND op.create_date <= '{end_date} 23:59:59'"
    
    # 예약상태 조건 생성
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
    elif order_status == '확정':
        # 확정 그룹의 모든 상태값
        confirmed_statuses = get_status_codes_by_group('확정')
        if confirmed_statuses:
            status_list = ','.join([f"'{s}'" for s in confirmed_statuses])
            status_condition = f"AND op.order_product_status IN ({status_list})"
    elif order_status == '취소':
        # 취소 그룹의 모든 상태값
        cancelled_statuses = get_status_codes_by_group('취소')
        if cancelled_statuses:
            status_list = ','.join([f"'{s}'" for s in cancelled_statuses])
            status_condition = f"AND op.order_product_status IN ({status_list})"
    
    # 날짜 기준 결정 (결과 표시용)
    if date_type == '전체':
        # 전체일 때는 create_date 기준으로 표시 (기존 로직 유지)
        date_field = "DATE(op.create_date)"
    elif date_type == 'useDate':
        date_field = "DATE(op.checkin_date)"
    else:  # orderDate
        date_field = "DATE(op.create_date)"
    
    query = f"""
    SELECT 
        {date_field} as booking_date,
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
        op.order_type as channel_code,
        COUNT(DISTINCT op.order_num) as booking_count,
        SUM(op.original_amount) as total_amount,
        'order_product' as data_sources
    FROM order_product op
    LEFT JOIN common_code cc 
        ON cc.code_id = op.order_channel_idx 
        AND cc.parent_idx = 1
    WHERE {date_condition}
        AND op.create_date < CURDATE()
        {status_condition}
        {channel_filter}
    GROUP BY {date_field}, channel_name, channel_code
    ORDER BY booking_date DESC, booking_count DESC
    """
    
    return query

def build_summary_query(start_date, end_date, date_type='전체', order_status='전체'):
    """
    요약 통계 쿼리 생성
    
    Args:
        start_date: 시작일
        end_date: 종료일
        date_type: 날짜유형
        order_status: 예약상태
    
    Returns:
        SQL 쿼리 문자열
    """
    
    # 날짜 조건 (build_integrated_query와 동일한 로직)
    date_condition = ""
    if date_type == '전체':
        date_condition = f"""(
            (op.checkin_date >= '{start_date}' AND op.checkin_date <= '{end_date}')
            OR 
            (op.create_date >= '{start_date}' AND op.create_date <= '{end_date} 23:59:59')
        )"""
    elif date_type == 'useDate':
        date_condition = f"op.checkin_date >= '{start_date}' AND op.checkin_date <= '{end_date}'"
    else:  # orderDate
        date_condition = f"op.create_date >= '{start_date}' AND op.create_date <= '{end_date} 23:59:59'"
    
    # 예약상태 조건 (build_integrated_query와 동일한 로직)
    status_condition = ""
    if order_status == '전체':
        all_statuses = get_all_order_status_codes()
        if all_statuses:
            status_list = ','.join([f"'{s}'" for s in all_statuses])
            status_condition = f"AND op.order_product_status IN ({status_list})"
    elif order_status == '확정':
        confirmed_statuses = get_status_codes_by_group('확정')
        if confirmed_statuses:
            status_list = ','.join([f"'{s}'" for s in confirmed_statuses])
            status_condition = f"AND op.order_product_status IN ({status_list})"
    elif order_status == '취소':
        cancelled_statuses = get_status_codes_by_group('취소')
        if cancelled_statuses:
            status_list = ','.join([f"'{s}'" for s in cancelled_statuses])
            status_condition = f"AND op.order_product_status IN ({status_list})"
    
    query = f"""
    SELECT 
        COUNT(DISTINCT op.order_num) as total_bookings,
        SUM(op.original_amount) as total_revenue,
        COUNT(DISTINCT op.order_type) as channel_count,
        COUNT(DISTINCT DATE(op.create_date)) as active_days
    FROM order_product op
    WHERE {date_condition}
        AND op.create_date < CURDATE()
        {status_condition}
    """
    
    return query

def build_daily_trend_query(start_date, end_date, date_type='전체', order_status='전체'):
    """
    일별 추세 쿼리 생성
    
    Args:
        start_date: 시작일
        end_date: 종료일
        date_type: 날짜유형
        order_status: 예약상태
    
    Returns:
        SQL 쿼리 문자열
    """
    
    # 날짜 조건
    if date_type == 'useDate':
        date_field = "DATE(op.checkin_date)"
        date_condition = f"op.checkin_date >= '{start_date}' AND op.checkin_date <= '{end_date}'"
    else:  # orderDate 또는 전체
        date_field = "DATE(op.create_date)"
        date_condition = f"op.create_date >= '{start_date}' AND op.create_date <= '{end_date} 23:59:59'"
    
    # 예약상태 조건
    status_condition = ""
    if order_status == '전체':
        all_statuses = get_all_order_status_codes()
        if all_statuses:
            status_list = ','.join([f"'{s}'" for s in all_statuses])
            status_condition = f"AND op.order_product_status IN ({status_list})"
    elif order_status == '확정':
        confirmed_statuses = get_status_codes_by_group('확정')
        if confirmed_statuses:
            status_list = ','.join([f"'{s}'" for s in confirmed_statuses])
            status_condition = f"AND op.order_product_status IN ({status_list})"
    elif order_status == '취소':
        cancelled_statuses = get_status_codes_by_group('취소')
        if cancelled_statuses:
            status_list = ','.join([f"'{s}'" for s in cancelled_statuses])
            status_condition = f"AND op.order_product_status IN ({status_list})"
    
    query = f"""
    SELECT 
        {date_field} as date,
        COUNT(DISTINCT op.order_num) as bookings,
        SUM(op.original_amount) as revenue
    FROM order_product op
    WHERE {date_condition}
        AND op.create_date < CURDATE()
        {status_condition}
    GROUP BY {date_field}
    ORDER BY date ASC
    """
    
    return query

def build_channel_performance_query(start_date, end_date, date_type='전체', order_status='전체'):
    """
    채널별 성과 쿼리 생성
    """
    
    query = build_integrated_query(start_date, end_date, None, date_type, order_status)
    
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
    print("📝 쿼리 빌더 테스트 v1.1")
    print("="*60)
    
    # 통합 쿼리 테스트
    print(f"\n[통합 쿼리] ({start_date} ~ {end_date})")
    print("- 날짜유형: 전체, 예약상태: 전체")
    query = build_integrated_query(start_date, end_date, None, '전체', '전체')
    print(query[:500] + "...")
    
    # 날짜유형 필터 테스트
    print(f"\n[날짜유형 필터] useDate")
    query2 = build_integrated_query(start_date, end_date, None, 'useDate', '전체')
    print(query2[:300] + "...")
    
    # 예약상태 필터 테스트
    print(f"\n[예약상태 필터] 확정")
    query3 = build_integrated_query(start_date, end_date, None, '전체', '확정')
    print(query3[:300] + "...")
    
    print("\n✅ 쿼리 빌더 v1.1 준비 완료!")


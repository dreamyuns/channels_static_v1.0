# utils/data_fetcher_hotel.py
"""숙소별 데이터 조회 및 처리 함수
- 날짜별 + 숙소별 + 채널별 집계
- order_item.due_price 사용 (입금가)
"""

import sys
import os
# 프로젝트 루트 디렉토리를 path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from sqlalchemy import text
from config.configdb import get_db_connection
# 점이 있는 파일명은 직접 import 불가하므로 importlib 사용
import importlib.util
_query_builder_path = os.path.join(os.path.dirname(__file__), 'query_builder_hotel.py')
spec = importlib.util.spec_from_file_location("query_builder_hotel", _query_builder_path)
query_builder_hotel = importlib.util.module_from_spec(spec)
sys.modules["query_builder_hotel"] = query_builder_hotel
spec.loader.exec_module(query_builder_hotel)

from query_builder_hotel import (  # type: ignore
    build_hotel_statistics_query,
    build_hotel_summary_query
)


def fetch_hotel_data(start_date, end_date, selected_hotel_ids=None,
                     date_type='orderDate', order_status='전체', sale_type='전체'):
    """
    숙소별 예약 데이터 조회
    날짜별 + 숙소별 + 채널별 집계
    
    Args:
        start_date: 시작일
        end_date: 종료일  
        selected_hotel_ids: 선택된 숙소 ID 리스트 (None이면 전체)
        date_type: 날짜유형 ('useDate', 'orderDate')
        order_status: 예약상태 (항상 '전체'로 고정)
        sale_type: 판매유형 ('전체', 'b2c', 'b2b')
    
    Returns:
        pandas DataFrame
    """
    try:
        engine = get_db_connection()
        
        # 쿼리 실행 (order_status는 항상 '전체'로 고정)
        query = build_hotel_statistics_query(
            start_date, 
            end_date, 
            selected_hotel_ids=selected_hotel_ids,
            date_type=date_type,
            order_status='전체',  # 항상 '전체'로 고정
            sale_type=sale_type
        )
        
        df = pd.read_sql(query, engine)
        
        # 데이터 타입 정리
        if not df.empty:
            df['booking_date'] = pd.to_datetime(df['booking_date'])
            df['hotel_idx'] = df['hotel_idx'].astype(int)
            df['booking_count'] = df['booking_count'].astype(int)
            df['total_rooms'] = df['total_rooms'].fillna(0).astype(int)
            df['confirmed_rooms'] = df['confirmed_rooms'].fillna(0).astype(int)
            df['cancelled_rooms'] = df['cancelled_rooms'].fillna(0).astype(int)
            df['cancellation_rate'] = df['cancellation_rate'].fillna(0).round(1)  # 소수점 1자리
            df['total_deposit'] = df['total_deposit'].fillna(0).round(0).astype(int)
            df['total_purchase'] = df['total_purchase'].fillna(0).round(0).astype(int)
            df['total_profit'] = df['total_profit'].fillna(0).round(0).astype(int)
            df['profit_rate'] = df['profit_rate'].fillna(0).round(1)  # 소수점 1자리
        
        return df
        
    except Exception as e:
        print(f"❌ 숙소별 데이터 조회 오류: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()


def fetch_hotel_summary_stats(start_date, end_date, selected_hotel_ids=None,
                              date_type='orderDate', order_status='전체', sale_type='전체'):
    """
    숙소별 요약 통계 조회
    
    Args:
        start_date: 시작일
        end_date: 종료일
        selected_hotel_ids: 선택된 숙소 ID 리스트
        date_type: 날짜유형
        order_status: 예약상태 (항상 '전체'로 고정)
        sale_type: 판매유형 ('전체', 'b2c', 'b2b')
    
    Returns:
        dict: 요약 통계 정보
    """
    try:
        engine = get_db_connection()
        query = build_hotel_summary_query(
            start_date, 
            end_date, 
            selected_hotel_ids=selected_hotel_ids,
            date_type=date_type, 
            order_status='전체',  # 항상 '전체'
            sale_type=sale_type
        )
        
        df = pd.read_sql(query, engine)
        
        if not df.empty:
            return {
                'total_bookings': int(df.iloc[0]['total_bookings'] or 0),
                'total_revenue': float(df.iloc[0]['total_revenue'] or 0),
                'hotel_count': int(df.iloc[0]['hotel_count'] or 0),
                'active_days': int(df.iloc[0]['active_days'] or 0)
            }
        
        return {
            'total_bookings': 0,
            'total_revenue': 0,
            'hotel_count': 0,
            'active_days': 0
        }
        
    except Exception as e:
        print(f"❌ 숙소별 요약 통계 조회 오류: {e}")
        return {
            'total_bookings': 0,
            'total_revenue': 0,
            'hotel_count': 0,
            'active_days': 0
        }


# 테스트 함수
if __name__ == "__main__":
    from datetime import datetime, timedelta
    
    print("="*60)
    print("📊 숙소별 데이터 조회 테스트")
    print("="*60)
    
    # 테스트 날짜 설정
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)
    
    print(f"\n기간: {start_date} ~ {end_date}")
    print("-"*40)
    
    # 1. 요약 통계
    print("\n[1. 요약 통계] - 날짜유형: 구매일")
    stats = fetch_hotel_summary_stats(start_date, end_date, None, 'orderDate', '전체')
    for key, value in stats.items():
        print(f"  - {key}: {value:,}")
    
    # 2. 숙소별 데이터
    print("\n[2. 숙소별 예약 데이터] - 날짜유형: 구매일")
    df = fetch_hotel_data(start_date, end_date, None, 'orderDate', '전체')
    if not df.empty:
        print(f"  조회 결과: {len(df)}개 레코드")
        print(f"  숙소 수: {df['hotel_name'].nunique()}개")
        print(f"  채널 수: {df['channel_name'].nunique()}개")
        print(f"  총 예약: {df['booking_count'].sum():,}건")
        print(f"  총 객실수: {df['total_rooms'].sum():,}개")
        print(f"  확정 객실수: {df['confirmed_rooms'].sum():,}개")
        print(f"  취소 객실수: {df['cancelled_rooms'].sum():,}개")
        print(f"  컬럼: {df.columns.tolist()}")
        print("\n  상위 5개 샘플:")
        print(df.head(5).to_string())
    else:
        print("  데이터 없음")
    
    print("\n✅ 숙소별 데이터 조회 테스트 완료!")


# utils/data_fetcher_v1.3.py
"""데이터 조회 및 처리 함수 v1.3 - terms*room_cnt, 확정/취소 객실수, 취소율 지원"""

import sys
import os
# 프로젝트 루트 디렉토리를 path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from sqlalchemy import text
from config.configdb import get_db_connection
# 점이 있는 파일명은 직접 import 불가하므로 importlib 사용
import importlib.util
_query_builder_path = os.path.join(os.path.dirname(__file__), 'query_builder_v1.3.py')
spec = importlib.util.spec_from_file_location("query_builder_v1_3", _query_builder_path)
query_builder_v1_3 = importlib.util.module_from_spec(spec)
sys.modules["query_builder_v1_3"] = query_builder_v1_3
spec.loader.exec_module(query_builder_v1_3)

from query_builder_v1_3 import (  # type: ignore
    build_integrated_query, 
    build_summary_query,
    build_daily_trend_query,
    build_channel_performance_query
)

def fetch_channel_data(start_date, end_date, selected_channels=None,
                      date_type='orderDate', order_status='전체'):
    """
    채널별 예약 데이터 조회
    
    Args:
        start_date: 시작일
        end_date: 종료일  
        selected_channels: 선택된 채널 리스트
        date_type: 날짜유형 ('useDate', 'orderDate')
        order_status: 예약상태 (항상 '전체'로 고정)
    
    Returns:
        pandas DataFrame
    """
    try:
        engine = get_db_connection()
        
        # 채널명 매핑: master_data.xlsx와 common_code를 활용한 정확한 매핑
        valid_channel_names = set()
        if selected_channels and '전체' not in selected_channels:
            # master_data.xlsx의 매핑 데이터 로드
            try:
                from config.channel_mapping import load_master_data_mapping, get_channel_ids_by_name
                channel_id_to_name, channel_name_to_ids = load_master_data_mapping()
            except:
                channel_id_to_name = {}
                channel_name_to_ids = {}
            
            # 1. common_code에서 선택된 채널의 code_name과 code_id 가져오기
            query_mapping = """
            SELECT 
                cc.code_name,
                cc.code_id
            FROM common_code cc
            WHERE cc.parent_idx = 1
                AND cc.code_name IN ({})
            """.format(','.join([f"'{c}'" for c in selected_channels]))
            
            try:
                df_mapping = pd.read_sql(query_mapping, engine)
                if not df_mapping.empty:
                    valid_channel_names.update(df_mapping['code_name'].tolist())
                    
                    # master_data.xlsx의 매핑을 활용하여 추가 채널명 찾기
                    for _, row in df_mapping.iterrows():
                        code_id = row['code_id']
                        code_name = row['code_name']
                        if code_id in channel_id_to_name:
                            master_name = channel_id_to_name[code_id]
                            if master_name != code_name:
                                valid_channel_names.add(master_name)
            except:
                pass
            
            # 2. channels.py의 채널명 추가
            from config.channels import CHANNEL_CONFIG
            for config in CHANNEL_CONFIG['order_product'].values():
                if config['name'] in selected_channels:
                    valid_channel_names.add(config['name'])
            
            # 3. 선택된 채널명 자체도 추가
            valid_channel_names.update(selected_channels)
        
        # 쿼리 실행 (order_status는 항상 '전체'로 고정)
        query = build_integrated_query(
            start_date, 
            end_date, 
            selected_channels=None,  # 쿼리 내에서 필터링
            date_type=date_type,
            order_status='전체'  # 항상 '전체'로 고정
        )
        
        df = pd.read_sql(query, engine)
        
        # 데이터 타입 정리
        if not df.empty:
            df['booking_date'] = pd.to_datetime(df['booking_date'])
            df['booking_count'] = df['booking_count'].astype(int)
            df['hotel_count'] = df['hotel_count'].astype(int)
            df['total_rooms'] = df['total_rooms'].fillna(0).astype(int)
            df['confirmed_rooms'] = df['confirmed_rooms'].fillna(0).astype(int)
            df['cancelled_rooms'] = df['cancelled_rooms'].fillna(0).astype(int)
            df['cancellation_rate'] = df['cancellation_rate'].fillna(0).round(1)  # 소수점 1자리
            df['total_deposit'] = df['total_deposit'].fillna(0).round(0).astype(int)
            df['total_purchase'] = df['total_purchase'].fillna(0).round(0).astype(int)
            df['total_profit'] = df['total_profit'].fillna(0).round(0).astype(int)
            df['profit_rate'] = df['profit_rate'].fillna(0).round(1)  # 소수점 1자리
            
            # 채널 필터링 (선택된 채널이 있고 '전체'가 아닌 경우)
            if selected_channels and '전체' not in selected_channels and valid_channel_names:
                df = df[df['channel_name'].isin(valid_channel_names)]
        
        return df
        
    except Exception as e:
        print(f"❌ 데이터 조회 오류: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

def fetch_summary_stats(start_date, end_date, date_type='orderDate', order_status='전체'):
    """
    요약 통계 조회
    
    Args:
        start_date: 시작일
        end_date: 종료일
        date_type: 날짜유형
        order_status: 예약상태 (항상 '전체'로 고정)
    
    Returns:
        dict: 요약 통계 정보
    """
    try:
        engine = get_db_connection()
        query = build_summary_query(start_date, end_date, date_type, '전체')  # 항상 '전체'
        
        df = pd.read_sql(query, engine)
        
        if not df.empty:
            return {
                'total_bookings': int(df.iloc[0]['total_bookings'] or 0),
                'total_revenue': float(df.iloc[0]['total_revenue'] or 0),
                'channel_count': int(df.iloc[0]['channel_count'] or 0),
                'active_days': int(df.iloc[0]['active_days'] or 0)
            }
        
        return {
            'total_bookings': 0,
            'total_revenue': 0,
            'channel_count': 0,
            'active_days': 0
        }
        
    except Exception as e:
        print(f"❌ 요약 통계 조회 오류: {e}")
        return {
            'total_bookings': 0,
            'total_revenue': 0,
            'channel_count': 0,
            'active_days': 0
        }

def fetch_daily_trend(start_date, end_date, date_type='orderDate', order_status='전체'):
    """
    일별 추세 데이터 조회
    
    Args:
        start_date: 시작일
        end_date: 종료일
        date_type: 날짜유형
        order_status: 예약상태 (항상 '전체'로 고정)
    
    Returns:
        pandas DataFrame
    """
    try:
        engine = get_db_connection()
        query = build_daily_trend_query(start_date, end_date, date_type, '전체')  # 항상 '전체'
        
        df = pd.read_sql(query, engine)
        
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df['revenue'] = df['revenue'].fillna(0).round(0).astype(int)
        
        return df
        
    except Exception as e:
        print(f"❌ 일별 추세 조회 오류: {e}")
        return pd.DataFrame()

def fetch_channel_list():
    """
    사용 가능한 채널 목록 조회
    common_code 테이블에서 parent_idx=1인 채널 목록을 가져옴
    
    Returns:
        list: 채널명 리스트
    """
    import time
    max_retries = 3
    retry_delay = 2  # 초
    
    for attempt in range(max_retries):
        try:
            engine = get_db_connection()
            
            # common_code 테이블에서 채널 목록 조회 (parent_idx = 1)
            query = """
            SELECT DISTINCT
                cc.code_name as channel_name,
                cc.code_id as channel_id
            FROM common_code cc
            WHERE cc.parent_idx = 1
                AND cc.code_name IS NOT NULL
                AND cc.code_name != ''
            ORDER BY cc.code_name
            """
            
            df = pd.read_sql(query, engine)
            
            channels = ['전체']
            
            if not df.empty:
                channels.extend(df['channel_name'].tolist())
            
            # order_product 채널도 추가 (common_code에 없을 수 있음)
            from config.channels import CHANNEL_CONFIG
            for config in CHANNEL_CONFIG['order_product'].values():
                channel_name = config['name']
                if channel_name not in channels:
                    channels.append(channel_name)
            
            # 중복 제거 및 정렬
            channels = ['전체'] + sorted(list(set(channels[1:])))
            
            return channels
            
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"⚠️ 채널 목록 조회 시도 {attempt + 1}/{max_retries} 실패, {retry_delay}초 후 재시도...")
                time.sleep(retry_delay)
                continue
            else:
                print(f"❌ 채널 목록 조회 오류 (최대 재시도 횟수 초과): {e}")
                # 오류 시 기본 채널 목록 반환
                from config.channels import get_all_channel_names
                return ['전체'] + get_all_channel_names()

def fetch_channel_performance(start_date, end_date, date_type='orderDate', order_status='전체'):
    """
    채널별 성과 데이터 조회
    
    Args:
        start_date: 시작일
        end_date: 종료일
        date_type: 날짜유형
        order_status: 예약상태 (항상 '전체'로 고정)
    
    Returns:
        pandas DataFrame
    """
    try:
        engine = get_db_connection()
        query = build_channel_performance_query(start_date, end_date, date_type, '전체')  # 항상 '전체'
        
        df = pd.read_sql(query, engine)
        
        if not df.empty:
            df['total_rooms'] = df['total_rooms'].fillna(0).astype(int)
            df['confirmed_rooms'] = df['confirmed_rooms'].fillna(0).astype(int)
            df['cancelled_rooms'] = df['cancelled_rooms'].fillna(0).astype(int)
            df['cancellation_rate'] = df['cancellation_rate'].fillna(0).round(1)
            df['total_deposit'] = df['total_deposit'].fillna(0).round(0).astype(int)
            df['total_purchase'] = df['total_purchase'].fillna(0).round(0).astype(int)
            df['total_profit'] = df['total_profit'].fillna(0).round(0).astype(int)
            df['profit_rate'] = df['profit_rate'].fillna(0).round(1)
            
        return df
        
    except Exception as e:
        print(f"❌ 채널별 성과 조회 오류: {e}")
        return pd.DataFrame()

# 테스트 함수
if __name__ == "__main__":
    from datetime import datetime, timedelta
    
    print("="*60)
    print("📊 데이터 조회 테스트 v1.3")
    print("="*60)
    
    # 테스트 날짜 설정
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)
    
    print(f"\n기간: {start_date} ~ {end_date}")
    print("-"*40)
    
    # 1. 채널 목록 조회
    print("\n[1. 채널 목록]")
    channels = fetch_channel_list()
    print(f"사용 가능한 채널 ({len(channels)}개): {', '.join(channels[:5])}...")
    
    # 2. 요약 통계
    print("\n[2. 요약 통계] - 날짜유형: 구매일")
    stats = fetch_summary_stats(start_date, end_date, 'orderDate', '전체')
    for key, value in stats.items():
        print(f"  - {key}: {value:,}")
    
    # 3. 채널별 데이터
    print("\n[3. 채널별 예약 데이터] - 날짜유형: 구매일")
    df = fetch_channel_data(start_date, end_date, None, 'orderDate', '전체')
    if not df.empty:
        print(f"  조회 결과: {len(df)}개 레코드")
        print(f"  채널 수: {df['channel_name'].nunique()}개")
        print(f"  총 예약: {df['booking_count'].sum():,}건")
        print(f"  총 객실수: {df['total_rooms'].sum():,}개")
        print(f"  확정 객실수: {df['confirmed_rooms'].sum():,}개")
        print(f"  취소 객실수: {df['cancelled_rooms'].sum():,}개")
        print(f"  컬럼: {df.columns.tolist()}")
    else:
        print("  데이터 없음")
    
    print("\n✅ 데이터 조회 테스트 v1.3 완료!")


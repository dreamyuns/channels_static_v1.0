# utils/hotel_search.py
"""숙소 검색 기능 모듈
- 최근 180일 예약이 있는 숙소 또는 신규 등록 숙소 검색
- LIKE 검색 (숙소명, 숙소코드, 공백 제거 검색)
- 성능 최적화: 검색 범위 제한
"""

import sys
import os
# 프로젝트 루트 디렉토리를 path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from config.configdb import get_db_connection


def search_hotels(search_term, limit=15):
    """
    숙소 검색 함수
    
    Args:
        search_term: 검색어 (2자 이상 권장)
        limit: 최대 결과 수 (기본값: 15)
    
    Returns:
        list: 숙소 정보 딕셔너리 리스트
        [
            {
                'idx': 숙소 ID,
                'product_code': 숙소코드,
                'name_kr': 숙소 한글명,
                'has_recent_booking': 최근 예약 여부 (1 또는 0)
            },
            ...
        ]
    """
    # 검색어가 2자 미만이면 빈 리스트 반환
    if not search_term or len(search_term.strip()) < 2:
        return []
    
    try:
        engine = get_db_connection()
        
        # 검색어 정리 (공백 제거)
        search_term_clean = search_term.strip()
        search_term_no_space = search_term_clean.replace(' ', '')
        
        # 검색 쿼리 (최적화)
        query = """
        SELECT DISTINCT 
            p.idx, 
            p.product_code, 
            p.name_kr,
            CASE WHEN op.idx IS NOT NULL THEN 1 ELSE 0 END as has_recent_booking
        FROM product p
        LEFT JOIN order_product op ON p.idx = op.product_idx
            AND (
                -- 구매일 기준: 최근 180일 (6개월)
                op.create_date >= DATE_SUB(CURDATE(), INTERVAL 180 DAY)
                -- 또는 이용일 기준: 오늘 기준 앞뒤 180일
                OR (
                    op.checkin_date >= DATE_SUB(CURDATE(), INTERVAL 180 DAY)
                    AND op.checkin_date <= DATE_ADD(CURDATE(), INTERVAL 180 DAY)
                )
            )
        WHERE (
            p.name_kr LIKE %s 
            OR p.product_code LIKE %s
            OR REPLACE(p.name_kr, ' ', '') LIKE %s  -- 공백 제거 검색
        )
        -- 최근 예약이 있거나, 신규 등록 호텔도 검색
        AND (
            op.idx IS NOT NULL  -- 최근 예약이 있는 호텔
            OR p.reg_date >= DATE_SUB(CURDATE(), INTERVAL 90 DAY)  -- 최근 90일 이내 등록 (신규 호텔)
        )
        GROUP BY p.idx, p.product_code, p.name_kr
        ORDER BY 
            has_recent_booking DESC,  -- 예약 있는 호텔 우선 표시
            p.name_kr ASC, 
            p.idx DESC
        LIMIT %s
        """
        
        # 검색어에 와일드카드 추가
        search_pattern = f'%{search_term_clean}%'
        search_pattern_no_space = f'%{search_term_no_space}%'
        
        # 쿼리 실행 (params는 튜플로 전달)
        df = pd.read_sql(
            query, 
            engine,
            params=(search_pattern, search_pattern, search_pattern_no_space, limit)
        )
        
        # 결과를 딕셔너리 리스트로 변환
        if df.empty:
            return []
        
        results = []
        for _, row in df.iterrows():
            results.append({
                'idx': int(row['idx']),
                'product_code': str(row['product_code']) if pd.notna(row['product_code']) else '',
                'name_kr': str(row['name_kr']) if pd.notna(row['name_kr']) else '',
                'has_recent_booking': int(row['has_recent_booking'])
            })
        
        return results
        
    except Exception as e:
        print(f"❌ 숙소 검색 오류: {e}")
        import traceback
        traceback.print_exc()
        return []


def get_hotel_by_id(hotel_id):
    """
    숙소 ID로 숙소 정보 조회
    
    Args:
        hotel_id: 숙소 ID (product.idx)
    
    Returns:
        dict: 숙소 정보 또는 None
        {
            'idx': 숙소 ID,
            'product_code': 숙소코드,
            'name_kr': 숙소 한글명
        }
    """
    try:
        engine = get_db_connection()
        
        query = """
        SELECT 
            idx,
            product_code,
            name_kr
        FROM product
        WHERE idx = %s
        LIMIT 1
        """
        
        df = pd.read_sql(query, engine, params=(hotel_id,))
        
        if df.empty:
            return None
        
        row = df.iloc[0]
        return {
            'idx': int(row['idx']),
            'product_code': str(row['product_code']) if pd.notna(row['product_code']) else '',
            'name_kr': str(row['name_kr']) if pd.notna(row['name_kr']) else ''
        }
        
    except Exception as e:
        print(f"❌ 숙소 정보 조회 오류: {e}")
        return None


# 테스트 함수
if __name__ == "__main__":
    print("="*60)
    print("🏨 숙소 검색 테스트")
    print("="*60)
    
    # 테스트 1: 검색어 "힐튼"
    print("\n[테스트 1] 검색어: '힐튼'")
    results = search_hotels("힐튼", limit=5)
    print(f"검색 결과: {len(results)}개")
    for i, hotel in enumerate(results, 1):
        booking_status = "✅ 예약 있음" if hotel['has_recent_booking'] else "🆕 신규 등록"
        print(f"  {i}. [{hotel['idx']}] {hotel['name_kr']} ({hotel['product_code']}) - {booking_status}")
    
    # 테스트 2: 검색어 "서울"
    print("\n[테스트 2] 검색어: '서울'")
    results = search_hotels("서울", limit=5)
    print(f"검색 결과: {len(results)}개")
    for i, hotel in enumerate(results, 1):
        booking_status = "✅ 예약 있음" if hotel['has_recent_booking'] else "🆕 신규 등록"
        print(f"  {i}. [{hotel['idx']}] {hotel['name_kr']} ({hotel['product_code']}) - {booking_status}")
    
    # 테스트 3: 1자 검색어 (결과 없어야 함)
    print("\n[테스트 3] 검색어: '힐' (1자)")
    results = search_hotels("힐", limit=5)
    print(f"검색 결과: {len(results)}개 (2자 미만이므로 빈 결과)")
    
    print("\n✅ 숙소 검색 테스트 완료!")


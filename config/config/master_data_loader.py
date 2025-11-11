# config/master_data_loader.py
"""master_data.xlsx 파일 로더"""

import pandas as pd
import os

# 프로젝트 루트 디렉토리
_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_dir)
_excel_path = os.path.join(_project_root, "master_data.xlsx")

# 캐시 변수
_date_types = None
_order_statuses = None

def load_date_types():
    """
    date_type 시트에서 날짜유형 데이터 로드
    
    Returns:
        dict: {date_types_en: date_types_kr} 형태
        예: {'useDate': '이용일', 'orderDate': '구매일'}
    """
    global _date_types
    
    if _date_types is not None:
        return _date_types
    
    _date_types = {}
    
    if not os.path.exists(_excel_path):
        print(f"Warning: master_data.xlsx not found at {_excel_path}")
        return _date_types
    
    try:
        df = pd.read_excel(_excel_path, sheet_name='date_types')
        
        # 디버깅: 시트가 비어있는지 확인
        if df.empty:
            print(f"Warning: date_types sheet is empty in {_excel_path}")
            return _date_types
        
        # 디버깅: 컬럼명 확인
        if 'date_types_en' not in df.columns or 'date_types_kr' not in df.columns:
            print(f"Warning: date_types sheet columns: {df.columns.tolist()}")
            print(f"Expected columns: ['date_types_en', 'date_types_kr']")
            return _date_types
        
        for _, row in df.iterrows():
            date_type_en = str(row['date_types_en']).strip() if pd.notna(row.get('date_types_en')) else None
            date_type_kr = str(row['date_types_kr']).strip() if pd.notna(row.get('date_types_kr')) else None
            
            if date_type_en and date_type_kr:
                _date_types[date_type_en] = date_type_kr
        
        # 디버깅: 로드된 데이터 확인
        if not _date_types:
            print(f"Warning: No date types loaded from {_excel_path}")
        else:
            print(f"Loaded date types: {_date_types}")
                
    except FileNotFoundError:
        print(f"Error: File not found: {_excel_path}")
    except Exception as e:
        print(f"Warning: Could not load date_types sheet: {e}")
        import traceback
        traceback.print_exc()
    
    return _date_types

def load_order_statuses():
    """
    order_status 시트에서 예약상태 데이터 로드
    
    Returns:
        dict: {status_en: status_kr} 형태
        예: {'addpay': '추가결제대기중', 'cancel': '취소'}
    """
    global _order_statuses
    
    if _order_statuses is not None:
        return _order_statuses
    
    _order_statuses = {}
    
    if not os.path.exists(_excel_path):
        print(f"Warning: master_data.xlsx not found at {_excel_path}")
        return _order_statuses
    
    try:
        df = pd.read_excel(_excel_path, sheet_name='order_status')
        
        for _, row in df.iterrows():
            status_en = str(row['status_en']).strip() if pd.notna(row.get('status_en')) else None
            status_kr = str(row['status_kr']).strip() if pd.notna(row.get('status_kr')) else None
            
            if status_en and status_kr:
                _order_statuses[status_en] = status_kr
                
    except Exception as e:
        print(f"Warning: Could not load order_status sheet: {e}")
    
    return _order_statuses

def get_date_type_options():
    """
    날짜유형 셀렉트박스용 옵션 리스트 반환
    
    Returns:
        list: ['전체', 'useDate', 'orderDate']
    """
    date_types = load_date_types()
    options = ['전체']
    options.extend(list(date_types.keys()))
    return options

def get_date_type_display_name(date_type_en):
    """
    날짜유형 영어명으로 한글명 조회
    
    Args:
        date_type_en: 'useDate' 또는 'orderDate'
    
    Returns:
        str: 한글명 ('이용일' 또는 '구매일')
    """
    date_types = load_date_types()
    return date_types.get(date_type_en, date_type_en)

def get_order_status_options():
    """
    예약상태 셀렉트박스용 옵션 리스트 반환
    
    Returns:
        list: ['전체', '확정', '취소']
    """
    return ['전체', '확정', '취소']

def get_all_order_status_codes():
    """
    order_status 시트의 모든 status_en 값 반환
    
    Returns:
        list: 모든 상태코드 리스트
    """
    order_statuses = load_order_statuses()
    return list(order_statuses.keys())


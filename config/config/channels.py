# config/channels.py
"""채널별 설정 및 매핑 정보"""

import sys
import os
# 프로젝트 루트 디렉토리를 path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 채널별 상태값 매핑
CHANNEL_CONFIG = {
    'order_product': {
        # order_type별 설정
        'expedia': {
            'status': 'confirm',
            'name': 'Expedia',
            'channel_idx': None
        },
        'expediab2b': {
            'status': 'confirm',
            'name': 'Expedia B2B',
            'channel_idx': None
        },
        'hotelbeds': {
            'status': 'confirm',
            'name': 'Hotelbeds',
            'channel_idx': None
        },
        'dabo': {
            'status': 'confirm',
            'name': '다보',
            'channel_idx': None
        },
        'nuuaapi': {
            'status': 'confirm',
            'name': '누아',
            'channel_idx': None
        },
        'hiot': {
            'status': 'confirm',
            'name': '하이오티',
            'channel_idx': None
        }
    },
    'booking_master_offer': {
        # bmo_sup_code별 설정
        'AMTSUPCT0001': {
            'status': 'New',
            'name': 'Trip'
        },
        'AMTSUPME0003': {
            'status': 'BOOKING',
            'name': 'Meituan'
        },
        'AMTSUPFL0004': {
            'status': 'CONFIRMED',
            'name': 'Fliggy'
        },
        'AMTSUPDI0005': {
            'status': 'Confirmed',
            'name': 'Dida'
        },
        'AMTSUPAG0007': {
            'status': 'BOOKING',
            'name': 'Agoda'
        },
        'AMTSUPEL0009': {
            'status': 'Confirmed',
            'name': 'Elong'
        },
        'AMTSUPPK0008': {
            'status': 'BOOKING',
            'name': 'PKFare'
        }
    }
}

def get_all_channel_names():
    """모든 채널명 리스트 반환"""
    channels = []
    
    # order_product 채널들
    for config in CHANNEL_CONFIG['order_product'].values():
        channels.append(config['name'])
    
    # booking_master_offer 채널들
    for config in CHANNEL_CONFIG['booking_master_offer'].values():
        channels.append(config['name'])
    
    return sorted(list(set(channels)))

def get_channel_status_conditions():
    """각 채널별 상태 조건 SQL 생성"""
    conditions = []
    
    # booking_master_offer 테이블 조건들
    for sup_code, config in CHANNEL_CONFIG['booking_master_offer'].items():
        condition = f"(bmo.bmo_sup_code = '{sup_code}' AND bmo.bmo_booking_status = '{config['status']}')"
        conditions.append(condition)
    
    return " OR ".join(conditions)

def get_channel_name_mapping():
    """채널 코드 -> 이름 매핑 딕셔너리 반환"""
    mapping = {}
    
    # order_product 매핑
    for order_type, config in CHANNEL_CONFIG['order_product'].items():
        mapping[order_type] = config['name']
    
    # booking_master_offer 매핑
    for sup_code, config in CHANNEL_CONFIG['booking_master_offer'].items():
        mapping[sup_code] = config['name']
    
    return mapping

def build_channel_case_sql(table_type='booking_master_offer'):
    """CASE WHEN SQL 생성"""
    if table_type == 'booking_master_offer':
        cases = []
        for sup_code, config in CHANNEL_CONFIG['booking_master_offer'].items():
            cases.append(f"WHEN '{sup_code}' THEN '{config['name']}'")
        
        return "CASE bmo.bmo_sup_code\n    " + "\n    ".join(cases) + "\n    ELSE bmo.bmo_sup_code\nEND"
    
    return ""

# 테스트 함수
if __name__ == "__main__":
    print("="*50)
    print("📋 채널 설정 정보")
    print("="*50)
    
    print("\n[Order Product 채널]")
    for order_type, config in CHANNEL_CONFIG['order_product'].items():
        print(f"  - {config['name']} ({order_type}): status='{config['status']}'")
    
    print("\n[Booking Master Offer 채널]")
    for sup_code, config in CHANNEL_CONFIG['booking_master_offer'].items():
        print(f"  - {config['name']} ({sup_code}): status='{config['status']}'")
    
    print("\n[전체 채널 목록]")
    all_channels = get_all_channel_names()
    print(f"  총 {len(all_channels)}개: {', '.join(all_channels)}")
    
    print("\n[채널별 상태 조건 SQL]")
    conditions = get_channel_status_conditions()
    print(conditions[:200] + "..." if len(conditions) > 200 else conditions)
    
    print("\n" + "="*50)


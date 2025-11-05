# config/order_status_mapping.py
"""예약상태 그룹핑 정의"""

# 확정 그룹: order_status 시트에서 '확정' 그룹으로 표시될 상태값들
ORDER_STATUS_GROUPS = {
    '확정': [
        'addpay',      # 추가결제대기중
        'complete',    # 완료
        'confirm',     # 확정
        'confirmWait', # 확정 확인필요
        'confirmWip',  # 확정처리중
        'noshow',      # 노쇼
        'pending'      # 대기
    ],
    '취소': [
        'cancel',        # 취소
        'cancelWait',    # 취소 확인필요
        'cancelWip',     # 취소처리중
        'cancelRequest', # 취소요청
        'fail'          # 결제실패
    ]
}

def get_status_codes_by_group(group_name):
    """
    그룹명으로 상태코드 리스트 반환
    
    Args:
        group_name: '확정' 또는 '취소'
    
    Returns:
        list: 상태코드 리스트
    """
    return ORDER_STATUS_GROUPS.get(group_name, [])

def get_all_status_codes():
    """
    모든 상태코드 리스트 반환 (확정 + 취소)
    
    Returns:
        list: 모든 상태코드 리스트
    """
    all_statuses = []
    for status_list in ORDER_STATUS_GROUPS.values():
        all_statuses.extend(status_list)
    return all_statuses

def get_status_group_by_code(status_code):
    """
    상태코드로 그룹명 조회
    
    Args:
        status_code: 상태코드 (예: 'confirm', 'cancel')
    
    Returns:
        str: 그룹명 ('확정', '취소') 또는 None
    """
    for group_name, status_list in ORDER_STATUS_GROUPS.items():
        if status_code in status_list:
            return group_name
    return None


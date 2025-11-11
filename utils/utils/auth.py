# utils/auth.py
"""인증 모듈 - 사용자 로그인 및 세션 관리"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Optional
import bcrypt
import hashlib

# 프로젝트 루트 경로 추가
_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from config.configdb import get_db_connection
from utils.logger import log_auth, log_error

# 세션 타임아웃 설정 (초)
SESSION_TIMEOUT_SECONDS = 3600  # 1시간
SESSION_WARNING_SECONDS = 300   # 5분 전 경고


def get_user_ip() -> Optional[str]:
    """사용자 IP 주소 가져오기 (Streamlit)"""
    try:
        import streamlit as st
        ip = st.context.ip_address if hasattr(st, 'context') else None
        return ip if ip else "unknown"
    except Exception:
        return "unknown"


def authenticate_user(admin_id: str, password: str) -> Dict:
    """
    사용자 인증
    
    Args:
        admin_id: 사용자 ID
        password: 비밀번호 (평문)
    
    Returns:
        {
            'success': bool,
            'admin_id': str,
            'user_status': str,
            'error': str (실패 시)
        }
    """
    ip = get_user_ip()
    
    # 입력 검증
    if not admin_id or not password:
        log_auth("WARNING", "로그인 실패", admin_id=admin_id, ip=ip, 사유="입력값 누락")
        return {
            'success': False,
            'admin_id': admin_id,
            'user_status': None,
            'error': 'ID와 비밀번호를 입력해주세요.'
        }
    
    try:
        # DB 연결
        engine = get_db_connection()
        
        # 사용자 조회
        query = """
        SELECT 
            admin_id,
            passwd,
            user_status
        FROM tblmanager
        WHERE admin_id = %s
        """
        
        import pandas as pd
        df = pd.read_sql(query, engine, params=(admin_id,))
        
        if df.empty:
            log_auth("WARNING", "로그인 실패", admin_id=admin_id, ip=ip, 사유="존재하지 않는 사용자")
            return {
                'success': False,
                'admin_id': admin_id,
                'user_status': None,
                'error': 'ID 또는 비밀번호가 올바르지 않습니다.'
            }
        
        user = df.iloc[0]
        stored_password = user['passwd']
        user_status = user['user_status']
        
        # user_status 디버깅 정보 로깅
        log_auth("INFO", "사용자 조회 성공", admin_id=admin_id, ip=ip, 
                user_status=str(user_status), user_status_type=str(type(user_status)))
        
        # user_status 확인 (일시적으로 비활성화 - 디버깅용)
        # user_status 값이 문자열 '1', 숫자 1, 또는 공백 포함 '1 ' 등 다양한 형식일 수 있음
        user_status_str = str(user_status).strip() if user_status is not None else ''
        
        # user_status 체크 비활성화 (임시)
        # if user_status_str != '1':
        #     log_auth("WARNING", "로그인 실패", admin_id=admin_id, ip=ip, 
        #             사유=f"계정 비활성화 (user_status='{user_status_str}')")
        #     return {
        #         'success': False,
        #         'admin_id': admin_id,
        #         'user_status': user_status,
        #         'error': f'계정이 비활성화되어 있습니다. (user_status: {user_status_str}) 관리자에게 문의하세요.'
        #     }
        
        # 비밀번호 검증
        password_valid = False
        password_length = len(stored_password) if stored_password else 0
        
        # 비밀번호 검증 디버깅 정보
        log_auth("INFO", "비밀번호 검증 시작", admin_id=admin_id, ip=ip, 
                stored_password_length=password_length)
        
        # 1. bcrypt 시도 (60자 길이)
        if password_length == 60:
            try:
                password_valid = bcrypt.checkpw(
                    password.encode('utf-8'),
                    stored_password.encode('utf-8')
                )
                if password_valid:
                    log_auth("INFO", "bcrypt 검증 성공", admin_id=admin_id, ip=ip)
                else:
                    log_auth("INFO", "bcrypt 검증 실패 (비밀번호 불일치)", admin_id=admin_id, ip=ip)
            except Exception as e:
                log_error("WARNING", "bcrypt 검증 실패", exception=e, admin_id=admin_id)
        
        # 2. MD5 시도 (32자 길이)
        if not password_valid and password_length == 32:
            try:
                md5_hash = hashlib.md5(password.encode('utf-8')).hexdigest()
                password_valid = (md5_hash.lower() == stored_password.lower())
                if password_valid:
                    log_auth("INFO", "MD5 검증 성공", admin_id=admin_id, ip=ip)
            except Exception as e:
                log_error("WARNING", "MD5 검증 중 오류", exception=e, admin_id=admin_id)
        
        # 3. SHA256 시도 (64자 길이)
        if not password_valid and password_length == 64:
            try:
                sha256_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
                password_valid = (sha256_hash.lower() == stored_password.lower())
                if password_valid:
                    log_auth("INFO", "SHA256 검증 성공", admin_id=admin_id, ip=ip)
            except Exception as e:
                log_error("WARNING", "SHA256 검증 중 오류", exception=e, admin_id=admin_id)
        
        # 4. 평문 비교 (보안상 권장하지 않지만 호환성을 위해)
        if not password_valid:
            password_valid = (password == stored_password)
            if password_valid:
                log_auth("WARNING", "평문 비밀번호 검증 성공 (보안 권장하지 않음)", admin_id=admin_id, ip=ip)
        
        if not password_valid:
            log_auth("WARNING", "로그인 실패", admin_id=admin_id, ip=ip, 
                    사유="비밀번호 불일치", 
                    stored_password_length=password_length,
                    password_hash_type="bcrypt" if password_length == 60 else 
                                      "MD5" if password_length == 32 else 
                                      "SHA256" if password_length == 64 else "평문")
            return {
                'success': False,
                'admin_id': admin_id,
                'user_status': user_status,
                'error': 'ID 또는 비밀번호가 올바르지 않습니다.'
            }
        
        # 로그인 성공
        log_auth("INFO", "로그인 성공", admin_id=admin_id, ip=ip)
        return {
            'success': True,
            'admin_id': admin_id,
            'user_status': user_status,
            'error': None
        }
        
    except Exception as e:
        log_error("ERROR", "인증 중 오류 발생", exception=e, admin_id=admin_id, ip=ip)
        return {
            'success': False,
            'admin_id': admin_id,
            'user_status': None,
            'error': f'인증 중 오류가 발생했습니다: {str(e)}'
        }


def check_session_timeout(login_time) -> Dict:
    """
    세션 타임아웃 체크
    
    Args:
        login_time: 로그인 시간 (datetime 또는 문자열)
    
    Returns:
        {
            'is_valid': bool,
            'time_remaining': int (초),
            'should_warn': bool (경고 필요 여부)
        }
    """
    if not login_time:
        return {
            'is_valid': False,
            'time_remaining': 0,
            'should_warn': False
        }
    
    # login_time이 문자열인 경우 datetime으로 변환
    if isinstance(login_time, str):
        try:
            login_time = datetime.fromisoformat(login_time)
        except (ValueError, AttributeError):
            # 변환 실패 시 현재 시간으로 간주 (세션 유지)
            return {
                'is_valid': True,
                'time_remaining': SESSION_TIMEOUT_SECONDS,
                'should_warn': False
            }
    elif not isinstance(login_time, datetime):
        # 예상치 못한 타입인 경우 세션 유지
        return {
            'is_valid': True,
            'time_remaining': SESSION_TIMEOUT_SECONDS,
            'should_warn': False
        }
    
    elapsed = (datetime.now() - login_time).total_seconds()
    time_remaining = SESSION_TIMEOUT_SECONDS - elapsed
    
    is_valid = time_remaining > 0
    should_warn = is_valid and time_remaining <= SESSION_WARNING_SECONDS
    
    return {
        'is_valid': is_valid,
        'time_remaining': int(time_remaining),
        'should_warn': should_warn
    }


def is_authenticated(session_state) -> bool:
    """인증 상태 확인"""
    # authenticated와 admin_id만 있으면 인증된 것으로 간주
    # 세션 타임아웃 체크 제거됨
    
    # 디버깅: 각 조건 확인
    has_authenticated_key = 'authenticated' in session_state
    authenticated_value = session_state.get('authenticated', False) if has_authenticated_key else None
    has_admin_id_key = 'admin_id' in session_state
    admin_id_value = session_state.get('admin_id') if has_admin_id_key else None
    
    # 디버깅 로그 (너무 많이 찍히지 않도록 조건부)
    if not has_authenticated_key or not authenticated_value or not has_admin_id_key or not admin_id_value:
        log_auth("DEBUG", "인증 체크 실패 상세", 
                 has_authenticated_key=has_authenticated_key,
                 authenticated_value=authenticated_value,
                 has_admin_id_key=has_admin_id_key,
                 admin_id_value=admin_id_value,
                 all_keys=list(session_state.keys()) if hasattr(session_state, 'keys') else 'N/A')
    
    result = (
        has_authenticated_key and
        authenticated_value and
        has_admin_id_key and
        admin_id_value  # admin_id가 실제로 값이 있는지 확인
    )
    
    return result


def logout(session_state):
    """로그아웃"""
    admin_id = session_state.get('admin_id', 'unknown')
    ip = get_user_ip()
    
    log_auth("INFO", "로그아웃", admin_id=admin_id, ip=ip)
    
    # 세션 정보 삭제
    if 'authenticated' in session_state:
        del session_state.authenticated
    if 'admin_id' in session_state:
        del session_state.admin_id
    if 'login_time' in session_state:
        del session_state.login_time


if __name__ == "__main__":
    # 테스트
    print("인증 모듈 테스트")
    print(f"IP 주소: {get_user_ip()}")
    print("✅ 인증 모듈 로드 완료")


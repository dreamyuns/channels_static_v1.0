# app_v1.1_hotel.py
"""숙소별 예약 통계 시스템 - Streamlit 메인 애플리케이션 v1.1
- 인증 기능 추가 (tblmanager 테이블 기반)
- 로깅 기능 추가 (타입별 로그 파일 분리)
- 로딩 표시 개선 (st.status 사용)
- 숙소 검색 기능 (자동완성)
- v1.1 변경사항:
  - 검색 버튼 삭제, 엔터키로만 검색
  - 선택된 숙소는 셀렉트박스 옵션에서 제외 (중복 선택 방지)
  - 선택 후 셀렉트박스 비우기
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import importlib.util
import sys
import os

# 로깅 모듈 import 및 초기화
from utils.logger import setup_logging, log_auth, log_error, log_access
setup_logging()

# 인증 모듈 import
from utils.auth import (
    authenticate_user,
    is_authenticated,
    logout
)

# 숙소 검색 모듈 import
from utils.hotel_search import search_hotels, get_hotel_by_id

# 숙소별 데이터 조회 모듈 import
from utils.data_fetcher_hotel import fetch_hotel_data, fetch_hotel_summary_stats

# 숙소별 엑셀 핸들러 import
from utils.excel_handler_hotel import create_hotel_excel_download

from config.master_data_loader import (
    get_date_type_options,
    get_date_type_display_name
)

# 페이지 설정
st.set_page_config(
    page_title="숙소별 예약 통계",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 사이드바 너비 1.5배 CSS
sidebar_css = """
<style>
    /* 사이드바 너비 1.5배 */
    .css-1d391kg {
        width: 450px !important;
    }
    [data-testid="stSidebar"] {
        width: 450px !important;
    }
    
    /* 숙소명 표시 (8자 제한, 12px) */
    .hotel-name-display {
        font-size: 12px;
        max-width: 100px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    
    /* 검색 결과 텍스트 링크 스타일 (밑줄 효과) */
    .search-result-link {
        text-decoration: underline;
        color: #1f77b4;
        cursor: pointer;
    }
    
    .search-result-link:hover {
        color: #0d5aa7;
    }
</style>
"""
st.markdown(sidebar_css, unsafe_allow_html=True)

# ============================================
# 인증 체크 및 로그인 페이지
# ============================================

# 쿠키에서 인증 정보 복원 (새로고침 문제 해결)
def restore_auth_from_cookie():
    """쿠키에서 인증 정보를 읽어 세션 상태에 복원"""
    try:
        log_auth("DEBUG", "restore_auth_from_cookie 시작", 
                has_logout_flag=st.session_state.get('_logout_in_progress', False),
                is_authenticated=is_authenticated(st.session_state))
    except:
        pass
    
    # 로그아웃 중이면 복원하지 않음
    # 단, 로그아웃 플래그는 로그아웃 버튼 클릭 시에만 설정되므로
    # 새로고침 시에는 플래그가 없어야 함
    if st.session_state.get('_logout_in_progress', False):
        try:
            log_auth("DEBUG", "로그아웃 진행 중 - 쿠키 복원 건너뜀")
        except:
            pass  # 로그 기록 실패해도 계속 진행
        return False
    
    # 이미 인증되어 있으면 복원 불필요
    if is_authenticated(st.session_state):
        try:
            log_auth("DEBUG", "이미 인증됨 - 쿠키 복원 불필요")
        except:
            pass
        return True
    
    # 방법 1: URL 파라미터에서 복원 (JavaScript 리다이렉트로 설정된 경우 우선 처리)
    try:
        query_params = st.query_params
        if 'auth_restore' in query_params:
            admin_id = query_params['auth_restore']
            if admin_id:
                st.session_state.authenticated = True
                st.session_state.admin_id = admin_id
                if '_logout_in_progress' in st.session_state:
                    del st.session_state['_logout_in_progress']
                # URL 파라미터 제거 (다음 요청에서는 쿠키로만 복원)
                st.query_params.clear()
                try:
                    log_auth("INFO", "쿠키에서 인증 정보 복원 (URL 파라미터)", admin_id=admin_id)
                except:
                    pass
                # URL 파라미터로 복원된 경우 rerun (쿠키로 복원되도록)
                st.rerun()
                return True
    except Exception as e:
        try:
            log_error("DEBUG", "URL 파라미터 복원 실패", exception=e)
        except:
            pass
    
    # 방법 2: st.context.cookies 사용 (서버 측 쿠키 읽기)
    try:
        has_context = hasattr(st, 'context')
        has_cookies = has_context and hasattr(st.context, 'cookies')
        
        if has_cookies:
            cookies = st.context.cookies
            cookie_dict = cookies.to_dict() if hasattr(cookies, 'to_dict') else dict(cookies)
            
            if 'auth_admin_id' in cookie_dict:
                admin_id = cookie_dict.get('auth_admin_id')
                if admin_id:
                    st.session_state.authenticated = True
                    st.session_state.admin_id = admin_id
                    # 로그아웃 플래그가 있다면 삭제 (새로고침 시 정상 복원을 위해)
                    if '_logout_in_progress' in st.session_state:
                        del st.session_state['_logout_in_progress']
                    try:
                        log_auth("INFO", "쿠키에서 인증 정보 복원 (context)", admin_id=admin_id)
                    except:
                        pass
                    return True
        
    except Exception as e:
        try:
            log_error("DEBUG", "st.context.cookies 접근 실패", exception=e)
        except:
            pass
    
    return False

# 쿠키에서 인증 정보 복원 시도
restore_result = restore_auth_from_cookie()

# 쿠키 복원 실패 시 JavaScript로 쿠키 읽기 시도 (운영서버 대응)
# 단, 로그아웃 진행 중이거나 이미 인증된 경우는 실행하지 않음
if not restore_result and not is_authenticated(st.session_state) and not st.session_state.get('_logout_in_progress', False):
    # URL 파라미터에 auth_restore가 없을 때만 JavaScript 실행 (무한 리다이렉트 방지)
    if 'auth_restore' not in st.query_params:
        cookie_read_script = """
        <script>
        (function() {
            function getCookie(name) {
                var nameEQ = name + "=";
                var ca = document.cookie.split(';');
                for(var i = 0; i < ca.length; i++) {
                    var c = ca[i];
                    while (c.charAt(0) == ' ') c = c.substring(1, c.length);
                    if (c.indexOf(nameEQ) == 0) {
                        return c.substring(nameEQ.length, c.length);
                    }
                }
                return null;
            }
            
            // URL 파라미터에 auth_restore가 없고, 쿠키에 auth_admin_id가 있으면 리다이렉트
            var urlParams = new URLSearchParams(window.location.search);
            if (!urlParams.has('auth_restore')) {
                var authId = getCookie("auth_admin_id");
                if (authId) {
                    // 즉시 리다이렉트 (방안 1: 타이밍 문제 해결)
                    var newUrl = window.location.pathname + "?auth_restore=" + encodeURIComponent(authId);
                    window.location.replace(newUrl);
                }
            }
        })();
        </script>
        """
        st.components.v1.html(cookie_read_script, height=0)

# 디버깅: 세션 상태 확인
debug_info = {
    'has_authenticated': 'authenticated' in st.session_state,
    'authenticated_value': st.session_state.get('authenticated', 'NOT_SET'),
    'has_admin_id': 'admin_id' in st.session_state,
    'admin_id_value': st.session_state.get('admin_id', 'NOT_SET'),
    'session_state_keys': list(st.session_state.keys())
}
is_auth_result = is_authenticated(st.session_state)

# 디버깅 로그 (로그 기록 실패해도 계속 진행)
try:
    log_auth("INFO", "인증 상태 체크", 
             is_authenticated=is_auth_result,
             debug_info=str(debug_info))
except:
    pass  # 로그 기록 실패해도 계속 진행

# 인증 상태 확인
if not is_auth_result:
    # 로그인 페이지
    st.title("🔐 로그인")
    st.markdown("---")
    
    # 디버깅 정보 표시 (개발용)
    with st.expander("🔍 디버깅 정보 (개발용)", expanded=False):
        st.json(debug_info)
        st.write(f"**is_authenticated() 결과:** {is_auth_result}")
    
    # 로그인 폼
    with st.form("login_form"):
        admin_id = st.text_input("사용자 ID", placeholder="admin_id를 입력하세요")
        password = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요")
        login_button = st.form_submit_button("로그인", type="primary", use_container_width=True)
        
        if login_button:
            if admin_id and password:
                # 인증 시도
                auth_result = authenticate_user(admin_id, password)
                
                if auth_result['success']:
                    # 로그인 성공
                    st.session_state.authenticated = True
                    st.session_state.admin_id = auth_result['admin_id']
                    
                    # 로그아웃 플래그 삭제 (로그인 성공 시)
                    if '_logout_in_progress' in st.session_state:
                        del st.session_state['_logout_in_progress']
                    
                    # 쿠키에 인증 정보 저장 (새로고침 문제 해결)
                    # JavaScript를 사용하여 쿠키 설정 (서버 환경 대응)
                    admin_id = auth_result['admin_id']
                    # 쿠키 설정 스크립트 (운영 서버 환경 대응 강화)
                    cookie_script = f"""
                    <script>
                    (function() {{
                        function setCookie(name, value, days) {{
                            var expires = "";
                            if (days) {{
                                var date = new Date();
                                date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
                                expires = "; expires=" + date.toUTCString();
                            }}
                            
                            // 운영 서버 환경 대응: 도메인 자동 감지 및 설정
                            var hostname = window.location.hostname;
                            var domain = "";
                            // 서브도메인이 있는 경우 도메인 설정 (예: app.example.com -> .example.com)
                            if (hostname.split('.').length > 2) {{
                                var parts = hostname.split('.');
                                domain = "." + parts.slice(-2).join('.');
                            }}
                            
                            // 쿠키 문자열 구성
                            var cookieString = name + "=" + value + expires + "; path=/; SameSite=Lax";
                            
                            // 도메인 설정 (로컬호스트가 아닌 경우)
                            if (domain && !hostname.includes('localhost') && !hostname.includes('127.0.0.1')) {{
                                cookieString += "; domain=" + domain;
                            }}
                            
                            // HTTPS 환경에서는 Secure 플래그 추가 (자동 감지)
                            if (window.location.protocol === 'https:') {{
                                cookieString += "; Secure";
                            }}
                            
                            document.cookie = cookieString;
                            console.log("Cookie set: " + name + "=" + value + " (domain: " + (domain || "default") + ")");
                            
                            // 쿠키 설정 확인 (여러 번 시도)
                            var attempts = 0;
                            var maxAttempts = 5;
                            var checkInterval = setInterval(function() {{
                                attempts++;
                                var checkCookie = document.cookie.indexOf(name + "=");
                                if (checkCookie >= 0) {{
                                    console.log("Cookie check: OK (attempt " + attempts + ")");
                                    clearInterval(checkInterval);
                                }} else if (attempts >= maxAttempts) {{
                                    console.log("Cookie check: FAILED after " + maxAttempts + " attempts");
                                    clearInterval(checkInterval);
                                }}
                            }}, 100);
                        }}
                        
                        // 즉시 실행
                        setCookie("auth_admin_id", "{admin_id}", 1);
                    }})();
                    </script>
                    """
                    st.components.v1.html(cookie_script, height=0)
                    
                    # 디버깅: 로그인 성공 후 세션 상태 확인
                    log_auth("INFO", "로그인 성공 - 세션 상태 및 쿠키 저장 시도", 
                             admin_id=auth_result['admin_id'],
                             authenticated_set=st.session_state.get('authenticated'),
                             admin_id_set=st.session_state.get('admin_id'),
                             all_keys=list(st.session_state.keys()))
                    
                    st.rerun()
                else:
                    # 로그인 실패 - 상세 정보 표시
                    error_msg = auth_result['error']
                    user_status = auth_result.get('user_status', 'N/A')
                    
                    # 디버깅 정보 (개발 환경에서만 표시)
                    debug_info = f"\n\n**디버깅 정보:**\n- user_status: `{user_status}` (타입: {type(user_status).__name__})"
                    
                    st.error(f"⚠️ {error_msg}")
                    st.info(f"💡 로그 파일(`logs/auth.log`)에서 상세 정보를 확인할 수 있습니다.{debug_info}")
                    log_auth("WARNING", "로그인 실패", admin_id=admin_id, 사유=error_msg, user_status=str(user_status))
            else:
                st.error("⚠️ ID와 비밀번호를 입력해주세요.")
    
    st.markdown("---")
    st.caption("숙소별 예약 통계 시스템 v1.1 | 로그인이 필요합니다")
    st.stop()

# 인증된 사용자만 여기까지 도달

# 디버깅: 인증된 사용자 접근 확인
log_auth("INFO", "인증된 사용자 접근", 
         admin_id=st.session_state.get('admin_id'),
         authenticated=st.session_state.get('authenticated'),
         session_keys=list(st.session_state.keys()))

# ============================================
# 메인 애플리케이션
# ============================================

# 헤더 (제목 + 로그아웃 버튼)
col_header1, col_header2 = st.columns([10, 1])
with col_header1:
    st.title("🏨 숙소별 예약 통계 시스템")
with col_header2:
    if st.button("🚪 로그아웃", type="secondary", use_container_width=True):
        # 로그아웃 플래그 설정 (쿠키 복원 방지) - 삭제하지 않고 유지
        st.session_state['_logout_in_progress'] = True
        
        # 세션 상태 먼저 삭제
        logout(st.session_state)
        
        # 쿠키 삭제 및 페이지 리로드 (JavaScript로 강제 리로드)
        cookie_script = """
        <script>
        // 쿠키 삭제
        document.cookie = "auth_admin_id=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Lax";
        // 페이지 강제 리로드하여 로그인 페이지로 이동
        setTimeout(function() {
            window.location.href = window.location.pathname;
        }, 100);
        </script>
        """
        st.components.v1.html(cookie_script, height=0)
        
        # st.rerun() 호출하여 즉시 로그인 페이지로 이동
        st.rerun()

st.markdown("---")

# 사용자 정보 표시 (선택사항)
admin_id = st.session_state.get('admin_id', 'unknown')
st.caption(f"👤 로그인 사용자: {admin_id}")

# 기본값 설정
default_end = date.today() - timedelta(days=1)  # 어제까지 (당일 제외)
default_start = default_end - timedelta(days=6)  # 최근 7일
default_date_type = 'orderDate'  # 구매일이 기본값
# 예약상태는 항상 '전체'로 고정
order_status = '전체'

# 숙소명 표시 함수 (8자 제한, 말줄임표)
def format_hotel_name(name, max_length=8):
    """숙소명을 최대 길이로 제한하고 말줄임표 추가"""
    if len(name) <= max_length:
        return name
    return name[:max_length] + "..."

# 사이드바: 검색 조건
with st.sidebar:
    st.header("🔍 검색 조건")
    
    # 날짜 범위
    st.subheader("날짜 범위")
    
    # 날짜유형 선택
    date_type_options = get_date_type_options()
    
    # '전체' 옵션 제거
    date_type_options = [opt for opt in date_type_options if opt != '전체']
    
    # 디버깅: 날짜유형 옵션이 제대로 로드되었는지 확인
    if len(date_type_options) <= 1:
        st.warning("⚠️ 날짜유형 데이터를 불러올 수 없습니다. master_data.xlsx의 date_types 시트를 확인하세요.")
        # 기본값으로 하드코딩된 옵션 제공
        date_type_options = ['useDate', 'orderDate']
    
    date_type_display = {opt: get_date_type_display_name(opt) 
                         for opt in date_type_options}
    
    # 세션 상태 초기화
    if 'date_type' not in st.session_state:
        st.session_state.date_type = default_date_type
    if 'start_date' not in st.session_state:
        st.session_state.start_date = default_start
    if 'end_date' not in st.session_state:
        st.session_state.end_date = default_end
    if 'selected_hotels' not in st.session_state:
        st.session_state.selected_hotels = []
    if 'search_term' not in st.session_state:
        st.session_state.search_term = ''
    
    # 세션 상태에서 날짜유형 인덱스 찾기
    date_type_index = 0
    if 'date_type' in st.session_state and st.session_state.date_type in date_type_options:
        date_type_index = date_type_options.index(st.session_state.date_type)
    elif default_date_type in date_type_options:
        date_type_index = date_type_options.index(default_date_type)
    
    date_type = st.selectbox(
        "날짜유형",
        options=date_type_options,
        index=date_type_index,
        format_func=lambda x: date_type_display[x],
        help="이용일 또는 구매일 기준으로 조회할 수 있습니다.",
        key='date_type_select'
    )
    
    # 세션 상태에 날짜유형 저장
    st.session_state.date_type = date_type
    
    # 날짜 범위 설정: 날짜유형에 따라 다르게 설정
    today = date.today()
    min_date = today - timedelta(days=90)  # 90일 전
    
    if date_type == 'useDate':
        # 이용일(체크인) 기준: 미래 날짜도 선택 가능
        max_date = today + timedelta(days=90)  # 90일 후
        start_help = "이용일(체크인) 기준으로 조회합니다. 미래 날짜도 선택 가능합니다."
        end_help = "이용일(체크인) 기준으로 조회합니다. 미래 날짜도 선택 가능합니다."
    else:
        # 구매일 기준: 어제까지만 선택 가능
        max_date = today - timedelta(days=1)  # 어제까지
        start_help = "구매일(예약일) 기준으로 조회합니다. 당일 데이터는 조회할 수 없습니다 (D-1까지만 조회 가능)"
        end_help = "구매일(예약일) 기준으로 조회합니다. 당일 데이터는 조회할 수 없습니다 (D-1까지만 조회 가능)"
    
    start_date = st.date_input(
        "시작일",
        value=st.session_state.start_date,
        min_value=min_date,
        max_value=max_date,
        help=start_help,
        key='start_date_input'
    )
    
    end_date = st.date_input(
        "종료일",
        value=st.session_state.end_date,
        min_value=min_date,
        max_value=max_date,
        help=end_help,
        key='end_date_input'
    )
    
    # 세션 상태에 날짜 저장
    st.session_state.start_date = start_date
    st.session_state.end_date = end_date
    
    # 날짜 범위 검증
    if start_date > end_date:
        st.error("⚠️ 시작일이 종료일보다 늦을 수 없습니다.")
        st.stop()
    
    # 최대 3개월 제한
    max_days = 90
    days_diff = (end_date - start_date).days + 1
    if days_diff > max_days:
        st.error(f"⚠️ 조회 기간은 최대 {max_days}일(3개월)까지 가능합니다.")
        st.stop()
    
    st.info(f"📅 조회 기간: {days_diff}일")
    
    # 숙소 검색
    st.subheader("숙소 검색")
    
    # 검색 입력창 (검색 버튼 삭제, 엔터키로만 검색)
    search_term = st.text_input(
        "숙소명 or 숙소코드를 입력해주세요",
        value=st.session_state.search_term,
        placeholder="숙소명 or 숙소코드를 입력해주세요.",
        help="검색어를 입력한 후 엔터 키를 눌러주세요.",
        key='hotel_search_input',
        label_visibility="collapsed"
    )
    
    # 검색 결과 표시 (엔터 키 입력 시에만)
    search_results = []
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []
    if 'last_search_term' not in st.session_state:
        st.session_state.last_search_term = ''
    
    # 검색 실행 조건: 검색어 변경 (엔터 키 입력 시)
    # Streamlit에서 text_input에 엔터를 누르면 자동으로 rerun되므로, 검색어 변경을 감지
    search_term_changed = search_term != st.session_state.last_search_term
    
    if search_term_changed:
        if search_term and len(search_term.strip()) >= 2:
            with st.spinner("🔍 검색 중..."):
                search_results = search_hotels(search_term.strip(), limit=15)
                st.session_state.search_results = search_results
                st.session_state.last_search_term = search_term.strip()  # 공백 제거하여 저장
        else:
            if search_term and len(search_term.strip()) < 2:
                st.warning("⚠️ 검색어를 2자 이상 입력해주세요.")
            st.session_state.search_results = []
            st.session_state.last_search_term = search_term.strip() if search_term else ''
    else:
        # 이전 검색 결과 유지
        search_results = st.session_state.search_results
    
    # 세션 상태에 검색어 저장
    st.session_state.search_term = search_term
    
    # 검색 결과를 multiselect 형태로 표시 (선택된 숙소도 포함)
    if search_results:
        # 이미 선택된 숙소의 idx 목록 (중복 선택 방지)
        selected_hotel_indices = {h.get('idx') for h in st.session_state.selected_hotels if h.get('idx')}
        
        # 검색 결과를 옵션 리스트로 변환 (모든 검색 결과 포함)
        hotel_options = []
        hotel_dict = {}  # 옵션 라벨 -> hotel 객체 매핑
        
        for hotel in search_results:
            hotel_label = f"{hotel['name_kr']} ({hotel['product_code']})"
            hotel_options.append(hotel_label)
            hotel_dict[hotel_label] = hotel
        
        # 이미 선택된 숙소의 라벨 추출 (체크 상태로 유지)
        selected_labels_in_results = []
        for hotel in st.session_state.selected_hotels:
            hotel_label = f"{hotel['name_kr']} ({hotel['product_code']})"
            if hotel_label in hotel_options:
                selected_labels_in_results.append(hotel_label)
        
        # multiselect로 표시 (선택된 항목은 default에 포함하여 체크 상태 유지)
        selected_hotel_labels = st.multiselect(
            "검색 결과에서 숙소를 선택하세요",
            options=hotel_options,
            default=selected_labels_in_results,  # 선택된 항목을 체크 상태로 유지
            help="숙소를 선택해주세요 (2개 이상 선택 가능)",
            key='hotel_search_multiselect',
            placeholder="숙소를 선택해주세요 (2개 이상 선택 가능)"
        )
        
        # 선택된 숙소 업데이트
        # 새로 선택된 숙소 추가
        for label in selected_hotel_labels:
            if label not in selected_labels_in_results:
                hotel = hotel_dict[label]
                # 중복 확인 (이미 선택된 숙소인지)
                if not any(h.get('idx') == hotel['idx'] for h in st.session_state.selected_hotels):
                    # 최대 10개 제한
                    if len(st.session_state.selected_hotels) < 10:
                        st.session_state.selected_hotels.append(hotel)
                        st.rerun()
                    else:
                        st.warning("⚠️ 최대 10개까지 선택 가능합니다.")
                        st.rerun()
        
        # 선택 해제된 숙소 제거
        for label in selected_labels_in_results:
            if label not in selected_hotel_labels:
                hotel = hotel_dict[label]
                st.session_state.selected_hotels = [h for h in st.session_state.selected_hotels if h.get('idx') != hotel['idx']]
                st.rerun()
    
    # 선택한 숙소 목록 (체크박스 형태, 체크 해제 시 삭제)
    if st.session_state.selected_hotels:
        st.markdown("---")
        st.write("**선택한 숙소 목록:**")
        
        # 선택된 숙소를 체크박스 형태로 표시
        hotels_to_remove = []
        
        for i, hotel in enumerate(st.session_state.selected_hotels):
            hotel_name = hotel.get('name_kr', 'Unknown')
            hotel_name_short = format_hotel_name(hotel_name, max_length=8)
            hotel_label = f"🏨 {hotel_name_short}"
            
            # 체크박스 (기본값: True, 체크 해제 시 삭제)
            is_checked = st.checkbox(
                hotel_label,
                value=True,
                key=f"hotel_checkbox_{hotel.get('idx')}_{i}",
                help=f"{hotel_name} (클릭하여 선택 해제)"
            )
            
            # 체크 해제 시 삭제 목록에 추가
            if not is_checked:
                hotels_to_remove.append(i)
        
        # 삭제 처리
        if hotels_to_remove:
            for idx in sorted(hotels_to_remove, reverse=True):
                removed_hotel = st.session_state.selected_hotels.pop(idx)
                st.info(f"✅ '{removed_hotel.get('name_kr', 'Unknown')}' 선택 해제됨")
            st.rerun()
    else:
        st.warning("⚠️ 최소 1개 이상의 숙소를 선택해주세요.")
    
    # 조회 및 초기화 버튼
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        search_button = st.button("🔍 조회", type="primary", use_container_width=True)
    with col2:
        reset_button = st.button("🔄 초기화", use_container_width=True)
    
    # 초기화 버튼 처리
    if reset_button:
        st.session_state.date_type = default_date_type
        st.session_state.start_date = default_start
        st.session_state.end_date = default_end
        st.session_state.selected_hotels = []
        st.session_state.search_term = ''
        st.session_state.last_search_result = None
        st.rerun()

# 메인 영역
# 조회 버튼이 클릭되었거나, 이전 조회 결과가 있는 경우 결과 표시
has_search_result = 'last_search_result' in st.session_state and st.session_state.last_search_result is not None
should_show_result = search_button or has_search_result

if should_show_result:
    # 조회 버튼이 클릭된 경우에만 새로 조회
    if search_button:
        # 선택된 숙소 확인
        if not st.session_state.selected_hotels:
            st.error("⚠️ 최소 1개 이상의 숙소를 선택해주세요.")
            st.stop()
        
        # 선택된 숙소 ID 리스트 추출
        selected_hotel_ids = [hotel.get('idx') for hotel in st.session_state.selected_hotels if hotel.get('idx')]
        
        if not selected_hotel_ids:
            st.error("⚠️ 선택된 숙소가 없습니다. 숙소를 선택해주세요.")
            st.stop()
        
        # 데이터 조회 (로딩 표시: st.spinner 사용 - 접기/펼치기 없음)
        try:
            with st.spinner("🔄 데이터를 조회하는 중..."):
                # 로깅: 데이터 조회 시작
                log_access("INFO", "숙소별 데이터 조회 시작", admin_id=admin_id, 
                          기간=f"{start_date}~{end_date}", 
                          숙소수=len(selected_hotel_ids),
                          날짜유형=date_type)
                
                df = fetch_hotel_data(
                    start_date=start_date,
                    end_date=end_date,
                    selected_hotel_ids=selected_hotel_ids,
                    date_type=date_type,
                    order_status='전체'  # 항상 '전체'로 고정
                )
                
                # 요약 통계 조회
                summary_stats = fetch_hotel_summary_stats(
                    start_date, 
                    end_date, 
                    selected_hotel_ids=selected_hotel_ids,
                    date_type=date_type,
                    order_status='전체'  # 항상 '전체'로 고정
                )
                
                # 조회 결과를 세션 상태에 저장
                st.session_state.last_search_result = {
                    'df': df,
                    'summary_stats': summary_stats,
                    'start_date': start_date,
                    'end_date': end_date,
                    'date_type': date_type,
                    'order_status': '전체',
                    'selected_hotel_ids': selected_hotel_ids,
                    'days_diff': days_diff
                }
                
                # 로깅: 데이터 조회 완료
                log_access("INFO", "숙소별 데이터 조회 완료", admin_id=admin_id, 
                          결과건수=len(df))
                
        except Exception as e:
            # 에러 로깅
            log_error("ERROR", "숙소별 데이터 조회 중 오류 발생", exception=e, admin_id=admin_id,
                     기간=f"{start_date}~{end_date}", 숙소수=len(selected_hotel_ids))
            
            st.error(f"❌ 데이터 조회 중 오류가 발생했습니다: {e}")
            st.exception(e)
            
            df = pd.DataFrame()
            summary_stats = {
                'total_bookings': 0,
                'total_revenue': 0,
                'hotel_count': 0,
                'active_days': 0
            }
            st.session_state.last_search_result = None
    else:
        # 이전 조회 결과 사용
        if st.session_state.last_search_result is not None:
            result = st.session_state.last_search_result
            df = result['df']
            summary_stats = result['summary_stats']
            start_date = result['start_date']
            end_date = result['end_date']
            date_type = result['date_type']
            order_status = result['order_status']  # '전체'
            days_diff = result['days_diff']
        else:
            # 이전 결과가 없으면 빈 결과
            df = pd.DataFrame()
            summary_stats = {
                'total_bookings': 0,
                'total_revenue': 0,
                'hotel_count': 0,
                'active_days': 0
            }
    
    # 결과 표시
    if df.empty:
        st.warning("⚠️ 조회된 데이터가 없습니다.")
        st.info("다른 날짜 범위, 날짜유형 또는 숙소를 선택해보세요.")
    else:
        # 요약 통계 표시
        st.subheader("📈 요약 통계")
        
        # 결과 데이터에서 합계 계산
        total_bookings = int(df['booking_count'].sum()) if 'booking_count' in df.columns else 0
        total_rooms = int(df['total_rooms'].sum()) if 'total_rooms' in df.columns else 0
        confirmed_rooms = int(df['confirmed_rooms'].sum()) if 'confirmed_rooms' in df.columns else 0
        cancelled_rooms = int(df['cancelled_rooms'].sum()) if 'cancelled_rooms' in df.columns else 0
        cancellation_rate = (cancelled_rooms / total_rooms * 100) if total_rooms > 0 else 0.0
        total_deposit = int(df['total_deposit'].sum()) if 'total_deposit' in df.columns else 0
        total_purchase = int(df['total_purchase'].sum()) if 'total_purchase' in df.columns else 0
        total_profit = int(df['total_profit'].sum()) if 'total_profit' in df.columns else 0
        
        # 1행: 총 예약건수 | 총 입금가 | 총 실구매가 | 총 수익
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("총 예약 건수", f"{total_bookings:,}건")
        with col2:
            st.metric("총 입금가", f"{total_deposit:,}")
        with col3:
            st.metric("총 실구매가", f"{total_purchase:,}")
        with col4:
            st.metric("총 수익", f"{total_profit:,}")
        
        # 2행: 총 객실수 | 확정 객실 수 | 취소 객실 수 | 취소율
        col5, col6, col7, col8 = st.columns(4)
        with col5:
            st.metric("총 객실수", f"{total_rooms:,}개")
        with col6:
            st.metric("확정 객실 수", f"{confirmed_rooms:,}개")
        with col7:
            st.metric("취소 객실 수", f"{cancelled_rooms:,}개")
        with col8:
            st.metric("취소율", f"{cancellation_rate:.1f}%")
        
        st.markdown("---")
        
        # 데이터 테이블 표시
        st.subheader("📋 상세 데이터")
        
        # 상위 10개만 표시 안내
        total_rows = len(df)
        if total_rows > 10:
            st.info(f"📊 상위 10개만 표시됩니다. 전체 데이터는 엑셀 다운로드를 이용하세요. (전체 {total_rows}개)")
        
        # 데이터 포맷팅
        display_df = df.copy()
        
        # 날짜 컬럼명 결정
        date_col_name = '구매일(예약일)' if date_type == 'orderDate' else '이용일(체크인)'
        
        # 날짜 포맷팅
        display_df['booking_date'] = pd.to_datetime(display_df['booking_date']).dt.strftime('%Y-%m-%d')
        
        # 컬럼명 한글화 및 순서 정리
        column_mapping = {
            'booking_date': date_col_name,
            'hotel_name': '숙소명',
            'channel_name': '채널명',
            'booking_count': '예약건수',
            'total_rooms': '총객실수',
            'confirmed_rooms': '확정객실수',
            'cancelled_rooms': '취소객실수',
            'cancellation_rate': '취소율',
            'total_deposit': '총 입금가',
            'total_purchase': '총 실구매가',
            'total_profit': '총 수익',
            'profit_rate': '수익률 (%)'
        }
        
        # 존재하는 컬럼만 매핑
        for old_col, new_col in column_mapping.items():
            if old_col in display_df.columns:
                display_df = display_df.rename(columns={old_col: new_col})
        
        # 컬럼 순서 정리
        desired_order = [
            date_col_name,
            '숙소명',
            '채널명',
            '예약건수',
            '총객실수',
            '확정객실수',
            '취소객실수',
            '취소율',
            '총 입금가',
            '총 실구매가',
            '총 수익',
            '수익률 (%)'
        ]
        
        # 존재하는 컬럼만 선택
        final_cols = [col for col in desired_order if col in display_df.columns]
        display_df = display_df[final_cols]
        
        # 숫자 포맷팅 (천단위 구분, 숫자만 표시)
        numeric_cols = ['예약건수', '총객실수', '확정객실수', '취소객실수', '총 입금가', '총 실구매가', '총 수익']
        for col in numeric_cols:
            if col in display_df.columns:
                display_df[col] = display_df[col].apply(lambda x: f"{int(x):,}" if pd.notna(x) else "0")
        
        # 취소율 포맷팅 (소수점 1자리, % 표시)
        if '취소율' in display_df.columns:
            display_df['취소율'] = display_df['취소율'].apply(
                lambda x: f"{float(x):.1f}%" if pd.notna(x) else "0.0%"
            )
        
        # 수익률 포맷팅 (소수점 1자리)
        if '수익률 (%)' in display_df.columns:
            display_df['수익률 (%)'] = display_df['수익률 (%)'].apply(
                lambda x: f"{float(x):.1f}%" if pd.notna(x) else "0.0%"
            )
        
        # 상위 10개만 표시
        display_df_top10 = display_df.head(10)
        
        st.dataframe(
            display_df_top10,
            use_container_width=True,
            hide_index=True
        )
        
        # 엑셀 다운로드
        st.markdown("---")
        st.subheader("💾 엑셀 다운로드")
        
        # date_type_display 재생성 (세션에서 가져온 경우를 대비)
        date_type_display_for_excel = {opt: get_date_type_display_name(opt) 
                                     for opt in date_type_options}
        
        summary_for_excel = {
            **summary_stats,
            'start_date': str(start_date),
            'end_date': str(end_date),
            'date_type': date_type_display_for_excel.get(date_type, date_type)
        }
        
        try:
            excel_data, filename = create_hotel_excel_download(
                df=df,  # 전체 데이터 (엑셀에는 전체 포함)
                summary_stats=summary_for_excel,
                date_type=date_type
            )
            
            st.download_button(
                label="📥 엑셀 파일 다운로드",
                data=excel_data,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            
            # 엑셀 다운로드 로깅
            log_access("INFO", "엑셀 다운로드", admin_id=admin_id, 파일명=filename)
        except Exception as e:
            log_error("ERROR", "엑셀 다운로드 실패", exception=e, admin_id=admin_id)
            st.error(f"❌ 엑셀 다운로드 중 오류가 발생했습니다: {e}")
        
        # 사용안내 (엑셀 다운로드 하단에 위치)
        st.markdown("---")
        with st.expander("📌 사용 안내", expanded=False):
            st.markdown("""
            **사용 방법:**
            1. **날짜유형 선택**: 이용일 또는 구매일 기준을 선택하세요
            2. **날짜 범위 선택**: 시작일과 종료일을 선택하세요 (최대 3개월)
               - 이용일 기준: 오늘 기준 90일 전 ~ 90일 후까지 선택 가능
               - 구매일 기준: 오늘 기준 90일 전 ~ 어제까지 선택 가능
            3. **숙소 검색**: 숙소명 또는 숙소코드를 입력하여 검색하세요 (최대 10개 선택 가능)
            4. **조회**: '조회' 버튼을 클릭하여 데이터를 조회합니다
            5. **초기화**: '초기화' 버튼을 클릭하여 모든 필터를 기본값으로 되돌립니다
            6. **엑셀 다운로드**: 조회 결과를 엑셀 파일로 다운로드할 수 있습니다
            
            **주의사항:**
            - 구매일 기준 조회 시 당일 데이터는 조회할 수 없습니다 (D-1까지만 조회 가능)
            - 조회 기간은 최대 90일(3개월)까지 가능합니다
            - 상세 데이터는 상위 10개만 표시되며, 전체 데이터는 엑셀 다운로드를 이용하세요
            - 예약상태는 상세 데이터에서 확인할 수 있습니다 (확정/취소 객실수, 취소율)
            """)

else:
    # 초기 화면: 사용 안내
    st.info("👈 왼쪽 사이드바에서 검색 조건을 입력하고 '조회' 버튼을 클릭하세요.")
    
    st.markdown("### 📌 사용 안내")
    st.markdown("""
    1. **날짜유형 선택**: 이용일 또는 구매일 기준을 선택하세요
    2. **날짜 범위 선택**: 시작일과 종료일을 선택하세요 (최대 3개월)
    3. **숙소 검색**: 숙소명 또는 숙소코드를 입력하여 검색하세요 (최대 10개 선택 가능)
    4. **조회**: '조회' 버튼을 클릭하여 데이터를 조회합니다
    5. **초기화**: '초기화' 버튼을 클릭하여 모든 필터를 기본값으로 되돌립니다
    6. **엑셀 다운로드**: 조회 결과를 엑셀 파일로 다운로드할 수 있습니다
    
    **주의사항**:
    - 당일 데이터는 조회할 수 없습니다 (D-1까지만 조회 가능)
    - 조회 기간은 최대 90일(3개월)까지 가능합니다
    - 상세 데이터는 상위 10개만 표시되며, 전체 데이터는 엑셀 다운로드를 이용하세요
    - 예약상태는 상세 데이터에서 확인할 수 있습니다 (확정/취소 객실수, 취소율)
    """)

# 푸터
st.markdown("---")
st.caption("숙소별 예약 통계 시스템 v1.1 | 개발 서버")


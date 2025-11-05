# app_v1.1.py
"""채널별 예약 통계 시스템 - Streamlit 메인 애플리케이션 v1.1
- 날짜유형 필터 추가 (date_type 시트 활용)
- 예약상태 필터 추가 (order_status 시트 활용)
- 초기화 버튼 추가
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import importlib.util
import sys
import os

# v1.1 모듈 import
_data_fetcher_path = os.path.join(os.path.dirname(__file__), 'utils', 'data_fetcher_v1.1.py')
spec = importlib.util.spec_from_file_location("data_fetcher_v1_1", _data_fetcher_path)
data_fetcher_v1_1 = importlib.util.module_from_spec(spec)
sys.modules["data_fetcher_v1_1"] = data_fetcher_v1_1
spec.loader.exec_module(data_fetcher_v1_1)

from data_fetcher_v1_1 import (  # type: ignore
    fetch_channel_data,
    fetch_summary_stats,
    fetch_channel_list
)
from utils.excel_handler import create_excel_download
from config.master_data_loader import (
    get_date_type_options,
    get_date_type_display_name,
    get_order_status_options
)

# 페이지 설정
st.set_page_config(
    page_title="채널별 예약 통계",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 제목
st.title("📊 채널별 예약 통계 시스템")
st.markdown("---")

# 기본값 설정
default_end = date.today() - timedelta(days=1)  # 어제까지 (당일 제외)
default_start = default_end - timedelta(days=6)  # 최근 7일
default_date_type = '전체'
default_order_status = '전체'

# 사이드바: 검색 조건
with st.sidebar:
    st.header("🔍 검색 조건")
    
    # 날짜 범위
    st.subheader("날짜 범위")
    
    # 날짜유형 선택
    date_type_options = get_date_type_options()
    
    # 디버깅: 날짜유형 옵션이 제대로 로드되었는지 확인
    if len(date_type_options) <= 1:
        st.warning("⚠️ 날짜유형 데이터를 불러올 수 없습니다. master_data.xlsx의 date_types 시트를 확인하세요.")
        # 기본값으로 하드코딩된 옵션 제공
        date_type_options = ['전체', 'useDate', 'orderDate']
    
    date_type_display = {opt: opt if opt == '전체' else get_date_type_display_name(opt) 
                         for opt in date_type_options}
    
    # 세션 상태 초기화
    if 'date_type' not in st.session_state:
        st.session_state.date_type = default_date_type
    if 'order_status' not in st.session_state:
        st.session_state.order_status = default_order_status
    if 'start_date' not in st.session_state:
        st.session_state.start_date = default_start
    if 'end_date' not in st.session_state:
        st.session_state.end_date = default_end
    if 'selected_channels' not in st.session_state:
        st.session_state.selected_channels = ['전체']
    
    date_type = st.selectbox(
        "날짜유형",
        options=date_type_options,
        index=0 if default_date_type in date_type_options else 0,
        format_func=lambda x: date_type_display[x],
        help="이용일 또는 구매일 기준으로 조회할 수 있습니다. '전체'는 둘 다 포함합니다.",
        key='date_type_select'
    )
    
    start_date = st.date_input(
        "시작일",
        value=st.session_state.start_date,
        max_value=date.today() - timedelta(days=1),
        help="당일 데이터는 조회할 수 없습니다 (D-1까지만 조회 가능)",
        key='start_date_input'
    )
    
    end_date = st.date_input(
        "종료일",
        value=st.session_state.end_date,
        max_value=date.today() - timedelta(days=1),
        help="당일 데이터는 조회할 수 없습니다 (D-1까지만 조회 가능)",
        key='end_date_input'
    )
    
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
    
    # 채널 선택
    st.subheader("채널 선택")
    
    # 채널 목록을 캐싱하여 DB 연결 부하 감소
    @st.cache_data(ttl=3600)  # 1시간 캐시
    def get_cached_channel_list():
        try:
            return fetch_channel_list()
        except Exception as e:
            st.error(f"❌ 채널 목록 조회 실패: {e}")
            return ['전체']  # 기본값 반환
    
    try:
        channel_list = get_cached_channel_list()
        
        if not channel_list or channel_list == ['전체']:
            st.warning("⚠️ 채널 목록을 불러올 수 없습니다. 기본 채널만 사용됩니다.")
            channel_list = ['전체']
        
        selected_channels = st.multiselect(
            "조회할 채널을 선택하세요",
            options=channel_list,
            default=st.session_state.selected_channels if '전체' in st.session_state.selected_channels else ['전체'] if '전체' in channel_list else [],
            help="여러 채널을 선택할 수 있습니다. '전체'를 선택하면 모든 채널이 조회됩니다.",
            key='channel_select'
        )
        
        if not selected_channels:
            st.warning("⚠️ 최소 1개 이상의 채널을 선택해주세요.")
            st.stop()
        
        if '전체' in selected_channels:
            selected_channels = channel_list[1:]  # '전체' 제외
        
    except Exception as e:
        st.error(f"❌ 채널 목록 조회 오류: {e}")
        st.stop()
    
    # 예약상태 선택
    st.subheader("예약상태")
    order_status_options = get_order_status_options()
    order_status = st.selectbox(
        "예약상태를 선택하세요",
        options=order_status_options,
        index=0,
        help="'전체'는 모든 상태를, '확정'은 확정 그룹의 모든 상태를, '취소'는 취소 그룹의 모든 상태를 조회합니다.",
        key='order_status_select'
    )
    
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
        st.session_state.order_status = default_order_status
        st.session_state.start_date = default_start
        st.session_state.end_date = default_end
        st.session_state.selected_channels = ['전체']
        # 초기화 시 필터만 초기화하고 결과 화면은 유지 (저장된 결과는 삭제하지 않음)
        st.rerun()

# 메인 영역
# 조회 버튼이 클릭되었거나, 이전 조회 결과가 있는 경우 결과 표시
has_search_result = 'last_search_result' in st.session_state and st.session_state.last_search_result is not None
should_show_result = search_button or has_search_result

if should_show_result:
    # 검색 조건 표시
    with st.container():
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("조회 기간", f"{start_date} ~ {end_date}")
        with col2:
            st.metric("날짜유형", date_type_display.get(date_type, date_type))
        with col3:
            st.metric("예약상태", order_status)
        with col4:
            st.metric("조회 일수", f"{days_diff}일")
    
    st.markdown("---")
    
    # 조회 버튼이 클릭된 경우에만 새로 조회
    if search_button:
        # 데이터 조회
        with st.spinner("데이터를 조회하는 중..."):
            try:
                # 채널별 데이터 조회
                df = fetch_channel_data(
                    start_date=start_date,
                    end_date=end_date,
                    selected_channels=selected_channels,
                    date_type=date_type,
                    order_status=order_status
                )
                
                # 요약 통계 조회
                summary_stats = fetch_summary_stats(
                    start_date, 
                    end_date, 
                    date_type=date_type,
                    order_status=order_status
                )
                
                # 조회 결과를 세션 상태에 저장
                st.session_state.last_search_result = {
                    'df': df,
                    'summary_stats': summary_stats,
                    'start_date': start_date,
                    'end_date': end_date,
                    'date_type': date_type,
                    'order_status': order_status,
                    'selected_channels': selected_channels,
                    'days_diff': days_diff
                }
                
            except Exception as e:
                st.error(f"❌ 데이터 조회 중 오류가 발생했습니다: {e}")
                st.exception(e)
                df = pd.DataFrame()
                summary_stats = {
                    'total_bookings': 0,
                    'total_revenue': 0,
                    'channel_count': 0,
                    'active_days': 0
                }
                st.session_state.last_search_result = None
                # 오류 발생 시 빈 DataFrame으로 표시
                df = pd.DataFrame()
                summary_stats = {
                    'total_bookings': 0,
                    'total_revenue': 0,
                    'channel_count': 0,
                    'active_days': 0
                }
    else:
        # 이전 조회 결과 사용
        if st.session_state.last_search_result is not None:
            result = st.session_state.last_search_result
            df = result['df']
            summary_stats = result['summary_stats']
            start_date = result['start_date']
            end_date = result['end_date']
            date_type = result['date_type']
            order_status = result['order_status']
            days_diff = result['days_diff']
        else:
            # 이전 결과가 없으면 빈 결과
            df = pd.DataFrame()
            summary_stats = {
                'total_bookings': 0,
                'total_revenue': 0,
                'channel_count': 0,
                'active_days': 0
            }
    
    # 결과 표시
    if df.empty:
        st.warning("⚠️ 조회된 데이터가 없습니다.")
        st.info("다른 날짜 범위, 날짜유형, 예약상태 또는 채널을 선택해보세요.")
    else:
        # 요약 통계 표시
        st.subheader("📈 요약 통계")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("총 예약 건수", f"{summary_stats.get('total_bookings', 0):,}건")
        with col2:
            st.metric("총 매출액", f"{summary_stats.get('total_revenue', 0):,.0f}원")
        with col3:
            st.metric("조회 채널 수", f"{df['channel_name'].nunique()}개")
        with col4:
            st.metric("데이터 건수", f"{len(df):,}건")
        
        st.markdown("---")
        
        # 데이터 테이블 표시
        st.subheader("📋 상세 데이터")
        
        # 데이터 포맷팅
        display_df = df.copy()
        display_df['booking_date'] = pd.to_datetime(display_df['booking_date']).dt.strftime('%Y-%m-%d')
        display_df['total_amount'] = display_df['total_amount'].apply(lambda x: f"{int(x):,}" if pd.notna(x) else "0")
        
        # 컬럼명 한글화
        display_df.columns = ['예약일', '채널명', '채널코드', '예약건수', '총금액', '데이터소스']
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
        
        # 엑셀 다운로드
        st.markdown("---")
        st.subheader("💾 엑셀 다운로드")
        
        # date_type_display 재생성 (세션에서 가져온 경우를 대비)
        date_type_display_for_excel = {opt: opt if opt == '전체' else get_date_type_display_name(opt) 
                                     for opt in date_type_options}
        
        summary_for_excel = {
            **summary_stats,
            'start_date': str(start_date),
            'end_date': str(end_date),
            'date_type': date_type_display_for_excel.get(date_type, date_type),
            'order_status': order_status
        }
        
        excel_data, filename = create_excel_download(
            df=df,
            summary_stats=summary_for_excel
        )
        
        st.download_button(
            label="📥 엑셀 파일 다운로드",
            data=excel_data,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

else:
    # 초기 화면: 사용 안내
    st.info("👈 왼쪽 사이드바에서 검색 조건을 입력하고 '조회' 버튼을 클릭하세요.")
    
    st.markdown("### 📌 사용 안내")
    st.markdown("""
    1. **날짜유형 선택**: 이용일 또는 구매일 기준을 선택하세요
    2. **날짜 범위 선택**: 시작일과 종료일을 선택하세요 (최대 3개월)
    3. **채널 선택**: 조회할 채널을 선택하세요 (여러 개 선택 가능)
    4. **예약상태 선택**: 전체, 확정, 또는 취소를 선택하세요
    5. **조회**: '조회' 버튼을 클릭하여 데이터를 조회합니다
    6. **초기화**: '초기화' 버튼을 클릭하여 모든 필터를 기본값으로 되돌립니다
    7. **엑셀 다운로드**: 조회 결과를 엑셀 파일로 다운로드할 수 있습니다
    
    **주의사항**:
    - 당일 데이터는 조회할 수 없습니다 (D-1까지만 조회 가능)
    - 조회 기간은 최대 90일(3개월)까지 가능합니다
    - 날짜유형이 '전체'인 경우, 이용일 또는 구매일 중 하나라도 범위 안에 있으면 조회됩니다
    """)

# 푸터
st.markdown("---")
st.caption("채널별 예약 통계 시스템 v1.1 | 개발 서버")


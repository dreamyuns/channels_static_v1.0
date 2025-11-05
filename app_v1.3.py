# app_v1.3.py
"""채널별 예약 통계 시스템 - Streamlit 메인 애플리케이션 v1.3
- terms*room_cnt 계산, 확정/취소 객실수, 취소율 추가
- 예약상태 필터 UI 제거 (백엔드는 항상 '전체'로 고정)
- 요약통계 레이아웃 변경
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import importlib.util
import sys
import os

# v1.3 모듈 import
_data_fetcher_path = os.path.join(os.path.dirname(__file__), 'utils', 'data_fetcher_v1.3.py')
spec = importlib.util.spec_from_file_location("data_fetcher_v1_3", _data_fetcher_path)
data_fetcher_v1_3 = importlib.util.module_from_spec(spec)
sys.modules["data_fetcher_v1_3"] = data_fetcher_v1_3
spec.loader.exec_module(data_fetcher_v1_3)

from data_fetcher_v1_3 import (  # type: ignore
    fetch_channel_data,
    fetch_summary_stats,
    fetch_channel_list
)

# v1.3 excel_handler 동적 import (점이 포함된 파일명)
_excel_handler_path = os.path.join(os.path.dirname(__file__), 'utils', 'excel_handler_v1.3.py')
spec_excel = importlib.util.spec_from_file_location("excel_handler_v1_3", _excel_handler_path)
excel_handler_v1_3 = importlib.util.module_from_spec(spec_excel)
sys.modules["excel_handler_v1_3"] = excel_handler_v1_3
spec_excel.loader.exec_module(excel_handler_v1_3)

from excel_handler_v1_3 import create_excel_download  # type: ignore

from config.master_data_loader import (
    get_date_type_options,
    get_date_type_display_name
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
default_date_type = 'orderDate'  # 구매일이 기본값
# 예약상태는 항상 '전체'로 고정
order_status = '전체'

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
    if 'selected_channels' not in st.session_state:
        st.session_state.selected_channels = ['전체']
    
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
        
        # 세션 상태에서 채널 기본값 설정
        channel_default = st.session_state.selected_channels if 'selected_channels' in st.session_state else (['전체'] if '전체' in channel_list else [])
        
        selected_channels = st.multiselect(
            "조회할 채널을 선택하세요",
            options=channel_list,
            default=channel_default,
            help="여러 채널을 선택할 수 있습니다. '전체'를 선택하면 모든 채널이 조회됩니다.",
            key='channel_select'
        )
        
        if not selected_channels:
            st.warning("⚠️ 최소 1개 이상의 채널을 선택해주세요.")
            st.stop()
        
        # 세션 상태에 원본 선택값 저장 (쿼리 실행 전)
        st.session_state.selected_channels = selected_channels
        
    except Exception as e:
        st.error(f"❌ 채널 목록 조회 오류: {e}")
        st.stop()
    
    # 예약상태 필터 제거됨 (UI에서 숨김, 백엔드는 항상 '전체'로 고정)
    
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
        st.session_state.selected_channels = ['전체']
        # 초기화 시 필터만 초기화하고 결과 화면은 유지 (저장된 결과는 삭제하지 않음)
        st.rerun()

# 메인 영역
# 조회 버튼이 클릭되었거나, 이전 조회 결과가 있는 경우 결과 표시
has_search_result = 'last_search_result' in st.session_state and st.session_state.last_search_result is not None
should_show_result = search_button or has_search_result

if should_show_result:
    # 조회 버튼이 클릭된 경우에만 새로 조회
    if search_button:
        # 데이터 조회
        with st.spinner("데이터를 조회하는 중..."):
            try:
                # 채널별 데이터 조회 (쿼리용 채널 리스트 사용)
                # 채널 목록 다시 가져오기
                channel_list_for_query = get_cached_channel_list()
                query_channels = channel_list_for_query[1:] if '전체' in selected_channels else selected_channels
                df = fetch_channel_data(
                    start_date=start_date,
                    end_date=end_date,
                    selected_channels=query_channels,
                    date_type=date_type,
                    order_status='전체'  # 항상 '전체'로 고정
                )
                
                # 요약 통계 조회
                summary_stats = fetch_summary_stats(
                    start_date, 
                    end_date, 
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
                    'order_status': '전체',  # 항상 '전체'
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
                'channel_count': 0,
                'active_days': 0
            }
    
    # 결과 표시
    if df.empty:
        st.warning("⚠️ 조회된 데이터가 없습니다.")
        st.info("다른 날짜 범위, 날짜유형 또는 채널을 선택해보세요.")
    else:
        # 요약 통계 표시
        st.subheader("📈 요약 통계")
        
        # 결과 데이터에서 합계 계산
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
            st.metric("총 예약 건수", f"{summary_stats.get('total_bookings', 0):,}건")
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
            'channel_name': '채널명',
            'hotel_count': '판매숙소수',
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
            '채널명',
            '판매숙소수',
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
        numeric_cols = ['판매숙소수', '예약건수', '총객실수', '확정객실수', '취소객실수', '총 입금가', '총 실구매가', '총 수익']
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
        
        excel_data, filename = create_excel_download(
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

else:
    # 초기 화면: 사용 안내
    st.info("👈 왼쪽 사이드바에서 검색 조건을 입력하고 '조회' 버튼을 클릭하세요.")
    
    st.markdown("### 📌 사용 안내")
    st.markdown("""
    1. **날짜유형 선택**: 이용일 또는 구매일 기준을 선택하세요
    2. **날짜 범위 선택**: 시작일과 종료일을 선택하세요 (최대 3개월)
    3. **채널 선택**: 조회할 채널을 선택하세요 (여러 개 선택 가능)
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
st.caption("채널별 예약 통계 시스템 v1.3 | 개발 서버")


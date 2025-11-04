# app.py
"""채널별 예약 통계 시스템 - Streamlit 메인 애플리케이션"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
from utils.data_fetcher import (
    fetch_channel_data,
    fetch_summary_stats,
    fetch_channel_list
)
from utils.excel_handler import create_excel_download

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

# 사이드바: 검색 조건
with st.sidebar:
    st.header("🔍 검색 조건")
    
    # 날짜 선택
    st.subheader("날짜 범위")
    
    # 기본값: 최근 7일
    default_end = date.today() - timedelta(days=1)  # 어제까지 (당일 제외)
    default_start = default_end - timedelta(days=6)  # 최근 7일
    
    start_date = st.date_input(
        "시작일",
        value=default_start,
        max_value=date.today() - timedelta(days=1),
        help="당일 데이터는 조회할 수 없습니다 (D-1까지만 조회 가능)"
    )
    
    end_date = st.date_input(
        "종료일",
        value=default_end,
        max_value=date.today() - timedelta(days=1),
        help="당일 데이터는 조회할 수 없습니다 (D-1까지만 조회 가능)"
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
    
    try:
        channel_list = fetch_channel_list()
        
        if not channel_list:
            st.error("❌ 채널 목록을 불러올 수 없습니다.")
            st.stop()
        
        selected_channels = st.multiselect(
            "조회할 채널을 선택하세요",
            options=channel_list,
            default=['전체'] if '전체' in channel_list else [],
            help="여러 채널을 선택할 수 있습니다. '전체'를 선택하면 모든 채널이 조회됩니다."
        )
        
        if not selected_channels:
            st.warning("⚠️ 최소 1개 이상의 채널을 선택해주세요.")
            st.stop()
        
        if '전체' in selected_channels:
            selected_channels = channel_list[1:]  # '전체' 제외
        
    except Exception as e:
        st.error(f"❌ 채널 목록 조회 오류: {e}")
        st.stop()
    
    # 조회 버튼
    st.markdown("---")
    search_button = st.button("🔍 조회", type="primary", use_container_width=True)

# 메인 영역
if search_button:
    # 검색 조건 표시
    with st.container():
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("조회 기간", f"{start_date} ~ {end_date}")
        with col2:
            st.metric("선택된 채널", f"{len(selected_channels)}개")
        with col3:
            st.metric("조회 일수", f"{days_diff}일")
    
    st.markdown("---")
    
    # 데이터 조회
    with st.spinner("데이터를 조회하는 중..."):
        try:
            # 채널별 데이터 조회
            df = fetch_channel_data(
                start_date=start_date,
                end_date=end_date,
                selected_channels=selected_channels
            )
            
            # 요약 통계 조회
            summary_stats = fetch_summary_stats(start_date, end_date)
            
            if df.empty:
                st.warning("⚠️ 조회된 데이터가 없습니다.")
                st.info("다른 날짜 범위나 채널을 선택해보세요.")
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
                
                summary_for_excel = {
                    **summary_stats,
                    'start_date': str(start_date),
                    'end_date': str(end_date)
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
                
        except Exception as e:
            st.error(f"❌ 데이터 조회 중 오류가 발생했습니다: {e}")
            st.exception(e)

else:
    # 초기 화면: 사용 안내
    st.info("👈 왼쪽 사이드바에서 검색 조건을 입력하고 '조회' 버튼을 클릭하세요.")
    
    st.markdown("### 📌 사용 안내")
    st.markdown("""
    1. **날짜 범위 선택**: 시작일과 종료일을 선택하세요 (최대 3개월)
    2. **채널 선택**: 조회할 채널을 선택하세요 (여러 개 선택 가능)
    3. **조회**: '조회' 버튼을 클릭하여 데이터를 조회합니다
    4. **엑셀 다운로드**: 조회 결과를 엑셀 파일로 다운로드할 수 있습니다
    
    **주의사항**:
    - 당일 데이터는 조회할 수 없습니다 (D-1까지만 조회 가능)
    - 조회 기간은 최대 90일(3개월)까지 가능합니다
    """)

# 푸터
st.markdown("---")
st.caption("채널별 예약 통계 시스템 v1.0 | 개발 서버")


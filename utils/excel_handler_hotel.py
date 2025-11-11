# utils/excel_handler_hotel.py
"""숙소별 엑셀 파일 생성 및 다운로드 처리
- 날짜별 + 숙소별 + 채널별 집계
- order_item.due_price 사용 (입금가)
"""

import pandas as pd
from io import BytesIO
from datetime import datetime

def create_hotel_excel_file(df, summary_stats=None, sheet_name='구매일', date_type='orderDate'):
    """
    숙소별 DataFrame을 엑셀 파일로 변환
    
    Args:
        df: pandas DataFrame (조회 결과 데이터)
        summary_stats: dict (요약 통계 정보, 선택사항)
        sheet_name: str (시트 이름 - '구매일' 또는 '이용일')
        date_type: str (날짜유형 - 'orderDate' 또는 'useDate')
    
    Returns:
        BytesIO: 엑셀 파일 바이너리 데이터
    """
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # 요약 통계 시트 추가 (선택사항)
        if summary_stats:
            summary_df = pd.DataFrame([{
                '항목': '총 예약 건수',
                '값': f"{summary_stats.get('total_bookings', 0):,}건"
            }, {
                '항목': '총 입금가',
                '값': f"{summary_stats.get('total_revenue', 0):,.0f}"
            }, {
                '항목': '조회 숙소 수',
                '값': f"{summary_stats.get('hotel_count', 0)}개"
            }, {
                '항목': '조회 기간',
                '값': f"{summary_stats.get('start_date', '')} ~ {summary_stats.get('end_date', '')}"
            }, {
                '항목': '날짜유형',
                '값': summary_stats.get('date_type', '구매일')
            }, {
                '항목': '생성 일시',
                '값': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }])
            summary_df.to_excel(writer, sheet_name='요약', index=False)
        
        # 메인 데이터 시트
        if not df.empty:
            # 데이터 복사 (원본 수정 방지)
            export_df = df.copy()
            
            # 날짜 컬럼명 결정
            date_col_name = '구매일(예약일)' if date_type == 'orderDate' else '이용일(체크인)'
            
            # 컬럼명 한글화 및 순서 정리
            column_mapping = {
                'booking_date': date_col_name,
                'hotel_name': '숙소명',
                'hotel_code': '숙소코드',
                'channel_name': '채널명',
                'channel_code': '채널코드',  # 내부용, 필요시 숨김 가능
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
            existing_cols = {k: v for k, v in column_mapping.items() if k in export_df.columns}
            export_df.rename(columns=existing_cols, inplace=True)
            
            # 컬럼 순서 정리
            desired_order = [
                date_col_name,
                '숙소명',
                '숙소코드',
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
            final_cols = [col for col in desired_order if col in export_df.columns]
            export_df = export_df[final_cols]
            
            # 날짜 포맷팅
            if date_col_name in export_df.columns:
                export_df[date_col_name] = pd.to_datetime(export_df[date_col_name]).dt.strftime('%Y-%m-%d')
            
            # 숫자 포맷팅 (천단위 구분, 숫자만 표시)
            numeric_cols = ['예약건수', '총객실수', '확정객실수', '취소객실수', '총 입금가', '총 실구매가', '총 수익']
            for col in numeric_cols:
                if col in export_df.columns:
                    export_df[col] = export_df[col].apply(lambda x: f"{int(x):,}" if pd.notna(x) else "0")
            
            # 취소율 포맷팅 (소수점 1자리, % 표시)
            if '취소율' in export_df.columns:
                export_df['취소율'] = export_df['취소율'].apply(
                    lambda x: f"{float(x):.1f}%" if pd.notna(x) else "0.0%"
                )
            
            # 수익률 포맷팅 (소수점 1자리)
            if '수익률 (%)' in export_df.columns:
                export_df['수익률 (%)'] = export_df['수익률 (%)'].apply(
                    lambda x: f"{float(x):.1f}%" if pd.notna(x) else "0.0%"
                )
            
            export_df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # 열 너비 자동 조정을 위한 설정
            worksheet = writer.sheets[sheet_name]
            for idx, col in enumerate(export_df.columns, 1):
                max_length = max(
                    export_df[col].astype(str).apply(len).max(),
                    len(str(col))
                )
                # 열 인덱스를 알파벳으로 변환 (A, B, C, ...)
                col_letter = chr(64 + idx) if idx <= 26 else chr(64 + (idx - 1) // 26) + chr(64 + ((idx - 1) % 26) + 1)
                worksheet.column_dimensions[col_letter].width = min(max_length + 2, 50)
        else:
            # 데이터가 없을 때 빈 시트 생성
            empty_df = pd.DataFrame({'메시지': ['조회된 데이터가 없습니다.']})
            empty_df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    output.seek(0)
    return output

def create_hotel_excel_download(df, summary_stats=None, filename=None, date_type='orderDate'):
    """
    Streamlit용 숙소별 엑셀 다운로드 파일 생성
    
    Args:
        df: pandas DataFrame
        summary_stats: dict (요약 통계)
        filename: str (파일명, 없으면 자동 생성)
        date_type: str (날짜유형 - 'orderDate' 또는 'useDate')
    
    Returns:
        tuple: (파일 바이너리, 파일명)
    """
    # 날짜유형에 따른 시트명 결정
    sheet_name = '구매일' if date_type == 'orderDate' else '이용일'
    
    # 파일명 생성
    if filename is None:
        now = datetime.now()
        date_str = now.strftime('%Y%m%d')
        time_str = now.strftime('%H%M%S')
        filename = f'숙소별_예약통계_{date_str}_{time_str}.xlsx'
    
    excel_file = create_hotel_excel_file(df, summary_stats, sheet_name, date_type)
    
    return excel_file.getvalue(), filename


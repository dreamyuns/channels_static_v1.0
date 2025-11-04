# utils/excel_handler.py
"""엑셀 파일 생성 및 다운로드 처리"""

import pandas as pd
from io import BytesIO
from datetime import datetime

def create_excel_file(df, summary_stats=None, sheet_name='채널별 통계'):
    """
    DataFrame을 엑셀 파일로 변환
    
    Args:
        df: pandas DataFrame (조회 결과 데이터)
        summary_stats: dict (요약 통계 정보, 선택사항)
        sheet_name: str (시트 이름)
    
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
                '항목': '총 매출액',
                '값': f"{summary_stats.get('total_revenue', 0):,.0f}원"
            }, {
                '항목': '조회 채널 수',
                '값': f"{summary_stats.get('channel_count', 0)}개"
            }, {
                '항목': '조회 기간',
                '값': f"{summary_stats.get('start_date', '')} ~ {summary_stats.get('end_date', '')}"
            }, {
                '항목': '생성 일시',
                '값': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }])
            summary_df.to_excel(writer, sheet_name='요약', index=False)
        
        # 메인 데이터 시트
        if not df.empty:
            # 데이터 복사 (원본 수정 방지)
            export_df = df.copy()
            
            # 컬럼명 한글화 (영문 컬럼명이 있는 경우)
            column_mapping = {
                'booking_date': '예약일',
                'channel_name': '채널명',
                'channel_code': '채널코드',
                'booking_count': '예약건수',
                'total_amount': '총금액',
                'data_sources': '데이터소스'
            }
            
            export_df.rename(columns=column_mapping, inplace=True)
            
            # 금액 포맷팅 (천단위 구분)
            if '총금액' in export_df.columns:
                export_df['총금액'] = export_df['총금액'].apply(lambda x: f"{int(x):,}" if pd.notna(x) else "0")
            
            export_df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # 열 너비 자동 조정을 위한 설정
            worksheet = writer.sheets[sheet_name]
            for idx, col in enumerate(export_df.columns, 1):
                max_length = max(
                    export_df[col].astype(str).apply(len).max(),
                    len(str(col))
                )
                worksheet.column_dimensions[chr(64 + idx)].width = min(max_length + 2, 50)
        else:
            # 데이터가 없을 때 빈 시트 생성
            empty_df = pd.DataFrame({'메시지': ['조회된 데이터가 없습니다.']})
            empty_df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    output.seek(0)
    return output

def create_excel_download(df, summary_stats=None, filename=None):
    """
    Streamlit용 엑셀 다운로드 파일 생성
    
    Args:
        df: pandas DataFrame
        summary_stats: dict (요약 통계)
        filename: str (파일명, 없으면 자동 생성)
    
    Returns:
        tuple: (파일 바이너리, 파일명)
    """
    if filename is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'채널별_예약통계_{timestamp}.xlsx'
    
    excel_file = create_excel_file(df, summary_stats)
    
    return excel_file.getvalue(), filename


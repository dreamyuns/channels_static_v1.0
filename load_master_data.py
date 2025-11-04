# load_master_data.py
"""master_data.xlsx의 channels 시트를 읽어서 매핑 정보 확인"""

import pandas as pd
import os

def load_channel_mapping():
    """master_data.xlsx의 channels 시트에서 ID-채널 매핑 로드"""
    
    excel_path = os.path.join(os.path.dirname(__file__), "master_data.xlsx")
    
    if not os.path.exists(excel_path):
        print(f"File not found: {excel_path}")
        return None
    
    try:
        df = pd.read_excel(excel_path, sheet_name='channels')
        print(f"Loaded {len(df)} channel mappings")
        print("\nColumns:", df.columns.tolist())
        print("\nFirst 30 rows:")
        print(df.head(30))
        
        # ID -> 채널명 딕셔너리 생성
        channel_id_to_name = {}
        for idx, row in df.iterrows():
            channel_id = int(row['ID']) if pd.notna(row['ID']) else None
            channel_name = str(row['channels']) if pd.notna(row['channels']) else None
            if channel_id and channel_name:
                channel_id_to_name[channel_id] = channel_name
        
        print(f"\nTotal {len(channel_id_to_name)} valid mappings")
        return df, channel_id_to_name
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None, None

if __name__ == "__main__":
    df, mapping = load_channel_mapping()
    if df is not None:
        print(f"\nTotal {len(df)} channel mappings found.")


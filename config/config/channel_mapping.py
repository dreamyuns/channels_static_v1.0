# config/channel_mapping.py
"""master_data.xlsx의 channels 시트를 활용한 채널 매핑"""

import pandas as pd
import os

# 프로젝트 루트 디렉토리
_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_dir)
_excel_path = os.path.join(_project_root, "master_data.xlsx")

# 매핑 데이터 캐시
_channel_id_to_name = None
_channel_name_to_ids = None

def load_master_data_mapping():
    """master_data.xlsx의 channels 시트에서 ID-채널 매핑 로드"""
    global _channel_id_to_name, _channel_name_to_ids
    
    if _channel_id_to_name is not None:
        return _channel_id_to_name, _channel_name_to_ids
    
    _channel_id_to_name = {}
    _channel_name_to_ids = {}
    
    if not os.path.exists(_excel_path):
        return _channel_id_to_name, _channel_name_to_ids
    
    try:
        df = pd.read_excel(_excel_path, sheet_name='channels')
        
        for idx, row in df.iterrows():
            channel_id = row['ID']
            channel_name = row['channels']
            
            if pd.notna(channel_id) and pd.notna(channel_name):
                channel_id = int(channel_id)
                channel_name = str(channel_name).strip()
                
                # ID -> 채널명 매핑
                _channel_id_to_name[channel_id] = channel_name
                
                # 채널명 -> ID 리스트 매핑 (같은 이름이 여러 ID에 있을 수 있음)
                if channel_name not in _channel_name_to_ids:
                    _channel_name_to_ids[channel_name] = []
                if channel_id not in _channel_name_to_ids[channel_name]:
                    _channel_name_to_ids[channel_name].append(channel_id)
    except Exception as e:
        print(f"Warning: Could not load master_data.xlsx: {e}")
    
    return _channel_id_to_name, _channel_name_to_ids

def get_channel_ids_by_name(channel_name):
    """채널명으로 ID 리스트 조회"""
    _, channel_name_to_ids = load_master_data_mapping()
    return channel_name_to_ids.get(channel_name, [])

def get_channel_name_by_id(channel_id):
    """ID로 채널명 조회"""
    channel_id_to_name, _ = load_master_data_mapping()
    return channel_id_to_name.get(int(channel_id), None)


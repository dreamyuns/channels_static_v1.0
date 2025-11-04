# config/database.py
"""데이터베이스 연결 설정 및 테스트"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
import pandas as pd
import pymysql

# 프로젝트 루트 디렉토리 찾기 (현재 파일의 위치에서 계산)
_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_dir)
_env_path = os.path.join(_project_root, '.env')

# .env 파일 로드 (프로젝트 루트에서)
# 절대 경로로 .env 파일 찾기
if os.path.exists(_env_path):
    load_dotenv(dotenv_path=_env_path, override=True)
else:
    # 프로젝트 루트에 없으면 현재 작업 디렉토리에서 찾기
    load_dotenv(override=True)

def get_db_connection():
    """데이터베이스 연결 객체 반환"""
    # 환경변수에서 DB 정보 읽기
    db_config = {
        'host': os.getenv('DB_HOST'),
        'port': int(os.getenv('DB_PORT', 3306)),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'database': os.getenv('DB_NAME')
    }
    
    # 필수 정보 확인
    missing = [k for k, v in db_config.items() if not v or v == 'None']
    if missing:
        raise ValueError(f"Missing database configuration: {', '.join(missing)}. Please check .env file.")
    
    # MySQL 연결 문자열 생성
    connection_string = (
        f"mysql+pymysql://{db_config['user']}:{db_config['password']}@"
        f"{db_config['host']}:{db_config['port']}/{db_config['database']}"
    )
    
    # 한글 처리를 위한 charset 추가
    connection_string += "?charset=utf8mb4"
    
    try:
        engine = create_engine(
            connection_string,
            pool_pre_ping=True,  # 연결 상태 자동 확인
            pool_recycle=3600,   # 1시간마다 연결 재활용
            echo=False            # SQL 로그 출력 (디버깅시 True)
        )
        return engine
    except Exception as e:
        print(f"❌ DB 연결 생성 실패: {e}")
        raise

def test_connection():
    """DB 연결 테스트"""
    print("="*50)
    print("📊 DB 연결 테스트 시작")
    print("="*50)
    
    try:
        # 1. 기본 연결 테스트
        engine = get_db_connection()
        df = pd.read_sql("SELECT 1 as test", engine)
        print("✅ 기본 연결 성공!")
        
        # 2. 테이블 존재 확인
        print("\n테이블 확인 중...")
        
        tables_to_check = [
            'order_product',
            'booking_master_offer',
            'common_code'
        ]
        
        for table in tables_to_check:
            query = f"SELECT COUNT(*) as cnt FROM {table} LIMIT 1"
            try:
                df = pd.read_sql(query, engine)
                print(f"  ✅ {table}: 접근 가능")
            except Exception as e:
                print(f"  ❌ {table}: {e}")
        
        # 3. 채널 목록 조회 테스트
        print("\n채널 데이터 확인 중...")
        
        # common_code에서 채널 목록
        query_channels = """
        SELECT 
            code_id,
            code_name
        FROM common_code
        WHERE parent_idx = 1
        LIMIT 5
        """
        
        df_channels = pd.read_sql(query_channels, engine)
        print(f"  ✅ common_code 채널 수: {len(df_channels)}개")
        if not df_channels.empty:
            print("\n  샘플 채널 목록:")
            for idx, row in df_channels.iterrows():
                print(f"    - [{row['code_id']}] {row['code_name']}")
        
        # 4. 예약 데이터 확인
        print("\n예약 데이터 확인 중...")
        
        # order_product 최근 데이터
        query_recent = """
        SELECT 
            DATE(create_date) as date,
            COUNT(*) as count
        FROM order_product
        WHERE create_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            AND create_date < CURDATE()
        GROUP BY DATE(create_date)
        ORDER BY date DESC
        LIMIT 3
        """
        
        df_recent = pd.read_sql(query_recent, engine)
        if not df_recent.empty:
            print("  ✅ 최근 예약 현황:")
            for idx, row in df_recent.iterrows():
                print(f"    - {row['date']}: {row['count']:,}건")
        
        print("\n" + "="*50)
        print("🎉 DB 연결 테스트 완료!")
        print("="*50)
        return True
        
    except Exception as e:
        print("\n" + "="*50)
        print(f"❌ DB 연결 테스트 실패!")
        print(f"오류: {e}")
        print("="*50)
        print("\n확인사항:")
        print("1. .env 파일의 DB 정보가 정확한지 확인")
        print("2. VPN 연결이 필요한지 확인")
        print("3. DB 서버가 실행 중인지 확인")
        print("4. 방화벽/IP 허용 설정 확인")
        return False

if __name__ == "__main__":
    # 직접 실행시 테스트 수행
    test_connection()
# config/database.py
"""데이터베이스 연결 설정 및 테스트"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
import pandas as pd
import pymysql

# SSH 터널 지원 (선택사항)
try:
    from sshtunnel import SSHTunnelForwarder
    SSH_TUNNEL_AVAILABLE = True
except ImportError:
    SSH_TUNNEL_AVAILABLE = False
    SSHTunnelForwarder = None

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

# SSH 터널 전역 변수 (프로세스 종료 시 정리)
_ssh_tunnel = None

def _setup_ssh_tunnel():
    """SSH 터널 설정 (필요한 경우)"""
    global _ssh_tunnel
    
    # SSH 터널 정보 확인
    ssh_host = os.getenv('SSH_HOST')
    ssh_port = int(os.getenv('SSH_PORT', 22))
    ssh_user = os.getenv('SSH_USER')
    ssh_password = os.getenv('SSH_PASSWORD')
    
    # SSH 터널이 필요한지 확인
    if not ssh_host or not ssh_user:
        return None  # SSH 터널 미사용
    
    # 원격 DB 정보 확인
    remote_host = os.getenv('DB_REMOTE_HOST')
    remote_port = int(os.getenv('DB_REMOTE_PORT', 3306))
    
    if not remote_host:
        return None  # SSH 터널 미사용
    
    # SSH 터널 라이브러리가 없으면 경고만 출력
    if not SSH_TUNNEL_AVAILABLE:
        print("⚠️  SSH 터널 라이브러리가 설치되지 않았습니다.")
        print("   PuTTY 등으로 수동으로 SSH 터널을 설정하거나, 다음 명령으로 설치하세요:")
        print("   pip install sshtunnel")
        return None
    
    # 이미 터널이 열려있으면 재사용
    if _ssh_tunnel and _ssh_tunnel.is_alive:
        return _ssh_tunnel
    
    try:
        # SSH 터널 생성
        print(f"[SSH] SSH 터널 생성 중... ({ssh_user}@{ssh_host}:{ssh_port})")
        _ssh_tunnel = SSHTunnelForwarder(
            (ssh_host, ssh_port),
            ssh_username=ssh_user,
            ssh_password=ssh_password,
            remote_bind_address=(remote_host, remote_port),
            local_bind_address=('127.0.0.1', 0)  # 0은 사용 가능한 포트 자동 할당
        )
        _ssh_tunnel.start()
        print(f"[SSH] SSH 터널 생성 완료! (로컬: {_ssh_tunnel.local_bind_host}:{_ssh_tunnel.local_bind_port})")
        return _ssh_tunnel
    except Exception as e:
        import traceback
        print(f"[ERROR] SSH 터널 생성 실패!")
        print(f"[ERROR] 오류 타입: {type(e).__name__}")
        print(f"[ERROR] 오류 메시지: {str(e)}")
        print("\n[ERROR] 상세 오류 정보:")
        traceback.print_exc()
        print("\n[해결 방법]")
        print("1. SSH 서버 정보 확인 (SSH_HOST, SSH_PORT, SSH_USER, SSH_PASSWORD)")
        print("2. 네트워크 연결 확인 (SSH 서버에 접근 가능한지)")
        print("3. PuTTY 등으로 수동으로 SSH 터널을 설정하거나")
        print("4. SSH 터널 없이 직접 연결을 시도하세요")
        return None

def get_db_connection():
    """데이터베이스 연결 객체 반환"""
    global _ssh_tunnel
    
    # SSH 터널 설정 (필요한 경우)
    tunnel = _setup_ssh_tunnel()
    
    # SSH 터널을 사용하는 경우 로컬 포트 사용
    if tunnel:
        db_host = tunnel.local_bind_host
        db_port = tunnel.local_bind_port
        print(f"📡 SSH 터널을 통해 DB 연결: {db_host}:{db_port}")
    else:
        # 직접 연결
        db_host = os.getenv('DB_HOST')
        db_port = int(os.getenv('DB_PORT', 3306))
    
    # 환경변수에서 DB 정보 읽기
    db_config = {
        'host': db_host,
        'port': db_port,
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
            echo=False,          # SQL 로그 출력 (디버깅시 True)
            connect_args={
                'connect_timeout': 30,  # 연결 타임아웃 30초
                'read_timeout': 30,     # 읽기 타임아웃 30초
                'write_timeout': 30     # 쓰기 타임아웃 30초
            }
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
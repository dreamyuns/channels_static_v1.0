# utils/logger.py
"""로깅 모듈 - 타입별 로그 파일 분리 및 관리"""

import logging
import os
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler
from pathlib import Path

# 로그 디렉토리 설정
# 환경 변수로 로그 디렉토리 경로를 설정할 수 있음 (운영서버 대응)
_log_dir_env = os.environ.get('LOG_DIR')
if _log_dir_env:
    # 환경 변수가 설정된 경우 절대 경로로 사용
    _log_dir = Path(_log_dir_env).resolve()
else:
    # 기본값: 프로젝트 루트의 logs 디렉토리
    _log_dir = Path(__file__).parent.parent.resolve() / "logs"

# 로그 디렉토리 생성 (실패 시 예외 처리)
try:
    _log_dir.mkdir(parents=True, exist_ok=True)
    # 디버깅: 로그 디렉토리 경로 확인 (초기화 시에만 출력)
    if not hasattr(setup_logging, '_path_logged'):
        print(f"[LOG] 로그 디렉토리: {_log_dir.absolute()}")
        setup_logging._path_logged = True
except Exception as e:
    # 로그 디렉토리 생성 실패 시 임시 디렉토리 사용
    import tempfile
    _log_dir = Path(tempfile.gettempdir()) / "app_logs"
    _log_dir.mkdir(parents=True, exist_ok=True)
    print(f"[LOG WARNING] 원래 로그 디렉토리 생성 실패, 임시 디렉토리 사용: {_log_dir.absolute()}")
    print(f"[LOG WARNING] 오류: {e}")

# 로그 포맷
LOG_FORMAT = "[%(asctime)s] [%(levelname)-8s] [%(category)s] %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 로거 딕셔너리
_loggers = {}

# 로그 레벨 매핑
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}


class CategoryFilter(logging.Filter):
    """로그 카테고리 필터"""
    def __init__(self, category):
        super().__init__()
        self.category = category
    
    def filter(self, record):
        record.category = self.category
        return True


def _setup_logger(name: str, filename: str, category: str, level: int = logging.INFO):
    """로거 설정"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 중복 핸들러 방지
    if logger.handlers:
        return logger
    
    # 파일 핸들러 (일별 로테이션)
    log_file = _log_dir / filename
    try:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=30,  # 30일 보관
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.addFilter(CategoryFilter(category))
        
        formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        
        # 디버깅: 로그 파일 경로 확인 (최초 설정 시에만)
        if not hasattr(_setup_logger, '_files_logged'):
            print(f"[LOG] 로그 파일 생성: {log_file.absolute()}")
            _setup_logger._files_logged = True
    except Exception as e:
        # 로그 파일 생성 실패 시 콘솔에 출력
        print(f"[LOG ERROR] 로그 파일 생성 실패: {log_file.absolute()}")
        print(f"[LOG ERROR] 오류: {e}")
        # 콘솔 핸들러 추가 (파일 쓰기 실패 시 대안)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.addFilter(CategoryFilter(category))
        formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger


def _get_logger(log_type: str):
    """로거 가져오기"""
    if log_type not in _loggers:
        if log_type == 'auth':
            _loggers[log_type] = _setup_logger('auth', 'auth.log', 'AUTH')
        elif log_type == 'error':
            _loggers[log_type] = _setup_logger('error', 'error.log', 'ERROR')
        elif log_type == 'access':
            _loggers[log_type] = _setup_logger('access', 'access.log', 'ACCESS')
        elif log_type == 'app':
            _loggers[log_type] = _setup_logger('app', 'app.log', 'APP')
        else:
            _loggers[log_type] = _setup_logger('app', 'app.log', 'APP')
    
    return _loggers[log_type]


def _clean_old_logs(days: int = 30):
    """오래된 로그 파일 삭제"""
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        for log_file in _log_dir.glob("*.log.*"):  # 로테이션된 파일
            try:
                file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                if file_time < cutoff_date:
                    log_file.unlink()
            except Exception:
                pass
    except Exception:
        pass


def log_auth(level: str, message: str, admin_id: str = None, ip: str = None, **kwargs):
    """인증 관련 로그"""
    logger = _get_logger('auth')
    log_level = LOG_LEVELS.get(level.upper(), logging.INFO)
    
    # 추가 정보 포맷팅
    extra_info = []
    if admin_id:
        extra_info.append(f"admin_id={admin_id}")
    if ip:
        extra_info.append(f"IP={ip}")
    for key, value in kwargs.items():
        if key not in ['admin_id', 'ip']:
            extra_info.append(f"{key}={value}")
    
    full_message = message
    if extra_info:
        full_message += f": {', '.join(extra_info)}"
    
    logger.log(log_level, full_message)
    
    # 전체 로그에도 기록
    log_app(level, f"[AUTH] {full_message}")


def log_error(level: str, message: str, exception: Exception = None, traceback_str: str = None, **kwargs):
    """에러 로그"""
    logger = _get_logger('error')
    log_level = LOG_LEVELS.get(level.upper(), logging.ERROR)
    
    full_message = message
    if kwargs:
        extra_info = [f"{key}={value}" for key, value in kwargs.items()]
        full_message += f": {', '.join(extra_info)}"
    
    if exception:
        full_message += f" | Exception: {type(exception).__name__}: {str(exception)}"
    
    logger.log(log_level, full_message)
    
    if traceback_str:
        logger.log(log_level, f"Traceback: {traceback_str}")
    
    # 전체 로그에도 기록
    log_app(level, f"[ERROR] {full_message}")


def log_access(level: str, message: str, admin_id: str = None, action: str = None, **kwargs):
    """접근/활동 로그"""
    logger = _get_logger('access')
    log_level = LOG_LEVELS.get(level.upper(), logging.INFO)
    
    # 추가 정보 포맷팅
    extra_info = []
    if admin_id:
        extra_info.append(f"admin_id={admin_id}")
    if action:
        extra_info.append(f"action={action}")
    for key, value in kwargs.items():
        if key not in ['admin_id', 'action']:
            extra_info.append(f"{key}={value}")
    
    full_message = message
    if extra_info:
        full_message += f": {', '.join(extra_info)}"
    
    logger.log(log_level, full_message)
    
    # 전체 로그에도 기록
    log_app(level, f"[ACCESS] {full_message}")


def log_app(level: str, message: str, **kwargs):
    """전체 로그"""
    logger = _get_logger('app')
    log_level = LOG_LEVELS.get(level.upper(), logging.INFO)
    
    full_message = message
    if kwargs:
        extra_info = [f"{key}={value}" for key, value in kwargs.items()]
        full_message += f": {', '.join(extra_info)}"
    
    logger.log(log_level, full_message)


def setup_logging():
    """로깅 초기화"""
    # 오래된 로그 정리
    _clean_old_logs(days=30)
    
    # 기본 로거 설정
    try:
        log_app("INFO", f"로깅 시스템 초기화 완료 (로그 디렉토리: {_log_dir.absolute()})")
    except Exception as e:
        # 로그 기록 실패 시 콘솔에 출력
        print(f"[LOG ERROR] 로깅 초기화 중 오류 발생: {e}")
        print(f"[LOG] 로그 디렉토리: {_log_dir.absolute()}")


if __name__ == "__main__":
    # 테스트
    setup_logging()
    log_auth("INFO", "로그인 시도", admin_id="test_user", ip="192.168.1.100")
    log_auth("INFO", "로그인 성공", admin_id="test_user")
    log_error("ERROR", "데이터베이스 연결 실패", exception=Exception("Connection timeout"))
    log_access("INFO", "데이터 조회", admin_id="test_user", action="fetch_data", 기간="2025-01-01~2025-01-07")
    print("✅ 로깅 테스트 완료")


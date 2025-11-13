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
    # systemd 실행 시 __file__ 경로가 잘못될 수 있으므로, 현재 작업 디렉토리도 확인
    try:
        # 방법 1: __file__ 기준 (일반적인 경우)
        _log_dir = Path(__file__).parent.parent.resolve() / "logs"
        # 경로가 존재하지 않거나 이상한 경로인 경우 확인
        if not _log_dir.exists() and str(_log_dir).startswith('/root'):
            # /root 경로는 잘못된 경로일 가능성이 높음
            raise ValueError("Invalid path detected")
    except (ValueError, AttributeError):
        # 방법 2: 현재 작업 디렉토리 기준 (systemd 실행 시)
        cwd = Path.cwd()
        _log_dir = cwd / "logs"
        # 여전히 이상한 경로인 경우
        if str(_log_dir).startswith('/root'):
            # 방법 3: 환경 변수 WORKING_DIRECTORY 확인
            working_dir = os.environ.get('WORKING_DIRECTORY')
            if working_dir:
                _log_dir = Path(working_dir) / "logs"
            else:
                # 최후의 수단: /tmp 사용
                _log_dir = Path("/tmp") / "app_logs"

# 앱 이름 (setup_logging 호출 시 설정됨)
_app_name = None

# 로그 디렉토리 생성 (실패 시 예외 처리)
try:
    _log_dir.mkdir(parents=True, exist_ok=True)
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
    
    # 로그 파일명 처리 (앱 이름이 이미 포함된 경우 그대로 사용)
    log_filename = filename
    
    # 파일 핸들러 (일별 로테이션)
    log_file = _log_dir / log_filename
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
    """로거 가져오기 (통합 로그)"""
    # 앱 이름을 포함한 고유 키 생성 (앱별로 로거 분리)
    logger_key = f"{log_type}_{_app_name}" if _app_name else log_type
    
    if logger_key not in _loggers:
        # 통합 로그: 모든 로그를 기록 (channels.log, hotel.log)
        if _app_name:
            log_filename = f"{_app_name}.log"
            logger_name = f"{_app_name}_unified"
        else:
            log_filename = "app.log"
            logger_name = "app_unified"
        
        _loggers[logger_key] = _setup_logger(logger_name, log_filename, 'APP')
    
    return _loggers[logger_key]


def _get_error_logger():
    """에러 로거 가져오기 (에러 로그만)"""
    logger_key = f"error_{_app_name}" if _app_name else "error"
    
    if logger_key not in _loggers:
        # 에러 로그: ERROR 레벨만 기록 (channels_error.log, hotel_error.log)
        if _app_name:
            log_filename = f"{_app_name}_error.log"
            logger_name = f"{_app_name}_error"
        else:
            log_filename = "error.log"
            logger_name = "error"
        
        _loggers[logger_key] = _setup_logger(logger_name, log_filename, 'ERROR', level=logging.ERROR)
    
    return _loggers[logger_key]


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
    logger = _get_logger('unified')
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
    
    # 통합 로그에 기록
    logger.log(log_level, f"[AUTH] {full_message}")
    
    # ERROR 레벨인 경우 에러 로그에도 기록
    if log_level >= logging.ERROR:
        error_logger = _get_error_logger()
        error_logger.log(log_level, f"[AUTH] {full_message}")


def log_error(level: str, message: str, exception: Exception = None, traceback_str: str = None, **kwargs):
    """에러 로그"""
    logger = _get_logger('unified')
    log_level = LOG_LEVELS.get(level.upper(), logging.ERROR)
    
    full_message = message
    if kwargs:
        extra_info = [f"{key}={value}" for key, value in kwargs.items()]
        full_message += f": {', '.join(extra_info)}"
    
    # 실패 사유: 사용자 친화적 메시지 + 기술적 상세 정보
    if exception:
        # Exception 타입에서 간단한 사용자 친화적 메시지 추출
        exception_type = type(exception).__name__
        exception_msg = str(exception)
        
        # 간단한 매핑 (주요 Exception 타입)
        user_friendly_msgs = {
            'ConnectionError': '데이터베이스 연결 실패',
            'TimeoutError': '요청 시간 초과',
            'MemoryError': '메모리 부족',
            'ValueError': '잘못된 값',
            'KeyError': '필수 데이터 누락',
            'FileNotFoundError': '파일을 찾을 수 없음',
            'PermissionError': '권한 없음',
        }
        
        user_msg = user_friendly_msgs.get(exception_type, f'{exception_type} 오류')
        full_message += f", 사유={user_msg} | Exception: {exception_type}: {exception_msg}"
    else:
        full_message += f", 사유={message}"
    
    # 통합 로그에 기록
    logger.log(log_level, f"[ERROR] {full_message}")
    
    # 에러 로그에도 기록
    error_logger = _get_error_logger()
    error_logger.log(log_level, f"[ERROR] {full_message}")
    
    if traceback_str:
        logger.log(log_level, f"Traceback: {traceback_str}")
        error_logger.log(log_level, f"Traceback: {traceback_str}")


def log_access(level: str, message: str, admin_id: str = None, action: str = None, **kwargs):
    """접근/활동 로그"""
    logger = _get_logger('unified')
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
    
    # 통합 로그에 기록
    logger.log(log_level, f"[ACCESS] {full_message}")
    
    # ERROR 레벨인 경우 에러 로그에도 기록
    if log_level >= logging.ERROR:
        error_logger = _get_error_logger()
        error_logger.log(log_level, f"[ACCESS] {full_message}")


def log_app(level: str, message: str, **kwargs):
    """전체 로그 (통합 로그)"""
    logger = _get_logger('unified')
    log_level = LOG_LEVELS.get(level.upper(), logging.INFO)
    
    full_message = message
    if kwargs:
        extra_info = [f"{key}={value}" for key, value in kwargs.items()]
        full_message += f": {', '.join(extra_info)}"
    
    # 통합 로그에 기록
    logger.log(log_level, full_message)
    
    # ERROR 레벨인 경우 에러 로그에도 기록
    if log_level >= logging.ERROR:
        error_logger = _get_error_logger()
        error_logger.log(log_level, full_message)


def setup_logging(app_name: str = None):
    """로깅 초기화
    
    Args:
        app_name: 앱 이름 (예: "channels", "hotel"). 로그 파일명에 포함됨.
                 None인 경우 기본 파일명 사용 (기존 방식과 호환)
    """
    global _app_name
    
    # 앱 이름 설정
    _app_name = app_name
    
    # 로그 디렉토리 경로 출력 (초기화 시에만)
    if not hasattr(setup_logging, '_path_logged'):
        print(f"[LOG] 로그 디렉토리: {_log_dir.absolute()}")
        if _app_name:
            print(f"[LOG] 앱 이름: {_app_name}")
        setup_logging._path_logged = True
    
    # 오래된 로그 정리
    _clean_old_logs(days=30)
    
    # 기본 로거 설정
    try:
        app_info = f" (앱: {_app_name})" if _app_name else ""
        log_app("INFO", f"로깅 시스템 초기화 완료{app_info} (로그 디렉토리: {_log_dir.absolute()})")
    except Exception as e:
        # 로그 기록 실패 시 콘솔에 출력
        print(f"[LOG ERROR] 로깅 초기화 중 오류 발생: {e}")
        print(f"[LOG] 로그 디렉토리: {_log_dir.absolute()}")
        if _app_name:
            print(f"[LOG] 앱 이름: {_app_name}")


if __name__ == "__main__":
    # 테스트
    setup_logging()
    log_auth("INFO", "로그인 시도", admin_id="test_user", ip="192.168.1.100")
    log_auth("INFO", "로그인 성공", admin_id="test_user")
    log_error("ERROR", "데이터베이스 연결 실패", exception=Exception("Connection timeout"))
    log_access("INFO", "데이터 조회", admin_id="test_user", action="fetch_data", 기간="2025-01-01~2025-01-07")
    print("✅ 로깅 테스트 완료")


#!/bin/bash
# 서버 상태 확인 스크립트

echo "=========================================="
echo "서버 상태 확인"
echo "=========================================="

# 1. 현재 디렉토리 확인
echo ""
echo "[1] 현재 위치:"
pwd

# 2. .env 파일 확인 (비밀번호는 마스킹)
echo ""
echo "[2] .env 파일 설정 확인:"
if [ -f .env ]; then
    cat .env | sed 's/DB_PASSWORD=.*/DB_PASSWORD=***HIDDEN***/'
else
    echo "❌ .env 파일이 없습니다!"
fi

# 3. 가상환경 확인
echo ""
echo "[3] 가상환경 확인:"
if [ -d "venv" ]; then
    echo "✅ venv 폴더 존재"
    source venv/bin/activate
    which python
    python --version
else
    echo "❌ venv 폴더가 없습니다!"
fi

# 4. 필수 파일 확인
echo ""
echo "[4] 필수 파일 확인:"
files=("app.py" "config/configdb.py" "utils/data_fetcher.py" "master_data.xlsx")
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file (없음)"
    fi
done

# 5. DB 연결 테스트
echo ""
echo "[5] 데이터베이스 연결 테스트:"
if [ -f .env ]; then
    source venv/bin/activate 2>/dev/null
    python3 << EOF
import sys
import os
sys.path.insert(0, os.getcwd())
try:
    from config.configdb import get_db_connection
    engine = get_db_connection()
    print("✅ DB 연결 성공!")
    engine.dispose()
except Exception as e:
    print(f"❌ DB 연결 실패: {e}")
EOF
else
    echo "⚠️  .env 파일이 없어 DB 연결 테스트를 건너뜁니다."
fi

# 6. 네트워크 연결 확인
echo ""
echo "[6] 네트워크 연결 확인:"
if [ -f .env ]; then
    DB_HOST=$(grep DB_HOST .env | cut -d '=' -f2)
    echo "DB 서버: $DB_HOST"
    if ping -c 2 -W 2 $DB_HOST > /dev/null 2>&1; then
        echo "✅ ping 성공"
    else
        echo "❌ ping 실패"
    fi
    
    # 포트 연결 테스트
    if timeout 3 bash -c "cat < /dev/null > /dev/tcp/$DB_HOST/3306" 2>/dev/null; then
        echo "✅ 포트 3306 연결 가능"
    else
        echo "❌ 포트 3306 연결 불가 (타임아웃 또는 방화벽 차단)"
    fi
fi

# 7. Streamlit 프로세스 확인
echo ""
echo "[7] Streamlit 프로세스 확인:"
if pgrep -f "streamlit.*app.py" > /dev/null; then
    echo "✅ Streamlit 실행 중"
    ps aux | grep "streamlit.*app.py" | grep -v grep
else
    echo "❌ Streamlit 실행 중이 아님"
fi

# 8. 포트 사용 확인
echo ""
echo "[8] 포트 8007 사용 확인:"
if netstat -tuln 2>/dev/null | grep :8007 > /dev/null || ss -tuln 2>/dev/null | grep :8007 > /dev/null; then
    echo "✅ 포트 8007 사용 중"
    netstat -tuln 2>/dev/null | grep :8007 || ss -tuln 2>/dev/null | grep :8007
else
    echo "❌ 포트 8007 사용 중이 아님"
fi

# 9. 방화벽 확인
echo ""
echo "[9] 방화벽 상태 확인:"
if command -v ufw > /dev/null; then
    echo "UFW 상태:"
    sudo ufw status | grep 8007 || echo "포트 8007 규칙 없음"
elif command -v firewall-cmd > /dev/null; then
    echo "Firewalld 상태:"
    sudo firewall-cmd --list-ports 2>/dev/null | grep 8007 || echo "포트 8007 규칙 없음"
else
    echo "⚠️  방화벽 도구를 찾을 수 없습니다."
fi

echo ""
echo "=========================================="
echo "확인 완료"
echo "=========================================="


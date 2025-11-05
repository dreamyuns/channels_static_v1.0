#!/bin/bash
# Systemd 서비스 설정 자동화 스크립트
# 사용법: ./setup_systemd_service.sh

set -e  # 에러 발생 시 스크립트 중단

echo "=========================================="
echo "Systemd 서비스 설정 시작"
echo "=========================================="
echo ""

# 1. 현재 상태 확인
echo "[1] 현재 상태 확인 중..."
echo ""

# 프로젝트 경로 확인
PROJECT_DIR=$(pwd)
echo "프로젝트 경로: $PROJECT_DIR"

# 사용자 확인
CURRENT_USER=$(whoami)
echo "현재 사용자: $CURRENT_USER"

# 포트 8007 사용 확인
echo ""
echo "포트 8007 사용 확인 중..."
if sudo lsof -i :8007 > /dev/null 2>&1; then
    echo "⚠️  포트 8007이 이미 사용 중입니다!"
    echo "사용 중인 프로세스:"
    sudo lsof -i :8007
    echo ""
    read -p "프로세스를 종료하시겠습니까? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo lsof -ti :8007 | xargs sudo kill -9
        echo "✅ 포트 8007 프로세스 종료 완료"
        sleep 2
    else
        echo "⚠️  포트 충돌이 발생할 수 있습니다."
    fi
else
    echo "✅ 포트 8007이 비어있습니다"
fi

# 가상환경 확인
echo ""
echo "[2] 가상환경 확인 중..."
if [ ! -d "venv" ]; then
    echo "❌ venv 폴더가 없습니다!"
    exit 1
fi

STREAMLIT_PATH="$PROJECT_DIR/venv/bin/streamlit"
if [ ! -f "$STREAMLIT_PATH" ]; then
    echo "❌ Streamlit이 설치되어 있지 않습니다!"
    exit 1
fi
echo "✅ 가상환경 확인 완료: $STREAMLIT_PATH"

# app.py 확인
if [ ! -f "$PROJECT_DIR/app.py" ]; then
    echo "❌ app.py 파일이 없습니다!"
    exit 1
fi
echo "✅ app.py 확인 완료"

# .env 파일 확인
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "⚠️  .env 파일이 없습니다!"
    echo "DB 연결 정보가 필요합니다."
fi

# 3. 서비스 파일 생성
echo ""
echo "[3] 서비스 파일 생성 중..."
SERVICE_FILE="/etc/systemd/system/channels-statistics.service"

sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=Channels Statistics Streamlit App
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
Group=$CURRENT_USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$STREAMLIT_PATH run $PROJECT_DIR/app.py --server.port 8007 --server.address 0.0.0.0
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo "✅ 서비스 파일 생성 완료: $SERVICE_FILE"

# 4. 서비스 파일 권한 설정
echo ""
echo "[4] 서비스 파일 권한 설정 중..."
sudo chmod 644 $SERVICE_FILE
echo "✅ 권한 설정 완료"

# 5. systemd에 서비스 파일 로드
echo ""
echo "[5] systemd에 서비스 파일 로드 중..."
sudo systemctl daemon-reload
echo "✅ 서비스 파일 로드 완료"

# 6. 서비스 시작
echo ""
echo "[6] 서비스 시작 중..."
sudo systemctl start channels-statistics
sleep 2

# 7. 서비스 상태 확인
echo ""
echo "[7] 서비스 상태 확인 중..."
sudo systemctl status channels-statistics --no-pager -l

# 8. 부팅 시 자동 시작 설정
echo ""
read -p "부팅 시 자동 시작을 활성화하시겠습니까? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo systemctl enable channels-statistics
    echo "✅ 부팅 시 자동 시작 활성화 완료"
else
    echo "⚠️  부팅 시 자동 시작이 비활성화되어 있습니다."
fi

# 9. 최종 확인
echo ""
echo "=========================================="
echo "설정 완료!"
echo "=========================================="
echo ""
echo "서비스 관리 명령어:"
echo "  시작:   sudo systemctl start channels-statistics"
echo "  중지:   sudo systemctl stop channels-statistics"
echo "  재시작: sudo systemctl restart channels-statistics"
echo "  상태:   sudo systemctl status channels-statistics"
echo "  로그:   sudo journalctl -u channels-statistics -f"
echo ""
echo "웹 서비스 접속:"
echo "  http://211.188.59.125:8007/"
echo ""
echo "=========================================="


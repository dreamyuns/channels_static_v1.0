#!/bin/bash
# Systemd 서비스 상태 확인 스크립트

echo "=========================================="
echo "Systemd 서비스 상태 확인"
echo "=========================================="
echo ""

# 1. 서비스 상태 확인
echo "[1] 서비스 상태 확인"
echo "----------------------------------------"
sudo systemctl status channels-statistics --no-pager -l | head -20
echo ""

# 2. 서비스 활성화 상태 확인
echo "[2] 부팅 시 자동 시작 설정 확인"
echo "----------------------------------------"
if sudo systemctl is-enabled channels-statistics > /dev/null 2>&1; then
    echo "✅ 부팅 시 자동 시작 활성화됨"
else
    echo "❌ 부팅 시 자동 시작 비활성화됨"
fi
echo ""

# 3. 포트 8007 사용 확인
echo "[3] 포트 8007 사용 확인"
echo "----------------------------------------"
if sudo ss -tulpn | grep :8007 > /dev/null 2>&1; then
    echo "✅ 포트 8007이 리스닝 중입니다"
    sudo ss -tulpn | grep :8007
else
    echo "❌ 포트 8007이 리스닝 중이 아닙니다"
fi
echo ""

# 4. Streamlit 프로세스 확인
echo "[4] Streamlit 프로세스 확인"
echo "----------------------------------------"
if pgrep -f "streamlit.*app.py" > /dev/null; then
    echo "✅ Streamlit 프로세스 실행 중"
    ps aux | grep "streamlit.*app.py" | grep -v grep
else
    echo "❌ Streamlit 프로세스가 실행 중이 아닙니다"
fi
echo ""

# 5. 로컬 웹 서비스 응답 확인
echo "[5] 로컬 웹 서비스 응답 확인"
echo "----------------------------------------"
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8007/ | grep -q "200\|301\|302"; then
    echo "✅ 웹 서비스가 정상 응답합니다"
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8007/)
    echo "   HTTP 상태 코드: $HTTP_CODE"
else
    echo "❌ 웹 서비스가 응답하지 않습니다"
fi
echo ""

# 6. 최근 로그 확인
echo "[6] 최근 서비스 로그 (마지막 10줄)"
echo "----------------------------------------"
sudo journalctl -u channels-statistics -n 10 --no-pager
echo ""

# 7. 에러 로그 확인
echo "[7] 에러 로그 확인"
echo "----------------------------------------"
ERROR_COUNT=$(sudo journalctl -u channels-statistics --since "5 minutes ago" --no-pager | grep -i "error\|failed\|exception" | wc -l)
if [ "$ERROR_COUNT" -gt 0 ]; then
    echo "⚠️  최근 5분 동안 $ERROR_COUNT 개의 에러가 발견되었습니다"
    sudo journalctl -u channels-statistics --since "5 minutes ago" --no-pager | grep -i "error\|failed\|exception" | tail -5
else
    echo "✅ 최근 에러가 없습니다"
fi
echo ""

echo "=========================================="
echo "확인 완료"
echo "=========================================="
echo ""
echo "외부 접속 테스트:"
echo "  http://211.188.59.125:8007/"
echo ""
echo "서비스 관리 명령어:"
echo "  상태:   sudo systemctl status channels-statistics"
echo "  로그:   sudo journalctl -u channels-statistics -f"
echo "  재시작: sudo systemctl restart channels-statistics"
echo ""


# 서버 환경 확인 스크립트 (Windows PowerShell)
# 사용법: PowerShell에서 실행
# .\check_server.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "서버 환경 확인 (211.188.59.125)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 서버 응답 확인
Write-Host "[1] 서버 응답 확인 (Ping 테스트)..." -ForegroundColor Yellow
try {
    $pingResult = Test-Connection -ComputerName 211.188.59.125 -Count 2 -Quiet
    if ($pingResult) {
        Write-Host "✅ 서버가 응답합니다 (서버는 켜져있음)" -ForegroundColor Green
    } else {
        Write-Host "❌ 서버가 응답하지 않습니다 (서버가 꺼져있거나 네트워크 문제)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Ping 테스트 실패: $_" -ForegroundColor Red
}

Write-Host ""

# 2. 포트 8007 연결 확인
Write-Host "[2] 포트 8007 연결 확인..." -ForegroundColor Yellow
try {
    $portTest = Test-NetConnection -ComputerName 211.188.59.125 -Port 8007 -WarningAction SilentlyContinue
    if ($portTest.TcpTestSucceeded) {
        Write-Host "✅ 포트 8007이 열려있습니다 (서비스 실행 중)" -ForegroundColor Green
        Write-Host "   → http://211.188.59.125:8007/ 접속 가능" -ForegroundColor Gray
    } else {
        Write-Host "❌ 포트 8007이 닫혀있습니다 (서비스 중단 또는 방화벽 차단)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ 포트 테스트 실패: $_" -ForegroundColor Red
}

Write-Host ""

# 3. 웹 서비스 응답 확인
Write-Host "[3] 웹 서비스 응답 확인..." -ForegroundColor Yellow
try {
    $webResponse = Invoke-WebRequest -Uri "http://211.188.59.125:8007/" -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
    Write-Host "✅ 웹 서비스가 정상 작동 중입니다" -ForegroundColor Green
    Write-Host "   → HTTP 상태 코드: $($webResponse.StatusCode)" -ForegroundColor Gray
} catch {
    Write-Host "❌ 웹 서비스가 응답하지 않습니다: $_" -ForegroundColor Red
}

Write-Host ""

# 4. SSH 접속 가능 여부 확인 (포트 22)
Write-Host "[4] SSH 접속 가능 여부 확인 (포트 22)..." -ForegroundColor Yellow
try {
    $sshTest = Test-NetConnection -ComputerName 211.188.59.125 -Port 22 -WarningAction SilentlyContinue
    if ($sshTest.TcpTestSucceeded) {
        Write-Host "✅ SSH 포트가 열려있습니다 (서버 접속 가능)" -ForegroundColor Green
        Write-Host "   → 명령어: ssh 사용자명@211.188.59.125" -ForegroundColor Gray
    } else {
        Write-Host "⚠️  SSH 포트가 닫혀있습니다 (서버 직접 접속 불가)" -ForegroundColor Yellow
        Write-Host "   → 서버 관리자에게 문의하거나 다른 방법 사용 필요" -ForegroundColor Gray
    }
} catch {
    Write-Host "⚠️  SSH 포트 테스트 실패: $_" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "추가 확인 사항" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "다음 단계:" -ForegroundColor Yellow
Write-Host "1. 서버에 SSH 접속 시도:" -ForegroundColor White
Write-Host "   ssh 사용자명@211.188.59.125" -ForegroundColor Gray
Write-Host ""
Write-Host "2. 서버 접속 후 OS 확인:" -ForegroundColor White
Write-Host "   Linux: cat /etc/os-release" -ForegroundColor Gray
Write-Host "   Windows: systeminfo | findstr /B /C:'OS Name'" -ForegroundColor Gray
Write-Host ""
Write-Host "3. 서버 업타임 확인:" -ForegroundColor White
Write-Host "   Linux: uptime" -ForegroundColor Gray
Write-Host "   Windows: systeminfo | findstr /C:'System Boot Time'" -ForegroundColor Gray
Write-Host ""
Write-Host "4. 현재 Streamlit 실행 상태 확인:" -ForegroundColor White
Write-Host "   Linux: ps aux | grep streamlit" -ForegroundColor Gray
Write-Host "   Windows: Get-Process | Where-Object {`$_.ProcessName -like '*streamlit*'}" -ForegroundColor Gray
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "확인 완료" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan


# 서버 운영 가이드 (비개발자용)

이 문서는 채널별 예약 통계 시스템 서버를 운영하기 위한 필수 가이드입니다.

---

## 📋 목차

1. [서비스 관리 명령어](#서비스-관리-명령어)
2. [로그 확인 방법](#로그-확인-방법)
3. [자동 시작 관리](#자동-시작-관리)
4. [서비스 상태 확인](#서비스-상태-확인)
5. [문제 해결](#문제-해결)
6. [업데이트 및 재배포](#업데이트-및-재배포)
7. [모니터링](#모니터링)
8. [주요 주의사항](#주요-주의사항)

---

## 🚀 서비스 관리 명령어

### 서비스 시작
```bash
sudo systemctl start channels-statistics
```
**언제 사용:**
- 서비스가 중지된 상태에서 다시 시작할 때
- 서버 재부팅 후 수동으로 시작할 때 (자동 시작이 비활성화된 경우)

---

### 서비스 중지
```bash
sudo systemctl stop channels-statistics
```
**언제 사용:**
- 서비스를 일시적으로 중지할 때
- 업데이트나 유지보수 전에 중지할 때

**주의:** 중지하면 웹 서비스(`http://211.188.59.125:8007/`)에 접속할 수 없습니다!

---

### 서비스 재시작
```bash
sudo systemctl restart channels-statistics
```
**언제 사용:**
- 코드나 설정을 변경한 후 적용할 때
- 서비스가 이상하게 동작할 때
- 문제 해결을 시도할 때

**재시작 시간:** 약 5-10초 소요

---

### 서비스 상태 확인
```bash
sudo systemctl status channels-statistics
```
**확인 사항:**
- `Active: active (running)` → 정상 실행 중 ✅
- `Active: inactive (dead)` → 실행 중이 아님 ❌
- `Active: failed` → 실행 실패 ❌

**상태 확인 빈도:** 일주일에 한 번 정도 확인 권장

---

## 📝 로그 확인 방법

### 실시간 로그 확인 (추천)
```bash
sudo journalctl -u channels-statistics -f
```
**의미:**
- 실시간으로 로그를 확인할 수 있습니다
- `Ctrl + C`로 종료

**언제 사용:**
- 서비스에 문제가 발생했을 때
- 어떤 작업이 실행되는지 확인할 때
- 디버깅할 때

---

### 최근 로그 확인
```bash
# 최근 50줄 로그 확인
sudo journalctl -u channels-statistics -n 50

# 최근 100줄 로그 확인
sudo journalctl -u channels-statistics -n 100
```

---

### 특정 시간대 로그 확인
```bash
# 오늘 로그 확인
sudo journalctl -u channels-statistics --since today

# 최근 1시간 로그 확인
sudo journalctl -u channels-statistics --since "1 hour ago"

# 특정 날짜 로그 확인
sudo journalctl -u channels-statistics --since "2025-11-05 00:00:00"
```

---

### 에러 로그만 확인
```bash
# 에러 메시지만 필터링
sudo journalctl -u channels-statistics -p err

# 또는 grep 사용
sudo journalctl -u channels-statistics | grep -i error
```

---

## 🔄 자동 시작 관리

### 현재 자동 시작 상태 확인
```bash
sudo systemctl is-enabled channels-statistics
```
**결과:**
- `enabled` → 재부팅 시 자동 시작 ✅
- `disabled` → 재부팅 시 자동 시작 안 됨 ❌

---

### 자동 시작 활성화
```bash
sudo systemctl enable channels-statistics
```
**의미:**
- 서버가 재부팅되면 자동으로 서비스가 시작됩니다
- **권장:** 항상 활성화 상태로 유지하세요

---

### 자동 시작 비활성화
```bash
sudo systemctl disable channels-statistics
```
**주의:** 비활성화하면 재부팅 후 수동으로 시작해야 합니다!

---

## ✅ 서비스 상태 확인

### 기본 상태 확인
```bash
sudo systemctl status channels-statistics
```

### 간단한 상태 확인
```bash
# 서비스가 실행 중인지만 확인
systemctl is-active channels-statistics
```
**결과:**
- `active` → 실행 중 ✅
- `inactive` → 실행 중이 아님 ❌

---

### 포트 확인
```bash
# 포트 8007이 사용 중인지 확인
sudo ss -tulpn | grep 8007
```
**정상 결과:**
```
tcp   LISTEN  0  4096  0.0.0.0:8007  0.0.0.0:*  users:(("python3",pid=286122,fd=3))
```

---

### 웹 서비스 응답 확인
```bash
# 로컬에서 테스트
curl -I http://localhost:8007/

# 또는
curl http://localhost:8007/
```

---

## 🔧 문제 해결

### 문제 1: 서비스가 시작되지 않음

**1단계: 상태 확인**
```bash
sudo systemctl status channels-statistics
```

**2단계: 로그 확인**
```bash
sudo journalctl -u channels-statistics -n 50
```

**3단계: 일반적인 원인 확인**
```bash
# 프로젝트 경로 확인
ls -la /home/allmytour/projects/channels_statistics

# 가상환경 확인
ls -la /home/allmytour/projects/channels_statistics/venv/bin/streamlit

# .env 파일 확인
ls -la /home/allmytour/projects/channels_statistics/.env
```

**4단계: 재시작 시도**
```bash
sudo systemctl restart channels-statistics
```

---

### 문제 2: 웹 서비스에 접속이 안 됨

**1단계: 서비스 상태 확인**
```bash
sudo systemctl status channels-statistics
```

**2단계: 포트 확인**
```bash
sudo ss -tulpn | grep 8007
```

**3단계: 방화벽 확인 (필요시)**
```bash
sudo ufw status
```

**4단계: 서비스 재시작**
```bash
sudo systemctl restart channels-statistics
```

---

### 문제 3: 서비스가 자주 종료됨

**1단계: 로그 확인**
```bash
sudo journalctl -u channels-statistics --since "1 hour ago" | grep -i error
```

**2단계: 메모리 확인**
```bash
free -h
```

**3단계: 자동 재시작 확인**
```bash
# 서비스 파일에서 Restart=always 확인
sudo cat /etc/systemd/system/channels-statistics.service | grep Restart
```

**해결:**
- 서비스는 자동으로 재시작되도록 설정되어 있습니다
- 문제가 지속되면 로그를 확인하여 원인 파악

---

### 문제 4: 서비스가 느리게 동작함

**1단계: 리소스 사용량 확인**
```bash
sudo systemctl status channels-statistics
# Memory와 CPU 사용량 확인
```

**2단계: 서버 전체 리소스 확인**
```bash
# CPU 사용률
top

# 메모리 사용률
free -h

# 디스크 사용률
df -h
```

---

## 🔄 업데이트 및 재배포

### 코드 업데이트 후 재배포

**1단계: 서비스 중지 (선택사항)**
```bash
sudo systemctl stop channels-statistics
```

**2단계: 코드 업데이트**
```bash
cd ~/projects/channels_statistics

# Git을 사용하는 경우
git pull origin main

# 또는 파일을 직접 업로드하는 경우
# (새 파일들을 서버에 업로드)
```

**3단계: 패키지 업데이트 (필요시)**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

**4단계: 서비스 재시작**
```bash
sudo systemctl restart channels-statistics
```

**5단계: 상태 확인**
```bash
sudo systemctl status channels-statistics
```

---

### 환경 변수(.env) 변경 후

**1단계: .env 파일 수정**
```bash
nano ~/projects/channels_statistics/.env
```

**2단계: 서비스 재시작**
```bash
sudo systemctl restart channels-statistics
```

---

## 📊 모니터링

### 일일 체크리스트

**매일 확인할 사항:**
```bash
# 1. 서비스 상태 확인
sudo systemctl status channels-statistics | head -5

# 2. 웹 서비스 접속 테스트
curl -I http://localhost:8007/

# 3. 포트 확인
sudo ss -tulpn | grep 8007
```

---

### 주간 체크리스트

**매주 확인할 사항:**
```bash
# 1. 로그 확인 (에러 체크)
sudo journalctl -u channels-statistics --since "7 days ago" | grep -i error

# 2. 리소스 사용량 확인
sudo systemctl status channels-statistics

# 3. 디스크 공간 확인
df -h

# 4. 자동 시작 설정 확인
sudo systemctl is-enabled channels-statistics
```

---

### 알림 설정 (선택사항)

**서비스가 중지되면 알림 받기:**
```bash
# 서비스 상태 모니터링 스크립트 생성
cat > ~/check_service.sh << 'EOF'
#!/bin/bash
if ! systemctl is-active --quiet channels-statistics; then
    echo "⚠️ 서비스가 중지되었습니다!"
    # 여기에 알림 보내는 코드 추가 (이메일, 슬랙 등)
fi
EOF

chmod +x ~/check_service.sh

# crontab에 추가 (매 시간마다 확인)
crontab -e
# 다음 줄 추가:
# 0 * * * * /home/allmytour/check_service.sh
```

---

## ⚠️ 주요 주의사항

### 1. 서비스 파일 수정 주의
- 서비스 파일(`/etc/systemd/system/channels-statistics.service`)을 수정한 후에는 반드시:
```bash
sudo systemctl daemon-reload
sudo systemctl restart channels-statistics
```

---

### 2. .env 파일 보안
- `.env` 파일에는 DB 비밀번호가 포함되어 있습니다
- 절대 다른 사람과 공유하지 마세요
- Git에 커밋하지 마세요

---

### 3. 포트 충돌
- 다른 프로그램이 포트 8007을 사용하면 서비스가 시작되지 않습니다
- 포트 충돌 시:
```bash
# 포트 사용 중인 프로세스 확인
sudo lsof -i :8007

# 프로세스 종료 (필요시)
sudo kill -9 [PID]
```

---

### 4. 로그 파일 관리
- 로그가 너무 많아지면 디스크 공간을 차지할 수 있습니다
- 주기적으로 로그 확인 및 정리:
```bash
# 오래된 로그 확인
sudo journalctl --disk-usage

# 특정 기간 로그만 유지 (선택사항)
sudo journalctl --vacuum-time=30d
```

---

### 5. 서버 재부팅
- 서버를 재부팅하면:
  - 자동 시작이 활성화되어 있으면 서비스가 자동으로 시작됩니다
  - 약 1-2분 후 웹 서비스에 접속 가능합니다

---

### 6. 백업
- 정기적으로 다음 항목을 백업하세요:
  - `.env` 파일 (DB 연결 정보)
  - `master_data.xlsx` 파일
  - 코드 변경 사항

---

## 📞 빠른 참조표

### 자주 사용하는 명령어

| 작업 | 명령어 |
|------|--------|
| 서비스 시작 | `sudo systemctl start channels-statistics` |
| 서비스 중지 | `sudo systemctl stop channels-statistics` |
| 서비스 재시작 | `sudo systemctl restart channels-statistics` |
| 상태 확인 | `sudo systemctl status channels-statistics` |
| 실시간 로그 | `sudo journalctl -u channels-statistics -f` |
| 최근 로그 | `sudo journalctl -u channels-statistics -n 50` |
| 포트 확인 | `sudo ss -tulpn \| grep 8007` |
| 자동 시작 확인 | `sudo systemctl is-enabled channels-statistics` |

---

## 🎯 요약

### 정상 운영 중 확인 사항:
1. ✅ 서비스 상태: `active (running)`
2. ✅ 자동 시작: `enabled`
3. ✅ 포트 8007: 리스닝 중
4. ✅ 웹 접속: `http://211.188.59.125:8007/` 정상 작동

### 문제 발생 시 순서:
1. 상태 확인: `sudo systemctl status channels-statistics`
2. 로그 확인: `sudo journalctl -u channels-statistics -n 50`
3. 재시작 시도: `sudo systemctl restart channels-statistics`
4. 문제 지속 시 로그 내용을 확인하여 원인 파악

---

**서비스가 정상적으로 운영되고 있습니다!** 🎉

추가 질문이나 문제가 발생하면 언제든지 문의하세요.


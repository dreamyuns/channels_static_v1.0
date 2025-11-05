# 서버 환경 확인 가이드

이 문서는 `211.188.59.125` 서버의 환경을 확인하는 방법을 안내합니다.

## 📋 확인할 항목

1. **서버 운영체제 (OS)**: Linux인지 Windows인지
2. **서버 타입**: 전용 서버인지, 일반 PC인지
3. **현재 서비스 상태**: Streamlit이 어떻게 실행 중인지
4. **서버 접속 방법**: SSH 접속 가능 여부

---

## 🔍 방법 1: 서버에 직접 접속해서 확인

### Step 1: 서버 접속

#### Windows PowerShell에서:
```powershell
# SSH로 서버 접속
ssh 사용자명@211.188.59.125
```

**필요한 정보:**
- 서버 사용자명 (예: `root`, `ubuntu`, `admin`, `administrator` 등)
- 서버 접속 비밀번호

**접속이 안 되는 경우:**
- PuTTY 프로그램 사용
- VS Code Remote SSH 확장 사용

### Step 2: 서버 OS 확인

**Linux 서버인 경우:**
```bash
# OS 정보 확인
cat /etc/os-release

# 또는
uname -a

# 예상 결과:
# Ubuntu 20.04 LTS
# 또는
# CentOS Linux release 7.x
```

**Windows 서버인 경우:**
```powershell
# PowerShell에서 실행
systeminfo | findstr /B /C:"OS Name" /C:"OS Version"
```

### Step 3: 서버 타입 확인 (항상 켜져있는지)

**Linux에서:**
```bash
# 서버 업타임 확인 (서버가 얼마나 오래 켜져있었는지)
uptime

# 시스템 부팅 시간 확인
who -b

# 예상 결과:
# 만약 "up 100 days" 같은 긴 시간이면 → 전용 서버 (항상 켜져있음)
# 만약 "up 2 hours" 같은 짧은 시간이면 → 일반 PC (방금 켜진 것)
```

**Windows에서:**
```powershell
# 시스템 업타임 확인
systeminfo | findstr /C:"System Boot Time"

# 또는 PowerShell 명령어
Get-CimInstance Win32_OperatingSystem | Select-Object LastBootUpTime
```

### Step 4: 현재 Streamlit 실행 상태 확인

**Linux에서:**
```bash
# Streamlit 프로세스 확인
ps aux | grep streamlit

# 포트 8007 사용 확인
netstat -tuln | grep 8007
# 또는
ss -tuln | grep 8007

# 예상 결과:
# tcp  0  0  0.0.0.0:8007  LISTEN  → 정상 실행 중
```

**Windows에서:**
```powershell
# Streamlit 프로세스 확인
Get-Process | Where-Object {$_.ProcessName -like "*streamlit*"}

# 포트 8007 사용 확인
netstat -ano | findstr :8007
```

---

## 🔍 방법 2: 로컬에서 간접 확인 (서버 접속이 안 되는 경우)

### 방법 2-1: 웹 브라우저로 확인

현재 서비스가 정상 작동 중인지 확인:
```
http://211.188.59.125:8007/
```

**확인 사항:**
- ✅ 페이지가 열리면 → 서버는 켜져있고 서비스 실행 중
- ❌ 페이지가 안 열리면 → 서버가 꺼져있거나 서비스 중단

### 방법 2-2: ping 테스트

**Windows PowerShell에서:**
```powershell
# 서버 응답 확인
ping 211.188.59.125

# 예상 결과:
# 응답이 오면 → 서버는 켜져있음
# 응답이 없으면 → 서버가 꺼져있거나 네트워크 문제
```

### 방법 2-3: 포트 연결 테스트

**Windows PowerShell에서:**
```powershell
# 포트 8007 연결 테스트
Test-NetConnection -ComputerName 211.188.59.125 -Port 8007

# 예상 결과:
# TcpTestSucceeded : True → 포트가 열려있고 서비스 실행 중
# TcpTestSucceeded : False → 포트가 닫혀있거나 서비스 중단
```

---

## 📊 확인 결과 정리

### 시나리오 A: Linux 서버 + 전용 서버인 경우

**확인 결과:**
- OS: Ubuntu/CentOS 등
- Uptime: 100일 이상 (예시)
- 서비스: systemd 또는 nohup으로 실행 중

**→ 해결 방법:**
- systemd 서비스로 등록 (영구적 실행)
- 재부팅 시 자동 시작 설정

### 시나리오 B: Windows 서버인 경우

**확인 결과:**
- OS: Windows Server 또는 Windows
- 서비스: 작업 스케줄러 또는 수동 실행

**→ 해결 방법:**
- Windows 서비스로 등록
- 또는 작업 스케줄러 설정

### 시나리오 C: 일반 PC인 경우

**확인 결과:**
- OS: Windows/Linux
- Uptime: 짧은 시간 (방금 켜진 것)
- 서비스: 수동 실행

**→ 해결 방법:**
- 클라우드 서버로 이전 고려
- 또는 PC를 항상 켜두고 서비스로 등록

---

## 🚀 다음 단계

서버 환경을 확인한 후, 다음 문서를 참고하세요:

1. **Linux 서버인 경우**: `DEPLOYMENT_GUIDE.md`의 "systemd 서비스로 실행" 섹션
2. **Windows 서버인 경우**: Windows 서비스 등록 가이드 (별도 작성 예정)

---

## ❓ 문제 해결

### 서버에 접속이 안 되는 경우

1. **SSH 서비스가 실행 중인지 확인**
   - 서버 관리자에게 문의
   - 포트 22가 열려있는지 확인

2. **방화벽 문제**
   - 회사 방화벽에서 포트 22가 차단되었을 수 있음
   - VPN 연결이 필요할 수 있음

3. **서버 정보 확인**
   - 서버 관리자에게 접속 정보 요청
   - IP 주소, 사용자명, 비밀번호 확인

---

## 📝 확인 체크리스트

- [ ] 서버에 SSH 접속 성공
- [ ] 서버 OS 확인 (Linux/Windows)
- [ ] 서버 업타임 확인 (전용 서버인지 확인)
- [ ] 현재 Streamlit 실행 방법 확인
- [ ] 포트 8007 사용 여부 확인
- [ ] 서비스가 영구적으로 실행되도록 설정할 방법 결정

---

**확인 완료 후 알려주시면, 해당 환경에 맞는 설정 가이드를 제공하겠습니다!**


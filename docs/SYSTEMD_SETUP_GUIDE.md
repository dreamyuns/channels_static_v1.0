# Systemd 서비스 설정 가이드

Ubuntu 24.04.1 LTS 서버에서 Streamlit을 systemd 서비스로 설정하는 방법입니다.

## 📋 현재 상황 확인

### 1. 포트 8007 사용 여부 확인

서버에서 다음 명령어를 실행하세요:

```bash
# 포트 8007 사용 확인
sudo netstat -tulpn | grep 8007

# 또는 (더 최신 명령어)
sudo ss -tulpn | grep 8007

# 또는 lsof 사용
sudo lsof -i :8007
```

**예상 결과:**
- 결과가 나오면 → 다른 프로세스가 포트를 사용 중
- 결과가 없으면 → 포트가 비어있음

### 2. Streamlit 프로세스 확인

```bash
# Streamlit 프로세스 확인
ps aux | grep streamlit

# Python 프로세스 확인
ps aux | grep python | grep app.py
```

### 3. screen/tmux 세션 확인

```bash
# screen 세션 확인
screen -ls

# tmux 세션 확인
tmux ls
```

---

## 🚀 Systemd 서비스 설정

### Step 1: 서비스 파일 생성

```bash
# 서비스 파일 생성
sudo nano /etc/systemd/system/channels-statistics.service
```

다음 내용을 입력하세요:

```ini
[Unit]
Description=Channels Statistics Streamlit App
After=network.target

[Service]
Type=simple
User=allmytour
Group=allmytour
WorkingDirectory=/home/allmytour/projects/channels_statistics
Environment="PATH=/home/allmytour/projects/channels_statistics/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/allmytour/projects/channels_statistics/venv/bin/streamlit run app.py --server.port 8007 --server.address 0.0.0.0
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**중요 사항:**
- `User=allmytour`: 실제 사용자명으로 변경
- `WorkingDirectory`: 프로젝트 경로 확인 필요
- `--server.port 8007`: 현재 사용 중인 포트
- `Restart=always`: 프로세스가 종료되면 자동 재시작

### Step 2: 프로젝트 경로 확인

```bash
# 현재 프로젝트 경로 확인
pwd

# 전체 경로 확인
realpath ~/projects/channels_statistics
```

### Step 3: 서비스 파일 로드

```bash
# systemd에 새 서비스 파일 알림
sudo systemctl daemon-reload
```

### Step 4: 현재 실행 중인 Streamlit 중지 (필요시)

만약 Streamlit이 다른 방법으로 실행 중이라면:

```bash
# 포트 8007을 사용하는 프로세스 찾기
sudo lsof -i :8007

# 프로세스 ID(PID) 확인 후 종료
sudo kill -9 [PID]
```

또는:

```bash
# Streamlit 프로세스 모두 종료
pkill -f streamlit
```

### Step 5: 서비스 시작

```bash
# 서비스 시작
sudo systemctl start channels-statistics

# 서비스 상태 확인
sudo systemctl status channels-statistics
```

**정상 실행 시 예상 결과:**
```
● channels-statistics.service - Channels Statistics Streamlit App
     Loaded: loaded (/etc/systemd/system/channels-statistics.service; disabled; vendor preset: enabled)
     Active: active (running) since ...
```

### Step 6: 부팅 시 자동 시작 설정

```bash
# 부팅 시 자동 시작 활성화
sudo systemctl enable channels-statistics
```

### Step 7: 서비스 확인

```bash
# 서비스 상태 확인
sudo systemctl status channels-statistics

# 로그 확인
sudo journalctl -u channels-statistics -f

# 최근 100줄 로그 확인
sudo journalctl -u channels-statistics -n 100
```

---

## 🔧 서비스 관리 명령어

### 서비스 시작/중지/재시작

```bash
# 서비스 시작
sudo systemctl start channels-statistics

# 서비스 중지
sudo systemctl stop channels-statistics

# 서비스 재시작
sudo systemctl restart channels-statistics

# 서비스 상태 확인
sudo systemctl status channels-statistics
```

### 서비스 로그 확인

```bash
# 실시간 로그 확인
sudo journalctl -u channels-statistics -f

# 최근 로그 확인
sudo journalctl -u channels-statistics -n 50

# 오늘 로그 확인
sudo journalctl -u channels-statistics --since today

# 특정 시간 이후 로그
sudo journalctl -u channels-statistics --since "2024-01-01 00:00:00"
```

### 자동 시작 설정

```bash
# 부팅 시 자동 시작 활성화
sudo systemctl enable channels-statistics

# 부팅 시 자동 시작 비활성화
sudo systemctl disable channels-statistics

# 자동 시작 상태 확인
sudo systemctl is-enabled channels-statistics
```

---

## 🔍 문제 해결

### 서비스가 시작되지 않는 경우

1. **서비스 파일 문법 확인**
```bash
sudo systemctl daemon-reload
sudo systemctl status channels-statistics
```

2. **로그 확인**
```bash
sudo journalctl -u channels-statistics -n 50
```

3. **경로 확인**
```bash
# 프로젝트 경로 존재 확인
ls -la /home/allmytour/projects/channels_statistics

# 가상환경 확인
ls -la /home/allmytour/projects/channels_statistics/venv/bin/streamlit
```

4. **권한 확인**
```bash
# 서비스 파일 권한
ls -la /etc/systemd/system/channels-statistics.service

# 프로젝트 폴더 권한
ls -la /home/allmytour/projects/channels_statistics
```

### 포트 충돌 문제

```bash
# 포트 8007 사용 중인 프로세스 확인
sudo lsof -i :8007

# 프로세스 종료
sudo kill -9 [PID]
```

### 환경 변수 문제

`.env` 파일이 제대로 로드되는지 확인:

```bash
# 서비스 파일에 환경 변수 추가 (필요시)
sudo nano /etc/systemd/system/channels-statistics.service
```

`[Service]` 섹션에 추가:
```ini
EnvironmentFile=/home/allmytour/projects/channels_statistics/.env
```

---

## ✅ 설정 완료 후 확인

1. **웹 서비스 접속 확인**
   - 브라우저에서 `http://211.188.59.125:8007/` 접속
   - 정상 작동 확인

2. **서비스 상태 확인**
   ```bash
   sudo systemctl status channels-statistics
   ```

3. **재부팅 테스트** (선택사항)
   ```bash
   sudo reboot
   ```
   재부팅 후 서비스가 자동으로 시작되는지 확인

---

## 📝 참고사항

- 서비스는 `allmytour` 사용자 권한으로 실행됩니다
- 로그는 `journalctl`로 확인할 수 있습니다
- 프로세스가 종료되면 자동으로 재시작됩니다
- 서버 재부팅 시 자동으로 서비스가 시작됩니다

---

**문제가 발생하면 로그를 확인하고 위의 문제 해결 섹션을 참고하세요!**


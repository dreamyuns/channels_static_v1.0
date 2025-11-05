# Systemd 서비스 빠른 설정 가이드

## 현재 위치
```bash
/home/allmytour/projects/channels_statistics
```

## 서비스 파일 생성 (올바른 경로)

```bash
# 서비스 파일 생성 (반드시 /etc/systemd/system/ 에 있어야 함)
sudo nano /etc/systemd/system/channels-statistics.service
```

**중요**: `/etc/systemd/system/` 경로를 사용해야 합니다!

## 서비스 파일 내용

다음 내용을 복사해서 붙여넣으세요:

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
ExecStart=/home/allmytour/projects/channels_statistics/venv/bin/streamlit run /home/allmytour/projects/channels_statistics/app.py --server.port 8007 --server.address 0.0.0.0
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

## 저장 및 종료

nano 편집기에서:
- `Ctrl + O` (저장)
- `Enter` (확인)
- `Ctrl + X` (종료)

## 서비스 활성화

```bash
# 1. systemd에 서비스 파일 로드
sudo systemctl daemon-reload

# 2. 서비스 시작
sudo systemctl start channels-statistics

# 3. 상태 확인
sudo systemctl status channels-statistics

# 4. 부팅 시 자동 시작 설정
sudo systemctl enable channels-statistics
```

## 확인

```bash
# 웹 브라우저에서 접속
http://211.188.59.125:8007/
```

## 서비스 관리 명령어

```bash
# 시작
sudo systemctl start channels-statistics

# 중지
sudo systemctl stop channels-statistics

# 재시작
sudo systemctl restart channels-statistics

# 상태 확인
sudo systemctl status channels-statistics

# 로그 확인
sudo journalctl -u channels-statistics -f
```


# 라이브 서버 배포 가이드

이 문서는 채널별 예약 통계 시스템을 라이브 서버에 배포하는 방법을 안내합니다.

## 📋 사전 준비사항

### 1. 서버 접속 정보 확인
- **서버 IP**: [서버 IP 주소]
- **접속 방법**: SSH (Windows에서는 PuTTY, PowerShell SSH, 또는 VS Code Remote SSH 사용)

### 2. 필요한 정보
- 서버 사용자명 (예: `root`, `ubuntu`, `admin` 등)
- 서버 접속 비밀번호 또는 SSH 키
- 서버에 Python 설치 여부 확인 필요

## 🚀 배포 방법

### 방법 1: Git을 통한 배포 (권장)

#### Step 1: 서버에 SSH 접속

```bash
ssh 사용자명@[서버_IP주소]
```

#### Step 2: 프로젝트 디렉토리 생성

```bash
# 홈 디렉토리로 이동
cd ~

# 프로젝트 디렉토리 생성
mkdir -p projects/channels_statistics
cd projects/channels_statistics
```

#### Step 3: Git 저장소 클론

```bash
git clone https://github.com/dreamyuns/channels_static_v1.0.git .
```

#### Step 4: 가상환경 생성 및 패키지 설치

```bash
# Python 가상환경 생성
python3 -m venv venv

# 가상환경 활성화
source venv/bin/activate

# 패키지 설치
pip install --upgrade pip
pip install -r requirements.txt
```

#### Step 5: 환경 변수 설정

```bash
# .env 파일 생성
nano .env
```

다음 내용을 입력하세요 (실제 값으로 변경):
```
DB_HOST=your_database_host
DB_PORT=3306
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_NAME=your_database_name
```

**⚠️ 주의**: 실제 운영 서버의 DB 정보를 사용하세요!

#### Step 6: master_data.xlsx 파일 업로드

`master_data.xlsx` 파일을 서버에 업로드해야 합니다.

**SFTP를 사용한 방법**:
```bash
# 로컬 컴퓨터에서 실행
scp master_data.xlsx 사용자명@[서버_IP주소]:~/projects/channels_statistics/
```

**또는 VS Code Remote SSH 사용**:
- VS Code에서 Remote SSH 확장 설치
- 서버에 연결 후 파일 탐색기에서 드래그 앤 드롭

### 방법 2: 파일 직접 업로드 (Git이 없는 경우)

#### Step 1: 로컬에서 프로젝트 압축

```bash
# Windows PowerShell에서 실행
# .env, venv, __pycache__ 제외하고 압축
Compress-Archive -Path app.py,config,utils,requirements.txt,README.md,env.example -DestinationPath deploy.zip
```

#### Step 2: 서버에 업로드

```bash
# SFTP로 업로드
scp deploy.zip 사용자명@[서버_IP주소]:~/
```

#### Step 3: 서버에서 압축 해제 및 설정

```bash
# 서버에 SSH 접속 후
cd ~
unzip deploy.zip -d projects/channels_statistics
cd projects/channels_statistics

# 가상환경 생성 및 패키지 설치 (위와 동일)
```

## 🔧 서버 설정

### Streamlit 애플리케이션 실행

#### 방법 1: 직접 실행 (테스트용)

```bash
cd ~/projects/channels_statistics
source venv/bin/activate
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

#### 방법 2: 백그라운드 실행

```bash
# nohup을 사용하여 백그라운드 실행
cd ~/projects/channels_statistics
source venv/bin/activate
nohup streamlit run app.py --server.port 8501 --server.address 0.0.0.0 > app.log 2>&1 &
```

#### 방법 3: systemd 서비스로 실행 (영구적)

**서비스 파일 생성**:
```bash
sudo nano /etc/systemd/system/channels-statistics.service
```

다음 내용 입력:
```ini
[Unit]
Description=Channels Statistics Streamlit App
After=network.target

[Service]
Type=simple
User=사용자명
WorkingDirectory=/home/사용자명/projects/channels_statistics
Environment="PATH=/home/사용자명/projects/channels_statistics/venv/bin"
ExecStart=/home/사용자명/projects/channels_statistics/venv/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**서비스 시작 및 활성화**:
```bash
# 서비스 파일 로드
sudo systemctl daemon-reload

# 서비스 시작
sudo systemctl start channels-statistics

# 서비스 상태 확인
sudo systemctl status channels-statistics

# 부팅 시 자동 시작 설정
sudo systemctl enable channels-statistics
```

**서비스 관리 명령어**:
```bash
# 서비스 시작
sudo systemctl start channels-statistics

# 서비스 중지
sudo systemctl stop channels-statistics

# 서비스 재시작
sudo systemctl restart channels-statistics

# 서비스 상태 확인
sudo systemctl status channels-statistics

# 로그 확인
sudo journalctl -u channels-statistics -f
```

### 방화벽 설정

서버에서 포트 8501이 열려있는지 확인:

```bash
# Ubuntu/Debian
sudo ufw allow 8501/tcp
sudo ufw reload

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=8501/tcp
sudo firewall-cmd --reload
```

## 🌐 접속 확인

브라우저에서 다음 주소로 접속:
```
http://[서버_IP주소]:8501
```

## 📝 업데이트 방법

### Git을 사용하는 경우

```bash
# 서버에 SSH 접속
ssh 사용자명@[서버_IP주소]

# 프로젝트 디렉토리로 이동
cd ~/projects/channels_statistics

# 최신 코드 가져오기
git pull origin main

# 서비스 재시작 (systemd 사용 시)
sudo systemctl restart channels-statistics
```

## 🔍 문제 해결

### 포트가 이미 사용 중인 경우

```bash
# 포트 사용 확인
sudo netstat -tulpn | grep 8501

# 다른 포트 사용
streamlit run app.py --server.port 8502 --server.address 0.0.0.0
```

### 로그 확인

```bash
# systemd 서비스 로그
sudo journalctl -u channels-statistics -f

# 또는 nohup 사용 시
tail -f ~/projects/channels_statistics/app.log
```

### 데이터베이스 연결 오류

`.env` 파일의 DB 정보가 올바른지 확인:
```bash
cat ~/projects/channels_statistics/.env
```

### 권한 문제

```bash
# 파일 권한 확인
ls -la ~/projects/channels_statistics

# 필요시 권한 변경
chmod +x ~/projects/channels_statistics/venv/bin/streamlit
```

## 📌 주의사항

1. **보안**: 
   - `.env` 파일은 절대 Git에 커밋하지 마세요
   - 서버의 `.env` 파일 권한을 제한하세요: `chmod 600 .env`
   - 방화벽에서 필요한 IP만 접속 허용하는 것을 권장합니다

2. **백업**:
   - 정기적으로 `.env` 파일과 `master_data.xlsx` 백업

3. **모니터링**:
   - 서비스가 정상 작동하는지 주기적으로 확인
   - 로그 파일 모니터링

## 📞 추가 도움

문제가 발생하면 다음을 확인하세요:
- 서버 로그: `sudo journalctl -u channels-statistics -f`
- Streamlit 로그: `tail -f app.log`
- 데이터베이스 연결 상태


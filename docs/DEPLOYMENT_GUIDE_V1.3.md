# 운영서버 배포 가이드 v1.3

이 문서는 채널별 예약 통계 시스템 v1.3을 운영서버에 배포하는 방법을 안내합니다.

## 📋 사전 준비사항

### 1. 서버 접속 정보
- **서버 IP**: 211.188.59.125
- **포트**: 8007
- **접속 방법**: SSH

### 2. 현재 서버 상태 확인

서버에 이미 v1.2가 배포되어 있고 systemd 서비스로 실행 중입니다.

## 🚀 v1.3 업데이트 방법

### 방법 1: Git을 통한 업데이트 (권장)

#### Step 1: 서버에 SSH 접속

```bash
ssh allmytour@211.188.59.125
```

#### Step 2: 프로젝트 디렉토리로 이동

```bash
cd /home/allmytour/projects/channels_statistics
```

#### Step 3: 현재 상태 확인

```bash
# 현재 실행 중인 서비스 확인
sudo systemctl status channels-statistics

# 현재 버전 확인
ls -la app*.py
```

#### Step 4: Git에서 최신 코드 가져오기

```bash
# Git 저장소가 연결되어 있다면
git pull origin main

# 또는 특정 브랜치에서 가져오기
git fetch origin
git checkout main
git pull origin main
```

#### Step 5: 새 파일 확인

다음 파일들이 있는지 확인:
- `app_v1.3.py`
- `utils/query_builder_v1.3.py`
- `utils/data_fetcher_v1.3.py`
- `utils/excel_handler_v1.3.py`

```bash
# 파일 확인
ls -la app_v1.3.py
ls -la utils/*v1.3.py
```

#### Step 6: 패키지 업데이트 (필요시)

```bash
# 가상환경 활성화
source venv/bin/activate

# requirements.txt 확인 및 업데이트
pip install -r requirements.txt
```

#### Step 7: systemd 서비스 파일 업데이트

```bash
# 서비스 파일 편집
sudo nano /etc/systemd/system/channels-statistics.service
```

다음 내용으로 수정 (app_v1.2.py → app_v1.3.py):

```ini
[Unit]
Description=Channels Statistics Streamlit App v1.3
After=network.target

[Service]
Type=simple
User=allmytour
WorkingDirectory=/home/allmytour/projects/channels_statistics
Environment="PATH=/home/allmytour/projects/channels_statistics/venv/bin"
ExecStart=/home/allmytour/projects/channels_statistics/venv/bin/streamlit run app_v1.3.py --server.port 8007 --server.address 0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Step 8: 서비스 재시작

```bash
# systemd 데몬 재로드
sudo systemctl daemon-reload

# 서비스 재시작
sudo systemctl restart channels-statistics

# 서비스 상태 확인
sudo systemctl status channels-statistics
```

#### Step 9: 로그 확인

```bash
# 최근 로그 확인
sudo journalctl -u channels-statistics -n 50

# 실시간 로그 확인
sudo journalctl -u channels-statistics -f
```

**정상 실행 시 예상 결과:**
```
Active: active (running)
URL: http://0.0.0.0:8007
```

#### Step 10: 웹 브라우저에서 확인

1. 브라우저에서 접속: `http://211.188.59.125:8007`
2. 기능 테스트:
   - ✅ 날짜유형 선택 (구매일/이용일)
   - ✅ 채널 선택
   - ✅ 조회 버튼 클릭
   - ✅ 요약통계 확인 (2행 4컬럼 구조)
   - ✅ 상세 데이터 확인 (확정/취소 객실수, 취소율 포함)
   - ✅ 엑셀 다운로드 확인

### 방법 2: 직접 파일 업로드

Git이 사용 불가능한 경우:

#### Step 1: 로컬에서 파일 압축

```bash
# 로컬에서 실행
tar -czf v1.3_files.tar.gz \
  app_v1.3.py \
  utils/query_builder_v1.3.py \
  utils/data_fetcher_v1.3.py \
  utils/excel_handler_v1.3.py
```

#### Step 2: 서버에 파일 업로드

```bash
# SCP를 사용한 업로드
scp v1.3_files.tar.gz allmytour@211.188.59.125:/home/allmytour/projects/channels_statistics/
```

#### Step 3: 서버에서 파일 압축 해제

```bash
# 서버에서 실행
cd /home/allmytour/projects/channels_statistics
tar -xzf v1.3_files.tar.gz
```

#### Step 4: 이후 절차는 방법 1의 Step 7부터 동일

## 🔄 v1.2로 되돌리기

문제 발생 시 이전 버전으로 롤백:

```bash
# 서비스 파일 편집
sudo nano /etc/systemd/system/channels-statistics.service
```

`app_v1.3.py` → `app_v1.2.py`로 변경

```bash
# 서비스 재시작
sudo systemctl daemon-reload
sudo systemctl restart channels-statistics
```

## 🔍 문제 해결

### 서비스가 시작되지 않는 경우

```bash
# 상세 로그 확인
sudo journalctl -u channels-statistics -n 100

# 일반적인 원인:
# 1. 파일 경로 오류
# 2. Python 패키지 누락
# 3. .env 파일 문제
# 4. 포트 충돌
```

### 포트 충돌

```bash
# 포트 사용 중인 프로세스 확인
sudo lsof -i :8007
# 또는
sudo fuser -k 8007/tcp

# 서비스 재시작
sudo systemctl restart channels-statistics
```

### 데이터베이스 연결 오류

```bash
# .env 파일 확인
cat /home/allmytour/projects/channels_statistics/.env

# 데이터베이스 연결 테스트
cd /home/allmytour/projects/channels_statistics
source venv/bin/activate
python -c "from config.configdb import test_connection; test_connection()"
```

### master_data.xlsx 파일 확인

```bash
# 파일 존재 확인
ls -la /home/allmytour/projects/channels_statistics/master_data.xlsx

# 파일이 없으면 업로드 필요
```

## 📝 업데이트 체크리스트

배포 전 확인:
- [ ] 로컬에서 v1.3 테스트 완료
- [ ] 모든 새 파일이 서버에 업로드됨
- [ ] systemd 서비스 파일 업데이트됨
- [ ] 서비스 재시작 완료
- [ ] 웹 브라우저에서 기능 테스트 완료
- [ ] 로그에 에러 없음

## 📞 추가 도움

문제가 발생하면:
1. 서비스 로그 확인: `sudo journalctl -u channels-statistics -f`
2. 포트 상태 확인: `sudo netstat -tulpn | grep 8007`
3. 데이터베이스 연결 확인
4. master_data.xlsx 파일 확인


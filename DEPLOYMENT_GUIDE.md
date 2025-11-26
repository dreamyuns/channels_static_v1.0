# GitHub 업로드 및 라이브 서버 배포 가이드

## 📋 목차
1. [일반적인 배포 프로세스](#1-일반적인-배포-프로세스)
2. [충돌 발생 시 해결 방법](#2-충돌-발생-시-해결-방법)
3. [운영 서버 배포](#3-운영-서버-배포)
4. [프로세스 재시작](#4-프로세스-재시작)
5. [롤백 방법](#5-롤백-방법)
6. [문제 해결](#6-문제-해결)

---

## 1. 일반적인 배포 프로세스

### 1-1. 로컬에서 Git 상태 확인

```powershell
# 프로젝트 디렉토리로 이동
cd C:\Users\윤성균\Documents\python_study\통계프로그램

# Git 상태 확인
git status

# 변경된 파일 확인
git diff
```

### 1-2. 변경사항 커밋

```powershell
# 변경된 파일 스테이징
git add app_v1.22_hotel.py

# 커밋 메시지 작성
git commit -m "fix: 선택한 숙소 목록 체크박스 삭제 기능 개선 (v1.22)

- multiselect 세션 상태 동기화 로직 개선 (플래그 기반)
- 체크박스에서 삭제한 항목이 multiselect에 다시 나타나지 않도록 수정
- 사용자가 multiselect에서 선택할 수 있도록 세션 상태 관리 개선"
```

### 1-3. GitHub에 푸시

```powershell
# 원격 저장소 확인
git remote -v

# GitHub에 푸시
git push origin main
```

---

## 2. 충돌 발생 시 해결 방법

### 2-1. 원격 변경사항 가져오기

```powershell
# 원격 저장소의 변경사항 가져오기
git pull origin main
```

### 2-2-A. 충돌이 없는 경우

```powershell
# 자동 병합 완료 후 바로 푸시
git push origin main
```

### 2-2-B. 충돌이 있는 경우

```powershell
# 충돌 파일 확인
git status

# 충돌 해결 후
git add app_v1.22_hotel.py

# 병합 커밋
git commit -m "merge: 원격 변경사항 병합"

# 푸시
git push origin main
```

---

## 3. 운영 서버 배포

### 3-1. SSH 접속

```bash
# SSH 접속
ssh root@110.165.19.152

# 또는 allmytour 사용자로 직접 접속
ssh allmytour@110.165.19.152
```

### 3-2. 프로젝트 디렉토리로 이동

```bash
# 프로젝트 디렉토리로 이동
cd ~/projects/channels_statistics

# 또는 절대 경로
cd /home/allmytour/projects/channels_statistics
```

### 3-3. 최신 코드 가져오기

```bash
# 가상환경 활성화 (필요한 경우)
source venv/bin/activate

# 최신 코드 가져오기
git pull origin main

# Git 상태 확인
git status

# 최근 커밋 확인
git log --oneline -5
```

### 3-4. 배포 확인

```bash
# 파일 버전 확인 (특정 코드가 있는지)
grep -n "_multiselect_sync_needed" app_v1.22_hotel.py

# 파일 수정 시간 확인
ls -lh app_v1.22_hotel.py
```

---

## 4. 프로세스 재시작

### ⚡ 빠른 재시작 (한 번에 실행)

**GitHub에서 코드를 가져온 후 바로 재시작하려면:**

```bash
# SSH 접속 후 한 번에 실행
ssh allmytour@110.165.19.152
cd ~/projects/channels_statistics && source venv/bin/activate && git pull origin main && kill $(lsof -ti :8008) 2>/dev/null; nohup streamlit run app_v1.22_hotel.py --server.port 8008 > /tmp/streamlit-hotel-8008.log 2>&1 &
```

**또는 단계별로:**

```bash
# 1. SSH 접속
ssh allmytour@110.165.19.152

# 2. 프로젝트 디렉토리로 이동 및 가상환경 활성화
cd ~/projects/channels_statistics
source venv/bin/activate

# 3. 최신 코드 가져오기
git pull origin main

# 4. 기존 프로세스 종료 (포트 8008)
kill $(lsof -ti :8008) 2>/dev/null

# 5. 새로 실행
nohup streamlit run app_v1.22_hotel.py --server.port 8008 > /tmp/streamlit-hotel-8008.log 2>&1 &

# 6. 확인
ps aux | grep streamlit | grep -v grep
```

---

### 4-1. 실행 중인 프로세스 확인

```bash
# Streamlit 프로세스 확인
ps aux | grep streamlit | grep -v grep

# 포트 사용 확인
lsof -i :8008
# 또는
lsof -i :8007
```

### 4-2. 프로세스 종료

```bash
# 방법 1: 포트로 직접 종료 (가장 간단)
kill $(lsof -ti :8008) 2>/dev/null

# 방법 2: PID 확인 후 종료
# 먼저 PID 확인
lsof -i :8008
# 또는
ps aux | grep streamlit | grep -v grep

# PID 확인 후 종료
kill <PID>

# 예시: PID 464923 종료
kill 464923

# 강제 종료 (필요한 경우)
kill -9 <PID>
```

### 4-3. 새로 실행

```bash
# 프로젝트 디렉토리로 이동
cd ~/projects/channels_statistics

# 가상환경 활성화
source venv/bin/activate

# 포트 8008로 실행
nohup streamlit run app_v1.22_hotel.py --server.port 8008 > /tmp/streamlit-hotel-8008.log 2>&1 &

# 포트 8007로 실행 (다른 파일인 경우)
nohup streamlit run app_v1.61.py --server.port 8007 > /tmp/streamlit-channels-8007.log 2>&1 &
```

### 4-4. 배포 확인

```bash
# 프로세스 확인
ps aux | grep streamlit | grep -v grep

# 포트 확인
lsof -i :8008

# 실행 중인 파일 확인
cat /proc/$(lsof -ti :8008)/cmdline | tr '\0' ' '

# 로그 확인
tail -f /tmp/streamlit-hotel-8008.log
```

---

## 5. 롤백 방법

### 5-1. 이전 커밋으로 되돌리기

```powershell
# 로컬에서
cd C:\Users\윤성균\Documents\python_study\통계프로그램

# 커밋 히스토리 확인
git log --oneline -10

# 특정 파일을 이전 커밋으로 되돌리기
git checkout <이전_커밋_해시> app_v1.22_hotel.py

# 커밋
git commit -m "rollback: 이전 버전으로 롤백"

# 푸시
git push origin main
```

### 5-2. 운영 서버에서 롤백

```bash
# 운영 서버에서
cd ~/projects/channels_statistics

# 이전 커밋으로 되돌리기
git checkout <이전_커밋_해시> app_v1.22_hotel.py

# 또는 전체 프로젝트를 이전 커밋으로
git reset --hard <이전_커밋_해시>

# 프로세스 재시작 (4단계 참고)
```

---

## 6. 문제 해결

### 6-1. Git Push 실패

**문제**: `! [rejected] main -> main (fetch first)`

**해결**:
```powershell
# 1. 원격 변경사항 가져오기
git pull origin main

# 2. 충돌 해결 후
git push origin main
```

### 6-2. 포트가 이미 사용 중

**문제**: `Port 8008 is already in use`

**해결**:
```bash
# 1. 포트 사용 중인 프로세스 확인
lsof -i :8008

# 2. 프로세스 종료
kill <PID>

# 3. 포트 확인
lsof -i :8008

# 4. 다시 실행
nohup streamlit run app_v1.22_hotel.py --server.port 8008 > /tmp/streamlit-hotel-8008.log 2>&1 &
```

### 6-3. 프로세스가 실행되지 않음

**해결**:
```bash
# 1. 가상환경 확인
source venv/bin/activate

# 2. Streamlit 설치 확인
pip list | grep streamlit

# 3. 파일 경로 확인
pwd
ls -la app_v1.22_hotel.py

# 4. 수동 실행으로 오류 확인
streamlit run app_v1.22_hotel.py --server.port 8008
```

### 6-4. 배포 후 변경사항이 반영되지 않음

**해결**:
```bash
# 1. Git 상태 확인
cd ~/projects/channels_statistics
git status
git log --oneline -3

# 2. 파일 내용 확인
grep -n "특정_코드" app_v1.22_hotel.py

# 3. 프로세스가 올바른 파일을 실행 중인지 확인
cat /proc/$(lsof -ti :8008)/cmdline | tr '\0' ' '

# 4. 프로세스 재시작 (4단계 참고)
```

---

## 7. 시나리오별 체크리스트

### 시나리오 1: 일반적인 코드 수정 후 배포

- [ ] 로컬에서 코드 수정
- [ ] `git status`로 변경사항 확인
- [ ] `git add <파일명>`로 스테이징
- [ ] `git commit -m "메시지"`로 커밋
- [ ] `git push origin main`으로 푸시
- [ ] 운영 서버 SSH 접속
- [ ] `cd ~/projects/channels_statistics`
- [ ] `git pull origin main`
- [ ] 프로세스 재시작 (4단계 참고)
- [ ] 브라우저에서 테스트

### 시나리오 2: 충돌 발생 시

- [ ] `git push origin main` 실패
- [ ] `git pull origin main` 실행
- [ ] 충돌 파일 확인
- [ ] 충돌 해결
- [ ] `git add <파일명>`
- [ ] `git commit -m "merge: 충돌 해결"`
- [ ] `git push origin main`
- [ ] 운영 서버 배포 (3단계 참고)

### 시나리오 3: 프로세스만 재시작

- [ ] 운영 서버 SSH 접속
- [ ] `ps aux | grep streamlit`로 프로세스 확인
- [ ] `lsof -i :8008`로 포트 확인
- [ ] `kill <PID>`로 프로세스 종료
- [ ] `nohup streamlit run app_v1.22_hotel.py --server.port 8008 > /tmp/streamlit-hotel-8008.log 2>&1 &`
- [ ] `ps aux | grep streamlit`로 확인
- [ ] 브라우저에서 테스트

### 시나리오 4: 롤백

- [ ] 로컬에서 `git log --oneline -10`으로 커밋 확인
- [ ] `git checkout <커밋_해시> <파일명>`로 파일 되돌리기
- [ ] `git commit -m "rollback: 이전 버전으로 롤백"`
- [ ] `git push origin main`
- [ ] 운영 서버에서 `git pull origin main`
- [ ] 프로세스 재시작 (4단계 참고)

---

## 8. 자주 사용하는 명령어 모음

### 로컬 (Windows PowerShell)

```powershell
# Git 상태 확인
git status

# 변경사항 확인
git diff

# 커밋
git add <파일명>
git commit -m "메시지"

# 푸시
git push origin main

# 원격 변경사항 가져오기
git pull origin main

# 커밋 히스토리
git log --oneline -10
```

### 운영 서버 (Linux)

```bash
# 프로젝트 디렉토리 이동
cd ~/projects/channels_statistics

# 가상환경 활성화
source venv/bin/activate

# Git pull
git pull origin main

# 프로세스 확인
ps aux | grep streamlit | grep -v grep

# 포트 확인
lsof -i :8008

# 프로세스 종료
kill <PID>

# 실행
nohup streamlit run app_v1.22_hotel.py --server.port 8008 > /tmp/streamlit-hotel-8008.log 2>&1 &

# 로그 확인
tail -f /tmp/streamlit-hotel-8008.log
```

---

## 9. 접속 정보

- **GitHub 저장소**: https://github.com/dreamyuns/channels_static_v1.0.git
- **브랜치**: main
- **운영 서버**: root@110.165.19.152
- **프로젝트 경로**: /home/allmytour/projects/channels_statistics
- **포트**: 8007 (channels), 8008 (hotel)
- **접속 URL**: 
  - http://211.188.59.125:8007/ (channels)
  - http://211.188.59.125:8008/ (hotel)

---

## 10. 주의사항

1. **프로세스 재시작 전** 항상 현재 실행 중인 프로세스를 확인하세요
2. **Git Push 전** 로컬에서 테스트를 완료하세요
3. **운영 서버 배포 후** 반드시 브라우저에서 테스트하세요
4. **롤백 시** 이전 커밋 해시를 정확히 확인하세요
5. **충돌 발생 시** 신중하게 해결하세요 (원격 변경사항 손실 주의)

---

## 11. 빠른 참조

### 전체 배포 프로세스 (한 번에)

**로컬**:
```powershell
cd C:\Users\윤성균\Documents\python_study\통계프로그램
git add app_v1.22_hotel.py
git commit -m "fix: 변경사항 설명"
git push origin main
```

**운영 서버**:
```bash
ssh allmytour@110.165.19.152
cd ~/projects/channels_statistics
source venv/bin/activate
git pull origin main
kill $(lsof -ti :8008)
nohup streamlit run app_v1.22_hotel.py --server.port 8008 > /tmp/streamlit-hotel-8008.log 2>&1 &
```

---

**문서 버전**: 1.0  
**최종 업데이트**: 2025-11-11


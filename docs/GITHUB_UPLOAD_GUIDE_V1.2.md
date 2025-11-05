# GitHub 업로드 가이드 v1.2

이 문서는 v1.2까지의 변경사항을 GitHub에 안전하게 업로드하는 방법을 안내합니다.

## ⚠️ 중요: 보안 체크리스트

업로드 전에 반드시 확인하세요:

- [ ] `.env` 파일이 `.gitignore`에 포함되어 있는지 확인
- [ ] `env.py` 파일이 `.gitignore`에 포함되어 있는지 확인  
- [ ] `master_data.xlsx` 파일이 `.gitignore`에 포함되어 있는지 확인
- [ ] `venv/` 폴더가 `.gitignore`에 포함되어 있는지 확인
- [ ] 코드에 하드코딩된 서버 접속 정보가 없는지 확인

## 📦 v1.2 업로드 단계

### 1. 현재 상태 확인

```bash
# 현재 Git 상태 확인
git status

# 현재 브랜치 확인
git branch

# 원격 저장소 확인
git remote -v
```

### 2. 변경사항 확인

```bash
# 변경된 파일 목록 확인
git status

# 변경 내용 확인
git diff
```

### 3. 새 파일 추가

v1.2에서 추가된 파일들:
- `app_v1.2.py`
- `utils/query_builder_v1.2.py`
- `utils/data_fetcher_v1.2.py`
- `utils/excel_handler_v1.2.py`
- `config/master_data_loader.py` (업데이트된 경우)
- `config/order_status_mapping.py` (업데이트된 경우)
- `README.md` (업데이트)
- `docs/DEPLOYMENT_GUIDE_V1.2.md` (새 문서)

### 4. 파일 추가 및 커밋

```bash
# 모든 변경사항 추가
git add .

# 또는 특정 파일만 추가
git add app_v1.2.py
git add utils/*v1.2.py
git add README.md
git add docs/DEPLOYMENT_GUIDE_V1.2.md

# 커밋 메시지 작성
git commit -m "feat: v1.2 업데이트

- 새로운 컬럼 구조 추가 (판매숙소수, 총객실수, 총 입금가, 총 실구매가, 총 수익, 수익률)
- 날짜유형 필터 추가 (구매일/이용일)
- 예약상태 필터 추가 (확정/취소)
- order_pay 테이블 JOIN 추가
- 상위 10개만 표시 기능
- 요약 통계 개선
- 검색 조건 유지 기능
- booking_master_offer 테이블 제거"
```

### 5. 커밋 전 최종 확인

```bash
# 커밋될 파일 목록 확인
git status

# 민감한 파일이 포함되어 있지 않은지 확인
git diff --cached --name-only
```

**⚠️ 다음 파일들이 목록에 나타나면 안 됩니다:**
- `.env`
- `env.py`
- `master_data.xlsx`
- `venv/` 폴더 내 파일들

### 6. GitHub에 푸시

```bash
# 메인 브랜치로 푸시
git push origin main

# 또는 특정 브랜치에 푸시
git push origin main:v1.2
```

### 7. GitHub에서 확인

1. GitHub 웹사이트 접속: https://github.com/dreamyuns/channels_static_v1.0
2. 다음을 확인:
   - ✅ 커밋이 정상적으로 업로드되었는지
   - ✅ `.env` 파일이 저장소에 없는지
   - ✅ `env.py` 파일이 저장소에 없는지
   - ✅ `master_data.xlsx` 파일이 저장소에 없는지
   - ✅ 새 파일들이 모두 포함되었는지

## 🔄 업데이트 후 서버 배포

GitHub 업로드 후 운영서버에 배포하려면:

1. `docs/DEPLOYMENT_GUIDE_V1.2.md` 참고
2. 서버에서 `git pull` 실행
3. systemd 서비스 재시작

## 📝 커밋 메시지 가이드

### 좋은 커밋 메시지 예시

```
feat: v1.2 업데이트 - 새로운 컬럼 구조 및 필터 추가

주요 변경사항:
- 새로운 컬럼: 판매숙소수, 총객실수, 총 입금가, 총 실구매가, 총 수익, 수익률
- 날짜유형 필터 추가 (구매일/이용일)
- 예약상태 필터 추가 (확정/취소)
- order_pay 테이블 JOIN 추가
- 상위 10개만 표시 기능
- 요약 통계 개선
- 검색 조건 유지 기능
```

### 커밋 메시지 규칙

- `feat:`: 새로운 기능 추가
- `fix:`: 버그 수정
- `docs:`: 문서 수정
- `refactor:`: 코드 리팩토링
- `style:`: 코드 포맷팅
- `test:`: 테스트 추가

## 🚨 문제 해결

### 이미 민감한 파일이 커밋되었다면?

**즉시 조치가 필요합니다!**

1. GitHub에서 해당 파일을 삭제
2. Git 히스토리에서 완전히 제거:

```bash
# .env 파일을 히스토리에서 제거
git filter-branch --force --index-filter "git rm --cached --ignore-unmatch .env" --prune-empty --tag-name-filter cat -- --all

# 강제 푸시 (주의: 팀원과 협의 필요)
git push origin --force --all
```

**더 안전한 방법**: GitHub 저장소를 삭제하고 새로 만드는 것을 권장합니다.

### 충돌 발생 시

```bash
# 원격 저장소의 최신 변경사항 가져오기
git fetch origin

# 현재 브랜치와 병합
git merge origin/main

# 충돌 해결 후
git add .
git commit -m "merge: 충돌 해결"
git push origin main
```

## 📌 다음 단계

1. ✅ GitHub 업로드 완료
2. ✅ 운영서버 배포 (`docs/DEPLOYMENT_GUIDE_V1.2.md` 참고)
3. ✅ 기능 테스트
4. ✅ 문서 업데이트 확인


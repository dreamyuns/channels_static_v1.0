# GitHub 업로드 가이드

이 문서는 프로젝트를 GitHub에 안전하게 업로드하는 방법을 안내합니다.

## ⚠️ 중요: 보안 체크리스트

업로드 전에 반드시 확인하세요:

- [ ] `.env` 파일이 `.gitignore`에 포함되어 있는지 확인
- [ ] `env.py` 파일이 `.gitignore`에 포함되어 있는지 확인  
- [ ] `master_data.xlsx` 파일이 `.gitignore`에 포함되어 있는지 확인
- [ ] 코드에 하드코딩된 서버 접속 정보가 없는지 확인

## 단계별 업로드 방법

### 1. Git 초기화 (아직 안 했다면)

```bash
git init
```

### 2. 원격 저장소 연결

```bash
git remote add origin https://github.com/dreamyuns/channels_static_v1.0.git
```

### 3. 파일 추가 및 커밋

```bash
# 모든 파일 추가 (민감한 파일은 .gitignore에 의해 자동 제외됨)
git add .

# 커밋
git commit -m "Initial commit: 채널별 예약 통계 시스템"
```

### 4. GitHub에 푸시

```bash
git branch -M main
git push -u origin main
```

## 업로드 전 확인사항

### .gitignore 확인

다음 명령어로 실제로 제외될 파일들을 확인하세요:

```bash
git status
```

다음 파일들이 목록에 나타나면 **절대 안 됩니다**:
- `.env`
- `env.py`
- `master_data.xlsx`
- `channel_data_check.xlsx`
- `venv/` 폴더

### 커밋 전 최종 확인

```bash
# 커밋될 파일 목록 확인
git status

# 만약 민감한 파일이 보이면
git reset  # 추가 취소
```

## 문제 해결

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

## 업로드 후 확인

GitHub 웹사이트에서 다음을 확인하세요:

1. `.env` 파일이 저장소에 없는지
2. `env.py` 파일이 저장소에 없는지
3. `master_data.xlsx` 파일이 저장소에 없는지

## 다음 단계

1. `.env.example` 파일을 복사하여 `.env` 파일 생성
2. 실제 데이터베이스 접속 정보 입력
3. 애플리케이션 실행 및 테스트


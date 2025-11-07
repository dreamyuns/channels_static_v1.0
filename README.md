# 채널별 예약 통계 시스템 v1.6

allmytour.com의 다양한 예약 채널별 통계를 실시간으로 조회하고 엑셀로 추출할 수 있는 백오피스 시스템입니다.

## 🎯 주요 기능

- 📊 **날짜별/채널별 예약 데이터 조회**
  - 구매일(예약일) 또는 이용일(체크인) 기준 조회
  - 다중 채널 선택 지원
  - 예약상태는 상세 데이터에서 확인 (확정/취소 객실수, 취소율)
- 📈 **요약 통계 대시보드**
  - 1행: 총 예약건수, 총 입금가, 총 실구매가, 총 수익
  - 2행: 총 객실수, 확정 객실 수, 취소 객실 수, 취소율
  - 실시간 집계 및 계산
- 📋 **상세 데이터 조회**
  - 판매숙소수, 예약건수, 총객실수, 확정객실수, 취소객실수, 취소율
  - 총 입금가, 총 실구매가, 총 수익, 수익률
  - 상위 10개 미리보기 (전체 데이터는 엑셀 다운로드)
- 📥 **원클릭 엑셀 다운로드**
  - 날짜유형별 시트 자동 생성 (구매일/이용일)
  - 요약 통계 포함
- 🔄 **검색 조건 유지**
  - 검색 조건 변경 시 결과 화면 유지
  - 조회 버튼 클릭 시에만 새로 조회

## 🚀 버전 히스토리

### v1.6 (현재 버전) - 2025년 1월
- 🔐 **사용자 인증 기능 추가**
  - `tblmanager` 테이블 기반 로그인 시스템
  - `user_status = '1'`인 사용자만 접근 가능
  - bcrypt, MD5, SHA256, 평문 비밀번호 지원
  - 쿠키 기반 인증 상태 유지 (새로고침 시에도 로그인 유지)
- 📝 **로깅 시스템 추가**
  - 타입별 로그 파일 분리: `auth.log`, `error.log`, `access.log`, `app.log`
  - 30일 보관 정책
  - 5초 이상 쿼리 자동 로깅
- ✨ **UI/UX 개선**
  - 로딩 표시 개선: `st.status` 사용으로 더 눈에 띄는 로딩 표시
  - 로그인 실패 시 빨간색 경고 메시지 표시
  - 로그인 페이지와 메인 페이지 분리
  - 헤더에 로그아웃 버튼 추가
- 🔄 **세션 관리 개선**
  - 세션 타임아웃 제거 (새로고침 문제 해결)
  - 쿠키 기반 인증 복원으로 브라우저 새로고침 시에도 로그인 상태 유지

### v1.5 - 2025년 1월
- 🔄 **입금가 계산 방식 변경**: `product_rateplan_price` → `order_item` 테이블 사용
  - `order_item.due_price`를 사용하여 예약당시 금액 정확히 반영
  - 2박 이상 예약 시 각 날짜별 `due_price` 합산
  - 입금가 계산식: `SUM(order_item.due_price) * room_cnt` (terms는 곱하지 않음)
- 🐛 **중복 계산 문제 해결**
  - `order_item` JOIN 제거, 서브쿼리로 처리하여 row 중복 방지
  - `terms * room_cnt` 계산은 `order_product`에서 직접 계산
  - `order_pay.total_amount`는 직접 JOIN 사용 (1:1 관계)
- ✅ **데이터 정확성 개선**
  - 총 입금가, 총 실구매가, 총객실수, 확정/취소 객실수 정확한 계산
- ✨ **UI 개선**
  - 날짜 범위 선택 범위 확대: 이용일 기준 90일 후까지 선택 가능
  - 구매일 기준은 어제까지만 선택 가능 (당일 데이터 조회 불가)
  - 결과 화면에 사용안내 툴팁 추가 (접기/펼치기)

### v1.4
- 🔄 입금가 계산: `product_rateplan_price.due_price` 사용
- 🔄 날짜 매핑: `product_rateplan_price.date` = `order_product.checkin_date`
- 🔄 입금가 계산식: `terms * room_cnt * due_price`
- 🐛 입금가 데이터 불일치 문제 발견 및 디버깅

### v1.3
- ✨ 총객실수 계산 변경: `terms * room_cnt` 기준
- ✨ 확정/취소 객실수 추가 (예약상태별 집계)
- ✨ 취소율 추가 (소수점 1자리, % 표시)
- ✨ 요약통계 레이아웃 변경 (2행 4컬럼 구조)
- 🗑️ 예약상태 필터 UI 제거 (백엔드는 항상 '전체'로 고정)
- ✨ 상세 데이터에 확정/취소 객실수, 취소율 컬럼 추가

### v1.2
- ✨ 새로운 컬럼 구조 추가
  - 판매숙소수, 총객실수, 총 입금가, 총 실구매가, 총 수익, 수익률
- ✨ 날짜유형 필터 추가 (구매일/이용일)
- ✨ 예약상태 필터 추가 (확정/취소)
- ✨ order_pay 테이블 JOIN 추가
- ✨ 상위 10개만 표시 기능
- ✨ 요약 통계 개선
- ✨ 검색 조건 유지 기능
- 🗑️ booking_master_offer 테이블 제거

### v1.1
- ✨ 날짜유형 필터 추가
- ✨ 예약상태 필터 추가
- ✨ 초기화 버튼 추가
- ✨ UI 상태 유지 기능

### v1.0
- 🎉 초기 릴리스
- 기본 채널별 통계 조회 기능

## 🛠️ 기술 스택

- **Frontend**: Streamlit
- **Backend**: Python 3.12+
- **Database**: MySQL (SQLAlchemy)
- **Data Processing**: Pandas
- **Excel Export**: openpyxl
- **Authentication**: bcrypt, 쿠키 기반 세션 관리
- **Logging**: Python logging (파일 로테이션)

## 📦 설치 방법

### 1. 저장소 클론

```bash
git clone https://github.com/dreamyuns/channels_static_v1.0.git
cd channels_static_v1.0
```

### 2. 가상환경 생성 및 활성화

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python -m venv venv
source venv/bin/activate
```

### 3. 패키지 설치

```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정

`.env.example` 파일을 참고하여 `.env` 파일을 생성하고 데이터베이스 연결 정보를 입력하세요.

```bash
# .env 파일 생성
DB_HOST=your_database_host
DB_PORT=3306
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_NAME=your_database_name
```

**⚠️ 중요**: `.env` 파일은 절대 Git에 커밋하지 마세요!

### 5. master_data.xlsx 파일 준비

프로젝트 루트에 `master_data.xlsx` 파일을 배치하세요. 다음 시트가 필요합니다:
- `date_types`: 날짜유형 마스터 (date_types_en, date_types_kr)
- `order_status`: 예약상태 마스터 (status_en, status_kr)
- `channels`: 채널 마스터 (ID, 채널명 등)

### 6. 애플리케이션 실행

```bash
# v1.6 실행 (최신)
streamlit run app_v1.6.py

# 또는 v1.5 실행
streamlit run app_v1.5.py

# 또는 v1.4 실행
streamlit run app_v1.4.py

# 또는 v1.3 실행
streamlit run app_v1.3.py

# 또는 v1.2 실행
streamlit run app_v1.2.py

# 또는 v1.1 실행
streamlit run app_v1.1.py

# 또는 v1.0 실행
streamlit run app.py
```

브라우저에서 `http://localhost:8501`로 접속하세요.

**v1.6부터는 로그인이 필요합니다:**
- `tblmanager` 테이블의 `admin_id`와 `passwd`로 로그인
- `user_status = '1'`인 계정만 접근 가능

## 📁 프로젝트 구조

```
통계프로그램/
├── app.py                 # Streamlit 메인 애플리케이션 (v1.0)
├── app_v1.1.py           # v1.1 버전
├── app_v1.2.py           # v1.2 버전
├── app_v1.3.py           # v1.3 버전
├── app_v1.4.py           # v1.4 버전
├── app_v1.5.py           # v1.5 버전
├── app_v1.6.py           # v1.6 버전 (현재)
├── config/
│   ├── channels.py        # 채널 설정 및 매핑
│   ├── channel_mapping.py # master_data.xlsx 매핑 로더
│   ├── configdb.py        # 데이터베이스 연결 설정
│   ├── master_data_loader.py # master_data.xlsx 로더
│   └── order_status_mapping.py # 예약상태 그룹핑 정의
├── utils/
│   ├── data_fetcher.py   # 데이터 조회 함수 (v1.0)
│   ├── data_fetcher_v1.1.py # v1.1 버전
│   ├── data_fetcher_v1.2.py # v1.2 버전
│   ├── data_fetcher_v1.3.py # v1.3 버전
│   ├── data_fetcher_v1.4.py # v1.4 버전
│   ├── data_fetcher_v1.5.py # v1.5 버전 (현재)
│   ├── query_builder.py  # SQL 쿼리 빌더 (v1.0)
│   ├── query_builder_v1.1.py # v1.1 버전
│   ├── query_builder_v1.2.py # v1.2 버전
│   ├── query_builder_v1.3.py # v1.3 버전
│   ├── query_builder_v1.4.py # v1.4 버전
│   ├── query_builder_v1.5.py # v1.5 버전 (현재)
│   ├── excel_handler.py   # 엑셀 다운로드 처리 (v1.0)
│   ├── excel_handler_v1.2.py # v1.2 버전
│   ├── excel_handler_v1.3.py # v1.3 버전
│   ├── excel_handler_v1.4.py # v1.4 버전
│   ├── excel_handler_v1.5.py # v1.5 버전 (현재)
│   ├── auth.py            # 사용자 인증 모듈 (v1.6)
│   └── logger.py           # 로깅 모듈 (v1.6)
├── logs/                  # 로그 파일 저장 폴더 (v1.6)
│   ├── auth.log           # 인증 관련 로그
│   ├── error.log          # 에러 로그
│   ├── access.log         # 접근 로그
│   └── app.log            # 일반 애플리케이션 로그
├── backup/               # 백업 파일
├── docs/                 # 문서 폴더
├── test/                 # 테스트 파일
├── requirements.txt      # 패키지 의존성
├── .env.example          # 환경 변수 템플릿
├── master_data.xlsx      # 마스터 데이터 (Git에 커밋하지 않음)
└── README.md             # 프로젝트 문서
```

## 📖 사용 방법

1. 웹 브라우저에서 애플리케이션 접속
2. **로그인** (v1.6부터 필수)
   - `tblmanager` 테이블의 `admin_id`와 `passwd` 입력
   - `user_status = '1'`인 계정만 접근 가능
   - 로그인 상태는 브라우저 쿠키에 저장되어 새로고침 시에도 유지됨
3. 사이드바에서 검색 조건 설정:
   - **날짜유형**: 구매일 또는 이용일 선택
   - **시작일 및 종료일** 선택
     - 이용일 기준: 오늘 기준 90일 전 ~ 90일 후까지 선택 가능
     - 구매일 기준: 오늘 기준 90일 전 ~ 어제까지 선택 가능 (당일 데이터 조회 불가)
   - **조회할 채널** 선택 (멀티셀렉트)
   - **예약상태**: 상세 데이터에서 확인 가능 (확정/취소 객실수, 취소율)
3. **"조회"** 버튼 클릭
4. 결과 확인:
   - 결과 화면 상단의 "📌 사용 안내"를 클릭하여 사용 방법 확인 가능
   - 요약 통계 확인 (2행 4컬럼 구조)
   - 상세 데이터 상위 10개 미리보기 (확정/취소 객실수, 취소율 포함)
5. **엑셀 다운로드** 버튼으로 전체 데이터 다운로드

## 🗄️ 데이터베이스 구조

### 주요 테이블

- `order_product`: 예약 상품 데이터
  - `idx`: 예약 상품 ID (PK)
  - `create_date`: 구매일(예약일)
  - `checkin_date`: 이용일(체크인)
  - `order_product_status`: 예약상태
  - `order_channel_idx`: 채널 ID
  - `order_pay_idx`: 결제 정보 ID
  - `product_name`: 숙소명
  - `terms`: 숙박기간 (박)
  - `room_cnt`: 객실수
  - `original_amount`: 입금가 (레거시, 사용 안 함)
- `order_item`: 예약 상세 항목 (v1.5부터 사용)
  - `idx`: 항목 ID (PK)
  - `order_product_idx`: 예약 상품 ID (FK → order_product.idx)
  - `stay_date`: 숙박일
  - `due_price`: 해당 날짜의 입금가
  - **특징**: 2박 이상 예약 시 각 날짜별로 row 생성 (예: 4박 → 4개 row)
- `order_pay`: 결제 정보
  - `idx`: 결제 ID (PK, order_product.order_pay_idx와 연결)
  - `total_amount`: 실구매가 (order_product당 1개 값)
- `common_code`: 채널명 마스터 데이터
  - `code_id`: 채널 ID (order_product.order_channel_idx와 연결)
  - `code_name`: 채널명
  - `parent_idx`: 부모 코드 ID (1 = 채널)
- `tblmanager`: 관리자 계정 정보 (v1.6부터 사용)
  - `admin_id`: 관리자 ID (로그인 ID)
  - `passwd`: 비밀번호 (bcrypt 해시, 길이 60)
  - `user_status`: 계정 상태 ('1' = 활성, '0' = 비활성)

### 테이블 관계

```
order_product (1) ──< (N) order_item
    │
    └── (1) ──< (1) order_pay
    │
    └── (N) ──< (1) common_code
```

### v1.5 입금가 계산 로직

**입금가 (`total_deposit`)**:
```sql
SUM(COALESCE((
    SELECT SUM(oi2.due_price)
    FROM order_item oi2
    WHERE oi2.order_product_idx = op.idx
), 0) * COALESCE(op.room_cnt, 1))
```

- `order_item` 테이블에서 각 예약의 모든 `due_price` 합산 후 `room_cnt` 곱하기
- `terms`는 곱하지 않음 (이미 날짜별 row로 합산되기 때문)
- 예: 4박 2객실 예약
  - `order_item`에 4개 row (각 날짜별)
  - 각 row의 `due_price` 합산 = 400,000원
  - 입금가 = 400,000 × 2(객실수) = 800,000원

**총객실수 (`total_rooms`)**:
```sql
SUM(COALESCE(op.terms, 1) * COALESCE(op.room_cnt, 0))
```

- `order_product` 테이블에서 직접 계산
- `order_item` JOIN과 무관하므로 중복 없음

**총 실구매가 (`total_purchase`)**:
```sql
SUM(COALESCE(opay.total_amount, 0))
```

- `order_pay` 테이블과 직접 JOIN (1:1 관계)
- `order_item` JOIN과 무관하므로 중복 없음

## 🔒 보안 주의사항

- ⚠️ **절대 커밋하지 마세요**:
  - `.env` 파일 (데이터베이스 접속 정보)
  - `master_data.xlsx` (민감한 데이터)
  - `env.py` (하드코딩된 접속 정보 포함)
  - `venv/` 폴더
  - `logs/` 폴더 (로그 파일에 민감한 정보 포함될 수 있음)

### v1.6 보안 기능

- **사용자 인증**: `tblmanager` 테이블 기반 로그인 시스템
- **계정 상태 확인**: `user_status = '1'`인 사용자만 접근 가능
- **비밀번호 해싱**: bcrypt, MD5, SHA256, 평문 순서로 검증 시도
- **세션 관리**: 쿠키 기반 인증 상태 유지 (1일 유효)
- **로깅**: 모든 인증 시도와 접근 기록 저장

## 🔧 v1.6 주요 변경사항 상세

### 사용자 인증 시스템

**인증 방식**:
- `tblmanager` 테이블의 `admin_id`와 `passwd` 사용
- `user_status = '1'`인 계정만 접근 가능
- 비밀번호 검증 순서: bcrypt (길이 60) → MD5 (길이 32) → SHA256 (길이 64) → 평문

**세션 관리**:
- Streamlit `session_state`와 브라우저 쿠키를 함께 사용
- 쿠키에 `auth_admin_id` 저장 (1일 유효)
- 브라우저 새로고침 시 쿠키에서 인증 정보 복원
- 로그아웃 시 세션 상태와 쿠키 모두 삭제

**로그인 페이지**:
- 별도 페이지로 구현
- 로그인 실패 시 빨간색 경고 메시지 표시
- 헤더에 로그아웃 버튼 추가

### 로깅 시스템

**로그 파일 구조**:
- `logs/auth.log`: 인증 관련 로그 (로그인, 로그아웃, 인증 실패)
- `logs/error.log`: 에러 로그 (예외, SQL 오류)
- `logs/access.log`: 접근 로그 (페이지 접근, 쿼리 실행)
- `logs/app.log`: 일반 애플리케이션 로그

**로깅 정책**:
- 일별 로그 파일 로테이션
- 30일 보관 후 자동 삭제
- 5초 이상 실행된 쿼리 자동 로깅

### UI/UX 개선

**로딩 표시**:
- `st.spinner` → `st.status`로 변경
- 더 눈에 띄는 로딩 표시
- 검색 결과 로딩 시에도 큰 로딩 표시

**에러 메시지**:
- 로그인 실패 시 빨간색 경고 메시지: "⚠️ ID / PW를 다시 확인해주세요"

## 🔧 v1.5 주요 변경사항 상세

### 입금가 계산 방식 변경

**v1.4 이전**:
- `product_rateplan_price.due_price` 사용
- 계산식: `terms * room_cnt * due_price`
- 날짜 매핑: `product_rateplan_price.date` = `order_product.checkin_date`

**v1.5**:
- `order_item.due_price` 사용
- 계산식: `SUM(order_item.due_price) * room_cnt`
  - `order_item`에 날짜별 row가 생성되므로 `terms`는 곱하지 않음
  - 각 예약의 모든 `order_item` row의 `due_price` 합산 후 `room_cnt` 곱하기
- 예약당시 금액을 정확히 반영
- 예시: 4박 2객실, 1박당 100,000원
  - `order_item` 4개 row (각 100,000원) → 합산 = 400,000원
  - 입금가 = 400,000 × 2(객실수) = 800,000원

### 중복 계산 문제 해결

**문제**:
- `order_item` JOIN으로 row 수 증가 (4박 → 4개 row)
- `terms * room_cnt` 계산이 중복됨
- `order_pay.total_amount`도 중복됨

**해결**:
1. `order_item` JOIN 제거 → 서브쿼리로만 처리
2. `terms * room_cnt`는 `order_product`에서 직접 계산
3. `order_pay`는 직접 JOIN (1:1 관계이므로 중복 없음)

### 쿼리 구조

```sql
FROM order_product op
LEFT JOIN order_pay opay 
    ON op.order_pay_idx = opay.idx
-- order_item JOIN 제거, 서브쿼리로만 처리
WHERE ...
GROUP BY ...
```

## 📚 추가 문서

자세한 가이드는 `docs/` 폴더를 참고하세요:
- `docs/README.md`: 문서 목록
- `docs/GITHUB_UPLOAD_GUIDE.md`: GitHub 업로드 가이드
- `docs/DEPLOYMENT_GUIDE.md`: 서버 배포 가이드
- `docs/SERVER_OPERATION_GUIDE.md`: 서버 운영 가이드

## 📝 라이선스

이 프로젝트는 내부 사용을 위한 것입니다.

## 📞 문의

프로젝트 관련 문의는 GitHub Issues를 통해 등록해주세요.

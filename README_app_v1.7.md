# 채널별 예약 통계 시스템 v1.7

채널별 예약 통계를 실시간으로 조회하고 엑셀로 추출할 수 있는 Streamlit 기반 웹 애플리케이션입니다.

## 📋 개요

이 시스템은 allmytour.com의 채널별 예약 데이터를 조회하고 통계를 제공합니다. 사용자는 날짜 범위와 채널을 선택하여 예약 건수, 입금가, 실구매가, 수익 등의 통계를 확인할 수 있습니다.

## 🎯 주요 기능

### 1. 사용자 인증
- `tblmanager` 테이블 기반 로그인 시스템
- 쿠키 기반 인증 상태 유지 (새로고침 시에도 로그인 유지)
- `user_status = '1'`인 사용자만 접근 가능
- bcrypt, MD5, SHA256, 평문 비밀번호 지원

### 2. 판매유형 선택
- 판매유형 필터 추가 (전체/b2c/b2b)
- '전체' 선택 시 모든 판매유형 조회
- 'b2c' 또는 'b2b' 선택 시 해당 판매유형만 조회
- `product_rateplan` 테이블의 `sale_type` 값 사용

### 3. 채널 선택
- 데이터베이스에서 채널 목록 자동 조회
- multiselect로 여러 채널 선택 가능
- '전체' 선택 시 모든 채널 조회
- 채널 목록 캐싱 (1시간 TTL)

### 4. 날짜 범위 조회
- **날짜유형 선택**: 구매일(예약일) 또는 이용일(체크인) 기준
- **구매일 기준**: 오늘 기준 90일 전 ~ 어제까지 선택 가능 (당일 데이터 조회 불가)
- **이용일 기준**: 오늘 기준 90일 전 ~ 90일 후까지 선택 가능
- 최대 90일(3개월) 조회 기간 제한

### 5. 통계 조회
- **요약 통계** (2행 4컬럼):
  - 1행: 총 예약건수, 총 입금가, 총 실구매가, 총 수익
  - 2행: 총 객실수, 확정 객실 수, 취소 객실 수, 취소율
- **상세 데이터**:
  - 날짜, 채널명, 판매유형, 판매숙소수, 예약건수, 총객실수, 확정객실수, 취소객실수, 취소율
  - 총 입금가, 총 실구매가, 총 수익, 수익률
  - 상위 10개만 화면에 표시 (전체 데이터는 엑셀 다운로드)

### 6. 엑셀 다운로드
- 전체 데이터를 엑셀 파일로 다운로드
- 날짜유형별 시트 자동 생성
- 요약 통계 포함

### 7. 로깅 시스템
- 타입별 로그 파일 분리: `auth.log`, `error.log`, `access.log`, `app.log`
- 30일 보관 정책
- 모든 사용자 액션 로깅

## 🛠️ 기술 스택

- **Frontend**: Streamlit 1.28.0+
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
- `channels`: 채널 마스터 (ID, 채널명 등)

### 6. 애플리케이션 실행

```bash
streamlit run app_v1.7.py --server.port=8501
```

브라우저에서 `http://localhost:8501`로 접속하세요.

**서버 배포 시:**
- 로컬: 포트 8501
- 서버: 포트 8007

## 📖 사용 방법

### 1. 로그인
- `tblmanager` 테이블의 `admin_id`와 `passwd`로 로그인
- `user_status = '1'`인 계정만 접근 가능
- 로그인 상태는 브라우저 쿠키에 저장되어 새로고침 시에도 유지됨

### 2. 검색 조건 설정
1. **날짜유형 선택**: 구매일 또는 이용일 선택
2. **날짜 범위 선택**: 시작일과 종료일 선택
   - 이용일 기준: 오늘 기준 90일 전 ~ 90일 후까지 선택 가능
   - 구매일 기준: 오늘 기준 90일 전 ~ 어제까지 선택 가능
3. **판매유형 선택**: 전체, b2c, b2b 중 선택
   - '전체'를 선택하면 모든 판매유형이 조회됩니다
4. **채널 선택**: 조회할 채널을 선택 (여러 개 선택 가능)
   - '전체'를 선택하면 모든 채널이 조회됩니다

### 3. 조회
- **"조회"** 버튼 클릭하여 데이터 조회
- 결과 화면에 요약 통계와 상세 데이터 표시

### 4. 엑셀 다운로드
- **"엑셀 파일 다운로드"** 버튼으로 전체 데이터 다운로드

### 5. 초기화
- **"초기화"** 버튼으로 모든 필터를 기본값으로 되돌림

## 🗄️ 데이터베이스 구조

### 주요 테이블

- `order_product`: 예약 상품 데이터
  - `idx`: 예약 상품 ID (PK)
  - `create_date`: 구매일(예약일)
  - `checkin_date`: 이용일(체크인)
  - `order_product_status`: 예약상태
  - `order_channel_idx`: 채널 ID
  - `order_pay_idx`: 결제 정보 ID
  - `rateplan_idx`: 요금제 ID (FK → product_rateplan.idx)
  - `terms`: 숙박기간 (박)
  - `room_cnt`: 객실수

- `order_item`: 예약 상세 항목
  - `idx`: 항목 ID (PK)
  - `order_product_idx`: 예약 상품 ID (FK → order_product.idx)
  - `stay_date`: 숙박일
  - `due_price`: 해당 날짜의 입금가

- `order_pay`: 결제 정보
  - `idx`: 결제 ID (PK)
  - `total_amount`: 실구매가

- `common_code`: 채널명 마스터 데이터
  - `code_id`: 채널 ID
  - `code_name`: 채널명
  - `parent_idx`: 부모 코드 ID (1 = 채널)

- `product_rateplan`: 요금제 마스터 데이터
  - `idx`: 요금제 ID (PK)
  - `sale_type`: 판매유형 ('b2c', 'b2b')

- `tblmanager`: 관리자 계정 정보
  - `admin_id`: 관리자 ID (로그인 ID)
  - `passwd`: 비밀번호 (bcrypt 해시)
  - `user_status`: 계정 상태 ('1' = 활성, '0' = 비활성)

### 테이블 관계

```
order_product (1) ──< (N) order_item
    │
    └── (1) ──< (1) order_pay
    │
    └── (N) ──< (1) common_code
    │
    └── (N) ──< (1) product_rateplan
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
  - `logs/` 폴더 (로그 파일에 민감한 정보 포함될 수 있음)

### 보안 기능

- **사용자 인증**: `tblmanager` 테이블 기반 로그인 시스템
- **계정 상태 확인**: `user_status = '1'`인 사용자만 접근 가능
- **비밀번호 해싱**: bcrypt, MD5, SHA256, 평문 순서로 검증 시도
- **세션 관리**: 쿠키 기반 인증 상태 유지 (1일 유효)
- **로깅**: 모든 인증 시도와 접근 기록 저장

## 📝 로깅 시스템

### 로그 파일 구조
- `logs/auth.log`: 인증 관련 로그 (로그인, 로그아웃, 인증 실패)
- `logs/error.log`: 에러 로그 (예외, SQL 오류)
- `logs/access.log`: 접근 로그 (페이지 접근, 쿼리 실행)
- `logs/app.log`: 일반 애플리케이션 로그

### 로깅 정책
- 일별 로그 파일 로테이션
- 30일 보관 후 자동 삭제
- 5초 이상 실행된 쿼리 자동 로깅

## 🚀 버전 히스토리

### v1.7 (현재 버전)
- ✨ **판매유형 필터 기능 추가**
  - 판매유형 선택 필터 추가 (전체/b2c/b2b)
  - `product_rateplan` 테이블과 조인하여 `sale_type` 값 사용
  - 상세 데이터에 '판매유형' 컬럼 추가 (채널명 다음 위치)
  - 엑셀 다운로드에도 '판매유형' 컬럼 포함
  - '채널선택' 위에 '판매유형선택' 셀렉트박스 배치
- 🔄 **v1.6 기반**
  - 채널별 예약 통계 시스템
  - 인증 기능 및 로깅 시스템 포함

### v1.6
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
  - 로딩 표시 개선: `st.spinner` 사용
  - 로그인 실패 시 빨간색 경고 메시지 표시
  - 로그인 페이지와 메인 페이지 분리
  - 헤더에 로그아웃 버튼 추가
- 🔄 **세션 관리 개선**
  - 세션 타임아웃 제거
  - 쿠키 기반 인증 복원으로 브라우저 새로고침 시에도 로그인 상태 유지

### v1.5
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

## 📚 추가 문서

자세한 가이드는 `docs/` 폴더를 참고하세요:
- `docs/# 채널별 예약 통계 시스템.md`: 채널별 통계 시스템 상세 문서

## 📞 문의

프로젝트 관련 문의는 GitHub Issues를 통해 등록해주세요.


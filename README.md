# 채널별 예약 통계 시스템 v1.2

allmytour.com의 다양한 예약 채널별 통계를 실시간으로 조회하고 엑셀로 추출할 수 있는 백오피스 시스템입니다.

## 🎯 주요 기능

- 📊 **날짜별/채널별 예약 데이터 조회**
  - 구매일(예약일) 또는 이용일(체크인) 기준 조회
  - 확정/취소 예약상태 필터링
  - 다중 채널 선택 지원
- 📈 **요약 통계 대시보드**
  - 총 예약건수, 총 객실수, 총 입금가, 총 실구매가, 총 수익
  - 실시간 집계 및 계산
- 📋 **상세 데이터 조회**
  - 판매숙소수, 예약건수, 총객실수, 총 입금가, 총 실구매가, 총 수익, 수익률
  - 상위 10개 미리보기 (전체 데이터는 엑셀 다운로드)
- 📥 **원클릭 엑셀 다운로드**
  - 날짜유형별 시트 자동 생성 (구매일/이용일)
  - 요약 통계 포함
- 🔄 **검색 조건 유지**
  - 검색 조건 변경 시 결과 화면 유지
  - 조회 버튼 클릭 시에만 새로 조회

## 🚀 버전 히스토리

### v1.2 (현재 버전)
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
# v1.2 실행
streamlit run app_v1.2.py

# 또는 v1.1 실행
streamlit run app_v1.1.py

# 또는 v1.0 실행
streamlit run app.py
```

브라우저에서 `http://localhost:8501`로 접속하세요.

## 📁 프로젝트 구조

```
통계프로그램/
├── app.py                 # Streamlit 메인 애플리케이션 (v1.0)
├── app_v1.1.py           # v1.1 버전
├── app_v1.2.py           # v1.2 버전 (현재)
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
│   ├── query_builder.py  # SQL 쿼리 빌더 (v1.0)
│   ├── query_builder_v1.1.py # v1.1 버전
│   ├── query_builder_v1.2.py # v1.2 버전
│   ├── excel_handler.py   # 엑셀 다운로드 처리 (v1.0)
│   └── excel_handler_v1.2.py # v1.2 버전
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
2. 사이드바에서 검색 조건 설정:
   - **날짜유형**: 구매일 또는 이용일 선택
   - **시작일 및 종료일** 선택 (최대 90일)
   - **조회할 채널** 선택 (멀티셀렉트)
   - **예약상태**: 전체, 확정, 취소 선택
3. **"조회"** 버튼 클릭
4. 결과 확인:
   - 요약 통계 확인
   - 상세 데이터 상위 10개 미리보기
5. **엑셀 다운로드** 버튼으로 전체 데이터 다운로드

## 🗄️ 데이터베이스 구조

### 주요 테이블

- `order_product`: 예약 상품 데이터
  - `create_date`: 구매일(예약일)
  - `checkin_date`: 이용일(체크인)
  - `order_product_status`: 예약상태
  - `order_channel_idx`: 채널 ID
  - `order_pay_idx`: 결제 정보 ID
  - `product_name`: 숙소명
  - `room_cnt`: 객실수
  - `original_amount`: 입금가
- `order_pay`: 결제 정보
  - `idx`: 결제 ID (order_product.order_pay_idx와 연결)
  - `total_amount`: 실구매가
- `common_code`: 채널명 마스터 데이터

## 🔒 보안 주의사항

- ⚠️ **절대 커밋하지 마세요**:
  - `.env` 파일 (데이터베이스 접속 정보)
  - `master_data.xlsx` (민감한 데이터)
  - `env.py` (하드코딩된 접속 정보 포함)
  - `venv/` 폴더

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

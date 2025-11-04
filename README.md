# 채널별 예약 통계 시스템

allmytour.com의 다양한 예약 채널별 통계를 실시간으로 조회하고 엑셀로 추출할 수 있는 백오피스 시스템입니다.

## 주요 기능

- 📊 날짜별/채널별 예약 데이터 조회
- 📈 요약 통계 및 일별 추세 분석
- 📥 원클릭 엑셀 다운로드
- 🔍 동적 채널 목록 로드
- 🔄 통합 쿼리를 통한 다중 테이블 데이터 조회

## 기술 스택

- **Frontend**: Streamlit
- **Backend**: Python 3.12+
- **Database**: MySQL (SQLAlchemy)
- **Data Processing**: Pandas
- **Excel Export**: openpyxl

## 설치 방법

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

### 5. 애플리케이션 실행

```bash
streamlit run app.py
```

브라우저에서 `http://localhost:8501`로 접속하세요.

## 프로젝트 구조

```
통계프로그램/
├── app.py                 # Streamlit 메인 애플리케이션
├── config/
│   ├── channels.py        # 채널 설정 및 매핑
│   ├── channel_mapping.py # master_data.xlsx 매핑 로더
│   └── configdb.py        # 데이터베이스 연결 설정
├── utils/
│   ├── data_fetcher.py   # 데이터 조회 함수
│   ├── query_builder.py  # SQL 쿼리 빌더
│   └── excel_handler.py   # 엑셀 다운로드 처리
├── requirements.txt      # 패키지 의존성
├── .env.example          # 환경 변수 템플릿
└── README.md             # 프로젝트 문서
```

## 사용 방법

1. 웹 브라우저에서 애플리케이션 접속
2. 사이드바에서 검색 조건 설정:
   - 시작일 및 종료일 선택
   - 조회할 채널 선택 (멀티셀렉트)
3. "조회" 버튼 클릭
4. 결과 확인 및 엑셀 다운로드

## 데이터베이스 구조

### 주요 테이블

- `order_product`: Expedia, Hotelbeds, 다보, 누아 등 채널 데이터
- `booking_master_offer`: Trip, Meituan, Fliggy, Agoda 등 중국계 채널 데이터
- `common_code`: 채널명 마스터 데이터

## 보안 주의사항

- ⚠️ **절대 커밋하지 마세요**:
  - `.env` 파일 (데이터베이스 접속 정보)
  - `master_data.xlsx` (민감한 데이터)
  - `env.py` (하드코딩된 접속 정보 포함)

## 라이선스

이 프로젝트는 내부 사용을 위한 것입니다.

## 문의

프로젝트 관련 문의는 GitHub Issues를 통해 등록해주세요.


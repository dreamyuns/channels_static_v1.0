#!/bin/bash
# 배포 스크립트
# 사용법: ./deploy.sh

set -e  # 에러 발생 시 스크립트 중단

echo "🚀 채널별 예약 통계 시스템 배포 시작..."

# 변수 설정
PROJECT_DIR="$HOME/projects/channels_statistics"
REPO_URL="https://github.com/dreamyuns/channels_static_v1.0.git"

# 프로젝트 디렉토리 생성
if [ ! -d "$PROJECT_DIR" ]; then
    echo "📁 프로젝트 디렉토리 생성 중..."
    mkdir -p "$PROJECT_DIR"
fi

cd "$PROJECT_DIR"

# Git 저장소 클론 또는 업데이트
if [ -d ".git" ]; then
    echo "🔄 코드 업데이트 중..."
    git pull origin main
else
    echo "📥 코드 다운로드 중..."
    git clone "$REPO_URL" .
fi

# 가상환경 생성
if [ ! -d "venv" ]; then
    echo "🐍 가상환경 생성 중..."
    python3 -m venv venv
fi

# 가상환경 활성화 및 패키지 설치
echo "📦 패키지 설치 중..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# .env 파일 확인
if [ ! -f ".env" ]; then
    echo "⚠️  .env 파일이 없습니다!"
    echo "env.example을 참고하여 .env 파일을 생성하세요."
    exit 1
fi

# master_data.xlsx 파일 확인
if [ ! -f "master_data.xlsx" ]; then
    echo "⚠️  master_data.xlsx 파일이 없습니다!"
    echo "이 파일을 서버에 업로드해야 합니다."
fi

echo "✅ 배포 준비 완료!"
echo ""
echo "다음 명령어로 애플리케이션을 실행하세요:"
echo "  cd $PROJECT_DIR"
echo "  source venv/bin/activate"
echo "  streamlit run app.py --server.port 8501 --server.address 0.0.0.0"
echo ""
echo "또는 systemd 서비스를 사용하세요:"
echo "  sudo systemctl restart channels-statistics"


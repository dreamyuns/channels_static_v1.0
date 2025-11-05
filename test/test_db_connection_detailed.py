#!/usr/bin/env python3
"""DB 서버 연결 상세 진단 스크립트"""

import socket
import errno
import os

host = '118.67.130.132'
port = 3306
timeout = 10

print(f"🔍 DB 서버 연결 상세 진단: {host}:{port}")
print("=" * 60)

# 1. 현재 서버 IP 확인
print("\n[1] 현재 서버 정보:")
try:
    import subprocess
    result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
    local_ips = result.stdout.strip().split()
    print(f"   로컬 IP: {', '.join(local_ips) if local_ips else '확인 불가'}")
except:
    pass

# 2. 에러 코드 매핑 확인
print("\n[2] 에러 코드 매핑:")
error_codes = {
    errno.ECONNREFUSED: "ECONNREFUSED (연결 거부 - 서버가 포트를 리스닝하지 않거나 거부)",
    errno.ETIMEDOUT: "ETIMEDOUT (연결 타임아웃 - 방화벽 차단 가능성)",
    errno.EHOSTUNREACH: "EHOSTUNREACH (호스트에 도달할 수 없음)",
    errno.ENETUNREACH: "ENETUNREACH (네트워크에 도달할 수 없음)",
    errno.EAGAIN: "EAGAIN (리소스 일시적으로 사용 불가)",
    errno.EINPROGRESS: "EINPROGRESS (연결 진행 중)",
}

print(f"   errno.ECONNREFUSED = {errno.ECONNREFUSED}")
print(f"   errno.ETIMEDOUT = {errno.ETIMEDOUT}")
print(f"   errno.EAGAIN = {errno.EAGAIN}")
print(f"   errno.EINPROGRESS = {errno.EINPROGRESS}")

# 3. 실제 연결 테스트
print(f"\n[3] 포트 {port} 연결 테스트:")
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    result = sock.connect_ex((host, port))
    
    print(f"   connect_ex() 반환값: {result}")
    
    if result == 0:
        print(f"   ✅ 포트 {port} 연결 성공!")
        print("   → TCP 연결은 정상입니다.")
        sock.close()
    else:
        # 에러 코드 해석
        error_msg = error_codes.get(result, f"알 수 없는 에러 코드: {result}")
        print(f"   ❌ 포트 {port} 연결 실패!")
        print(f"   원인: {error_msg}")
        
        # 추가 정보
        if result == errno.ETIMEDOUT:
            print("\n   💡 해결 방법:")
            print("      - DB 서버 방화벽에서 라이브 서버 IP 허용 필요")
            print("      - DB 관리자에게 요청: '라이브 서버에서 접근 가능하도록 설정'")
        elif result == errno.ECONNREFUSED:
            print("\n   💡 해결 방법:")
            print("      - MySQL이 외부 접근을 허용하지 않음")
            print("      - MySQL bind-address 설정 확인 필요")
        elif result == 11:  # 에러 코드 11
            print("\n   💡 에러 코드 11 분석:")
            print("      - Linux에서 errno 11은 보통 EAGAIN")
            print("      - 하지만 네트워크 연결에서는 드뭅니다")
            print("      - 실제로는 타임아웃이나 방화벽 차단일 가능성이 높음")
            print("      - DB 서버 방화벽 설정 확인 필요")
        
        sock.close()
        
except socket.timeout:
    print(f"   ❌ 연결 타임아웃 ({timeout}초)")
    print("   → DB 서버 방화벽에서 이 IP를 허용하지 않거나")
    print("   → 네트워크 경로 문제일 수 있습니다")
    
except Exception as e:
    print(f"   ❌ 예기치 않은 오류: {e}")
    import traceback
    traceback.print_exc()

# 4. 추가 테스트 - nc 명령어 결과 확인
print("\n[4] 추가 확인 사항:")
print("   아래 명령어로도 테스트해보세요:")
print(f"   timeout 10 nc -zv {host} {port}")

print("\n" + "=" * 60)
print("📋 요약:")
print("   현재 상황: DB 서버로의 TCP 연결이 실패하고 있습니다.")
print("   가장 가능성 높은 원인: DB 서버 방화벽에서 라이브 서버 IP를 차단")
print("\n   📞 DB 관리자에게 요청할 내용:")
print("   1. 라이브 서버 IP: 211.188.59.125")
print("   2. DB 서버 IP: 118.67.130.132")
print("   3. 포트: 3306")
print("   4. 요청: '라이브 서버에서 DB 서버로 접근 가능하도록 방화벽 설정'")


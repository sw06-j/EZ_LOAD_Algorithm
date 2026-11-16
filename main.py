"""
main.py
-------
EZ_LOAD_Algorithm 실행 진입점.

- test: 알고리즘 단위 테스트 실행
- demo: 실제 서울 강남 테헤란로 도로망 기반 '쉬운 길' vs '빠른 길' 라우팅 데모 실행
"""

import sys
from osm_adapter import run_gangnam_real_test
from test_ez_router import (
    test_basic,
    test_highway_preference,
    test_personalized_hard_factor,
)


def main():
    print("=" * 60)
    print("🚗 EZ_LOAD_Algorithm: 초보 운전자 맞춤형 쉬운 길 라우팅 엔진")
    print("=" * 60)
    print("\n[1단계] 단위 테스트 검증 실행...")
    test_basic()
    test_personalized_hard_factor()
    test_highway_preference()
    print(">> 모든 단위 테스트 PASS 완료!\n")

    print("[2단계] 실제 서울 강남 도로망(OSM) 기반 라우팅 데모 실행...")
    run_gangnam_real_test()


if __name__ == "__main__":
    main()

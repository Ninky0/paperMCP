#!/usr/bin/env python3
"""
서버 API 테스트 스크립트
"""

import requests
import json

def test_search():
    """논문 검색 테스트"""
    server_url = "http://localhost:8001"
    
    print("🔍 논문 검색 테스트 시작...")
    
    try:
        # 서버 상태 확인
        response = requests.get(f"{server_url}/")
        print(f"서버 상태: {response.status_code}")
        print(f"응답: {response.json()}")
        print()
        
        # 논문 검색 테스트
        search_data = {
            "query": "machine learning",
            "max_results": 5,
            "source": "arxiv"
        }
        
        print(f"검색 요청: {search_data}")
        response = requests.post(f"{server_url}/search_papers", json=search_data)
        
        print(f"검색 응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            papers = response.json()
            print(f"수집된 논문 수: {len(papers)}")
            
            if papers:
                print("📄 수집된 논문 목록:")
                for i, paper in enumerate(papers[:3], 1):  # 상위 3개만 출력
                    print(f"  {i}. {paper['title']}")
                    print(f"     저자: {', '.join(paper['authors'][:3])}")
                    print(f"     URL: {paper['url']}")
                    print(f"     소스: {paper['source']}")
                    print()
            else:
                print("❌ 수집된 논문이 없습니다.")
        else:
            print(f"❌ 검색 실패: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    test_search() 
#!/usr/bin/env python3
"""
기존 수집된 논문들의 PDF 다운로드 테스트
"""

import requests
import time

def test_download_existing_papers():
    """기존 논문들의 PDF 다운로드 테스트"""
    print("📥 기존 논문들의 PDF 다운로드 테스트...")
    
    try:
        # 저장된 논문 목록 가져오기
        response = requests.get("http://localhost:8001/papers?limit=5")
        
        if response.status_code == 200:
            papers = response.json()
            print(f"📁 저장된 논문: {len(papers)}개")
            
            downloaded_count = 0
            
            for i, paper in enumerate(papers, 1):
                print(f"\n{i}. {paper['title'][:60]}...")
                print(f"   URL: {paper['url']}")
                
                if paper.get('pdf_url'):
                    print(f"   📥 PDF 다운로드 시도...")
                    
                    try:
                        download_response = requests.post("http://localhost:8001/download_paper", 
                                                        params={"paper_url": paper['url']}, timeout=60)
                        
                        if download_response.status_code == 200:
                            result = download_response.json()
                            if result.get('success'):
                                print(f"   ✅ 다운로드 완료: {result.get('filename', 'N/A')}")
                                downloaded_count += 1
                            else:
                                print(f"   ❌ 다운로드 실패: {result.get('error', 'Unknown error')}")
                        else:
                            print(f"   ❌ 다운로드 요청 실패: {download_response.status_code}")
                            print(f"   응답: {download_response.text}")
                            
                    except Exception as e:
                        print(f"   ❌ 다운로드 오류: {e}")
                else:
                    print(f"   ⚠️ PDF URL 없음")
                
                # 다운로드 간 지연
                time.sleep(2)
            
            print(f"\n🎉 다운로드 테스트 완료!")
            print(f"📥 성공한 다운로드: {downloaded_count}개")
            
        else:
            print(f"❌ 논문 목록 조회 실패: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 오류: {e}")

if __name__ == "__main__":
    test_download_existing_papers() 
#!/usr/bin/env python3
"""
arXiv 수집기 직접 테스트
"""

import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tools.arxiv_collector import ArxivCollector

async def test_arxiv():
    """arXiv 수집기 테스트"""
    print("🔍 arXiv 수집기 테스트 시작...")
    
    collector = ArxivCollector()
    
    try:
        # 간단한 검색 테스트
        print("'machine learning' 키워드로 검색 중...")
        papers = await collector.search("machine learning", 5)
        
        print(f"수집된 논문 수: {len(papers)}")
        
        if papers:
            print("📄 수집된 논문 목록:")
            for i, paper in enumerate(papers[:3], 1):
                print(f"  {i}. {paper['title']}")
                print(f"     저자: {', '.join(paper['authors'][:3])}")
                print(f"     URL: {paper['url']}")
                print(f"     PDF URL: {paper.get('pdf_url', 'N/A')}")
                print()
        else:
            print("❌ 수집된 논문이 없습니다.")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_arxiv()) 
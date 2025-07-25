#!/usr/bin/env python3
"""
데이터베이스 내용 확인 스크립트
"""

import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from database.paper_db import PaperDatabase

async def check_database():
    """데이터베이스 내용 확인"""
    print("🔍 데이터베이스 내용 확인...")
    
    db = PaperDatabase()
    
    try:
        # 전체 논문 수 확인
        papers = await db.get_papers(limit=1000)
        print(f"총 저장된 논문 수: {len(papers)}")
        
        if papers:
            print("\n📄 최근 저장된 논문들:")
            for i, paper in enumerate(papers[:5], 1):
                print(f"  {i}. {paper['title']}")
                print(f"     URL: {paper['url']}")
                print(f"     소스: {paper['source']}")
                print(f"     저장일: {paper['created_at']}")
                print()
            
            # 소스별 통계
            source_stats = {}
            for paper in papers:
                source = paper['source']
                source_stats[source] = source_stats.get(source, 0) + 1
            
            print("📊 소스별 통계:")
            for source, count in source_stats.items():
                print(f"  {source}: {count}개")
        else:
            print("❌ 데이터베이스에 논문이 없습니다.")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_database()) 
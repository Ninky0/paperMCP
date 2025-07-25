#!/usr/bin/env python3
"""
간단한 논문 수집 스크립트
즉시 논문을 검색하고 PDF를 다운로드합니다.
"""

import requests
import json
import time
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def collect_papers():
    """논문 수집 및 PDF 다운로드"""
    from datetime import datetime
    from pathlib import Path
    
    # 실행 시간 기준 폴더 생성
    current_time = datetime.now()
    time_folder = current_time.strftime('%Y%m%d_%H%M%S')
    
    # 시간별 폴더 생성
    papers_dir = Path("papers")
    time_papers_dir = papers_dir / time_folder
    time_papers_dir.mkdir(parents=True, exist_ok=True)
    
    server_url = "http://localhost:8001"
    session = requests.Session()
    
    logging.info(f"📁 저장 폴더: {time_folder}")
    logging.info(f"📂 폴더 생성 완료: {time_papers_dir}")
    
    # 키워드별 소스 설정
    keyword_sources = {
        # 🧬 생명과학/의학 (PubMed + arXiv)
        "cancer research": "all",
        "drug discovery": "all", 
        "genomics": "all",
        "neuroscience": "all",
        
        # 🌍 지구과학/환경 (PubMed + arXiv)
        "geology": "all",
        "climate change": "all",
        "environmental science": "all",
        
        # 🔬 물리학/화학 (arXiv 위주)
        "quantum physics": "arxiv",
        "astrophysics": "arxiv",
        "biochemistry": "all",
        
        # 📐 수학 (arXiv 위주)
        "mathematical analysis": "arxiv",
        "statistics": "all",
        "optimization": "arxiv",
        
        # ⚡ 전기/전자공학 (arXiv 위주)
        "electrical engineering": "arxiv",
        "robotics": "arxiv",
        "semiconductor physics": "arxiv",
        
        # 🎨 예술/디자인 (arXiv 위주)
        "computer graphics": "arxiv",
        "virtual reality": "arxiv",
        "human-computer interaction": "arxiv",
        
        # 🏗️ 건축/토목 (arXiv 위주)
        "architecture": "arxiv",
        "civil engineering": "arxiv",
        "structural engineering": "arxiv",
        
        # 💰 경제/금융 (arXiv 위주)
        "financial economics": "arxiv",
        "behavioral economics": "arxiv",
        "risk management": "arxiv",
        
        # 🧠 심리학/사회학 (PubMed + arXiv)
        "cognitive psychology": "all",
        "social psychology": "all",
        "sociology": "all",
        
        # 📚 교육/언어학 (arXiv 위주)
        "educational technology": "arxiv",
        "linguistics": "arxiv",
        "cognitive science": "arxiv",
        
        # 🏥 의료기기/바이오메디컬 (PubMed + arXiv)
        "biomedical engineering": "all",
        "medical devices": "all",
        "bioinformatics": "all",
        
        # 🌱 농업/식품과학 (PubMed + arXiv)
        "agricultural science": "all",
        "food science": "all",
        "plant biology": "all",
        
        # 🔒 보안/사이버보안 (arXiv 위주)
        "cybersecurity": "arxiv",
        "cryptography": "arxiv",
        "network security": "arxiv"
    }
    
    total_collected = 0
    total_downloaded = 0
    
    logging.info("=" * 60)
    logging.info("간단한 논문 수집 시작")
    logging.info("=" * 60)
    
    for i, (keyword, source) in enumerate(keyword_sources.items(), 1):
        logging.info(f"진행률: {i}/{len(keyword_sources)} - '{keyword}' 처리 중... (소스: {source})")
        
        try:
            # 논문 검색
            response = session.post(f"{server_url}/search_papers", json={
                "query": keyword,
                "max_results": 8,  # 각 키워드당 8개씩
                "source": source  # 키워드별 소스 설정
            }, timeout=60)
            
            if response.status_code == 200:
                papers = response.json()
                logging.info(f"'{keyword}': {len(papers)}개 논문 수집")
                total_collected += len(papers)
                
                # PDF 다운로드
                downloaded_count = 0
                for paper in papers:
                    if paper.get('pdf_url'):
                        try:
                            download_response = session.post(f"{server_url}/download_paper", 
                                                           params={"paper_url": paper['url'], "time_folder": time_folder}, timeout=60)
                            
                            if download_response.status_code == 200:
                                result = download_response.json()
                                if result.get('success'):
                                    logging.info(f"  📥 다운로드 완료: {result.get('filename', 'N/A')}")
                                    downloaded_count += 1
                                    total_downloaded += 1
                                else:
                                    error_msg = result.get('error', 'Unknown error')
                                    if 'too long' in error_msg.lower():
                                        logging.info(f"  ⏭️ 페이지 수 초과로 건너뜀: {error_msg}")
                                    else:
                                        logging.warning(f"  ❌ 다운로드 실패: {error_msg}")
                            
                        except Exception as e:
                            logging.warning(f"  ❌ 다운로드 오류: {e}")
                    
                    # 다운로드 간 지연
                    time.sleep(1)
                
                logging.info(f"'{keyword}': {downloaded_count}개 PDF 다운로드 완료")
                
            else:
                logging.error(f"'{keyword}' 검색 실패: {response.status_code}")
            
            # 키워드 간 지연
            if i < len(keyword_sources):
                time.sleep(2)
                
        except Exception as e:
            logging.error(f"'{keyword}' 처리 중 오류: {e}")
    
    logging.info("=" * 60)
    logging.info(f"수집 완료: 총 {total_collected}개 논문 수집, {total_downloaded}개 PDF 다운로드")
    logging.info(f"📁 저장 위치: {time_papers_dir}")
    logging.info("=" * 60)

if __name__ == "__main__":
    collect_papers() 
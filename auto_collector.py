#!/usr/bin/env python3
"""
자동 논문 수집 스크립트
매일 지정된 키워드로 논문을 자동 수집합니다.
"""

import requests
import json
import time
import schedule
from datetime import datetime, timedelta
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_collector.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class AutoPaperCollector:
    def __init__(self, server_url="http://localhost:8001"):
        self.server_url = server_url
        self.session = requests.Session()
        
        # 수집할 키워드와 설정 (다양한 학문 분야)
        self.keywords = [
            # 🧠 인공지능/컴퓨터 과학
            "machine learning",
            "deep learning", 
            "artificial intelligence",
            "neural networks",
            "computer vision",
            "natural language processing",
            "large language models",
            "transformer models",
            
            # 🧬 생명과학/의학
            "cancer research",
            "drug discovery",
            "genomics",
            "proteomics",
            "immunology",
            "neuroscience",
            "microbiology",
            "biotechnology",
            "medical imaging",
            "clinical trials",
            "epidemiology",
            "pharmacology",
            
            # 🐾 동물학/생태학
            "animal behavior",
            "wildlife conservation",
            "marine biology",
            "evolutionary biology",
            "ecology",
            "biodiversity",
            "zoology",
            "ornithology",
            
            # 🌍 지구과학/환경
            "geology",
            "climate change",
            "atmospheric science",
            "oceanography",
            "seismology",
            "volcanology",
            "environmental science",
            "sustainability",
            "renewable energy",
            
            # 🔬 물리학/화학
            "quantum physics",
            "particle physics",
            "astrophysics",
            "condensed matter physics",
            "nuclear physics",
            "physical chemistry",
            "organic chemistry",
            "inorganic chemistry",
            "biochemistry",
            "materials science",
            
            # 📐 수학
            "mathematical analysis",
            "algebra",
            "geometry",
            "topology",
            "number theory",
            "statistics",
            "probability theory",
            "optimization",
            "differential equations",
            
            # ⚡ 전기/전자공학
            "electrical engineering",
            "electronics",
            "semiconductor physics",
            "power systems",
            "control systems",
            "signal processing",
            "telecommunications",
            "robotics",
            
            # 🎨 예술/디자인
            "digital art",
            "computer graphics",
            "human-computer interaction",
            "user interface design",
            "creative computing",
            "generative art",
            "virtual reality",
            "augmented reality",
            
            # 🏗️ 건축/토목
            "architecture",
            "structural engineering",
            "civil engineering",
            "construction materials",
            "urban planning",
            "transportation engineering",
            "environmental engineering",
            
            # 💰 경제/금융
            "financial economics",
            "behavioral economics",
            "financial modeling",
            "risk management",
            "investment analysis",
            "market research",
            "economic forecasting",
            
            # 🧠 심리학/사회학
            "cognitive psychology",
            "social psychology",
            "developmental psychology",
            "clinical psychology",
            "sociology",
            "anthropology",
            "political science",
            
            # 📚 교육/언어학
            "educational technology",
            "language learning",
            "linguistics",
            "cognitive science",
            "pedagogy",
            "curriculum design",
            
            # 🏥 의료기기/바이오메디컬
            "biomedical engineering",
            "medical devices",
            "tissue engineering",
            "biomechanics",
            "bioinformatics",
            "precision medicine",
            
            # 🌱 농업/식품과학
            "agricultural science",
            "food science",
            "plant biology",
            "soil science",
            "agricultural technology",
            "food safety",
            
            # 🔒 보안/사이버보안
            "cybersecurity",
            "cryptography",
            "network security",
            "information security",
            "privacy protection",
            "digital forensics"
        ]
        
        # 각 키워드별 설정 (균형잡힌 수집)
        self.keyword_configs = {
            # 🧠 인공지능/컴퓨터 과학 (중간 수집)
            "machine learning": {"max_results": 10, "source": "arxiv"},
            "deep learning": {"max_results": 10, "source": "arxiv"},
            "artificial intelligence": {"max_results": 8, "source": "all"},
            "neural networks": {"max_results": 8, "source": "arxiv"},
            "computer vision": {"max_results": 8, "source": "arxiv"},
            "natural language processing": {"max_results": 8, "source": "arxiv"},
            "large language models": {"max_results": 8, "source": "arxiv"},
            "transformer models": {"max_results": 6, "source": "arxiv"},
            
            # 🧬 생명과학/의학 (많이 수집)
            "cancer research": {"max_results": 12, "source": "all"},
            "drug discovery": {"max_results": 10, "source": "all"},
            "genomics": {"max_results": 10, "source": "all"},
            "proteomics": {"max_results": 8, "source": "all"},
            "immunology": {"max_results": 8, "source": "all"},
            "neuroscience": {"max_results": 10, "source": "all"},
            "microbiology": {"max_results": 8, "source": "all"},
            "biotechnology": {"max_results": 8, "source": "all"},
            "medical imaging": {"max_results": 8, "source": "all"},
            "clinical trials": {"max_results": 6, "source": "all"},
            "epidemiology": {"max_results": 8, "source": "all"},
            "pharmacology": {"max_results": 8, "source": "all"},
            
            # 🐾 동물학/생태학 (적당히 수집)
            "animal behavior": {"max_results": 6, "source": "all"},
            "wildlife conservation": {"max_results": 6, "source": "all"},
            "marine biology": {"max_results": 6, "source": "all"},
            "evolutionary biology": {"max_results": 6, "source": "all"},
            "ecology": {"max_results": 6, "source": "all"},
            "biodiversity": {"max_results": 6, "source": "all"},
            "zoology": {"max_results": 5, "source": "all"},
            "ornithology": {"max_results": 5, "source": "all"},
            
            # 🌍 지구과학/환경 (적당히 수집)
            "geology": {"max_results": 8, "source": "all"},
            "climate change": {"max_results": 8, "source": "all"},
            "atmospheric science": {"max_results": 6, "source": "all"},
            "oceanography": {"max_results": 6, "source": "all"},
            "seismology": {"max_results": 5, "source": "all"},
            "volcanology": {"max_results": 5, "source": "all"},
            "environmental science": {"max_results": 8, "source": "all"},
            "sustainability": {"max_results": 6, "source": "all"},
            "renewable energy": {"max_results": 6, "source": "all"},
            
            # 🔬 물리학/화학 (많이 수집)
            "quantum physics": {"max_results": 10, "source": "arxiv"},
            "particle physics": {"max_results": 8, "source": "arxiv"},
            "astrophysics": {"max_results": 8, "source": "arxiv"},
            "condensed matter physics": {"max_results": 8, "source": "arxiv"},
            "nuclear physics": {"max_results": 6, "source": "arxiv"},
            "physical chemistry": {"max_results": 8, "source": "all"},
            "organic chemistry": {"max_results": 8, "source": "all"},
            "inorganic chemistry": {"max_results": 6, "source": "all"},
            "biochemistry": {"max_results": 8, "source": "all"},
            "materials science": {"max_results": 8, "source": "all"},
            
            # 📐 수학 (적당히 수집)
            "mathematical analysis": {"max_results": 8, "source": "arxiv"},
            "algebra": {"max_results": 6, "source": "arxiv"},
            "geometry": {"max_results": 6, "source": "arxiv"},
            "topology": {"max_results": 6, "source": "arxiv"},
            "number theory": {"max_results": 6, "source": "arxiv"},
            "statistics": {"max_results": 8, "source": "arxiv"},
            "probability theory": {"max_results": 6, "source": "arxiv"},
            "optimization": {"max_results": 6, "source": "arxiv"},
            "differential equations": {"max_results": 6, "source": "arxiv"},
            
            # ⚡ 전기/전자공학 (적당히 수집)
            "electrical engineering": {"max_results": 8, "source": "arxiv"},
            "electronics": {"max_results": 8, "source": "arxiv"},
            "semiconductor physics": {"max_results": 6, "source": "arxiv"},
            "power systems": {"max_results": 6, "source": "arxiv"},
            "control systems": {"max_results": 6, "source": "arxiv"},
            "signal processing": {"max_results": 6, "source": "arxiv"},
            "telecommunications": {"max_results": 6, "source": "arxiv"},
            "robotics": {"max_results": 8, "source": "arxiv"},
            
            # 🎨 예술/디자인 (적당히 수집)
            "digital art": {"max_results": 5, "source": "arxiv"},
            "computer graphics": {"max_results": 6, "source": "arxiv"},
            "human-computer interaction": {"max_results": 6, "source": "arxiv"},
            "user interface design": {"max_results": 5, "source": "arxiv"},
            "creative computing": {"max_results": 5, "source": "arxiv"},
            "generative art": {"max_results": 5, "source": "arxiv"},
            "virtual reality": {"max_results": 6, "source": "arxiv"},
            "augmented reality": {"max_results": 6, "source": "arxiv"},
            
            # 🏗️ 건축/토목 (적당히 수집)
            "architecture": {"max_results": 6, "source": "arxiv"},
            "structural engineering": {"max_results": 6, "source": "arxiv"},
            "civil engineering": {"max_results": 6, "source": "arxiv"},
            "construction materials": {"max_results": 5, "source": "arxiv"},
            "urban planning": {"max_results": 5, "source": "arxiv"},
            "transportation engineering": {"max_results": 5, "source": "arxiv"},
            "environmental engineering": {"max_results": 6, "source": "arxiv"},
            
            # 💰 경제/금융 (적당히 수집)
            "financial economics": {"max_results": 6, "source": "arxiv"},
            "behavioral economics": {"max_results": 6, "source": "arxiv"},
            "financial modeling": {"max_results": 6, "source": "arxiv"},
            "risk management": {"max_results": 5, "source": "arxiv"},
            "investment analysis": {"max_results": 5, "source": "arxiv"},
            "market research": {"max_results": 5, "source": "arxiv"},
            "economic forecasting": {"max_results": 5, "source": "arxiv"},
            
            # 🧠 심리학/사회학 (적당히 수집)
            "cognitive psychology": {"max_results": 6, "source": "arxiv"},
            "social psychology": {"max_results": 6, "source": "arxiv"},
            "developmental psychology": {"max_results": 5, "source": "arxiv"},
            "clinical psychology": {"max_results": 6, "source": "arxiv"},
            "sociology": {"max_results": 6, "source": "arxiv"},
            "anthropology": {"max_results": 5, "source": "arxiv"},
            "political science": {"max_results": 5, "source": "arxiv"},
            
            # 📚 교육/언어학 (적당히 수집)
            "educational technology": {"max_results": 6, "source": "arxiv"},
            "language learning": {"max_results": 5, "source": "arxiv"},
            "linguistics": {"max_results": 6, "source": "arxiv"},
            "cognitive science": {"max_results": 6, "source": "arxiv"},
            "pedagogy": {"max_results": 5, "source": "arxiv"},
            "curriculum design": {"max_results": 5, "source": "arxiv"},
            
            # 🏥 의료기기/바이오메디컬 (적당히 수집)
            "biomedical engineering": {"max_results": 8, "source": "arxiv"},
            "medical devices": {"max_results": 6, "source": "arxiv"},
            "tissue engineering": {"max_results": 6, "source": "arxiv"},
            "biomechanics": {"max_results": 6, "source": "arxiv"},
            "bioinformatics": {"max_results": 8, "source": "arxiv"},
            "precision medicine": {"max_results": 6, "source": "arxiv"},
            
            # 🌱 농업/식품과학 (적당히 수집)
            "agricultural science": {"max_results": 6, "source": "arxiv"},
            "food science": {"max_results": 6, "source": "arxiv"},
            "plant biology": {"max_results": 6, "source": "arxiv"},
            "soil science": {"max_results": 5, "source": "arxiv"},
            "agricultural technology": {"max_results": 5, "source": "arxiv"},
            "food safety": {"max_results": 5, "source": "arxiv"},
            
            # 🔒 보안/사이버보안 (적당히 수집)
            "cybersecurity": {"max_results": 6, "source": "arxiv"},
            "cryptography": {"max_results": 6, "source": "arxiv"},
            "network security": {"max_results": 5, "source": "arxiv"},
            "information security": {"max_results": 5, "source": "arxiv"},
            "privacy protection": {"max_results": 5, "source": "arxiv"},
            "digital forensics": {"max_results": 5, "source": "arxiv"}
        }
    
    def collect_papers_for_keyword(self, keyword, time_folder=None):
        """특정 키워드로 논문 수집 및 PDF 다운로드"""
        try:
            config = self.keyword_configs.get(keyword, {"max_results": 5, "source": "arxiv"})
            
            logging.info(f"'{keyword}' 키워드로 논문 수집 시작...")
            
            response = self.session.post(f"{self.server_url}/search_papers", json={
                "query": keyword,
                "max_results": config["max_results"],
                "source": config["source"]
            }, timeout=60)
            
            if response.status_code == 200:
                papers = response.json()
                logging.info(f"'{keyword}': {len(papers)}개 논문 수집 완료")
                
                # 수집된 논문 정보 로깅 및 PDF 다운로드
                downloaded_count = 0
                skipped_long_papers = 0
                
                for i, paper in enumerate(papers, 1):
                    logging.info(f"  {i}. {paper['title']} ({paper['source']})")
                    
                    # PDF 다운로드 시도
                    if paper.get('pdf_url'):
                        try:
                            download_response = self.session.post(f"{self.server_url}/download_paper", 
                                                                params={"paper_url": paper['url'], "time_folder": time_folder}, timeout=60)
                            
                            if download_response.status_code == 200:
                                result = download_response.json()
                                if result.get('success'):
                                    logging.info(f"    📥 PDF 다운로드 완료: {result.get('filename', 'N/A')}")
                                    downloaded_count += 1
                                else:
                                    error_msg = result.get('error', 'Unknown error')
                                    if 'too long' in error_msg.lower():
                                        logging.info(f"    ⏭️ 페이지 수 초과로 건너뜀: {error_msg}")
                                        skipped_long_papers += 1
                                    else:
                                        logging.warning(f"    ❌ PDF 다운로드 실패: {error_msg}")
                            else:
                                logging.warning(f"    ❌ PDF 다운로드 요청 실패: {download_response.status_code}")
                                
                        except Exception as e:
                            logging.warning(f"    ❌ PDF 다운로드 오류: {e}")
                    
                    # 다운로드 간 지연 (서버 부하 방지)
                    time.sleep(1.5)
                
                logging.info(f"'{keyword}': {downloaded_count}개 PDF 다운로드 완료, {skipped_long_papers}개 페이지 수 초과로 건너뜀")
                return papers
            else:
                logging.error(f"'{keyword}' 검색 실패: {response.status_code}")
                return []
                
        except Exception as e:
            logging.error(f"'{keyword}' 수집 중 오류: {e}")
            return []
    
    def daily_collection(self):
        """매일 실행할 논문 수집 작업"""
        # 실행 시간 기준 폴더 생성
        current_time = datetime.now()
        time_folder = current_time.strftime('%Y%m%d_%H%M%S')
        
        logging.info("=" * 60)
        logging.info(f"일일 논문 수집 시작 - {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logging.info(f"📁 저장 폴더: {time_folder}")
        logging.info("=" * 60)
        
        # 시간별 폴더 생성
        import os
        from pathlib import Path
        
        papers_dir = Path("papers")
        time_papers_dir = papers_dir / time_folder
        time_papers_dir.mkdir(parents=True, exist_ok=True)
        
        logging.info(f"📂 폴더 생성 완료: {time_papers_dir}")
        
        total_collected = 0
        total_downloaded = 0
        total_skipped = 0
        
        for i, keyword in enumerate(self.keywords, 1):
            logging.info(f"진행률: {i}/{len(self.keywords)} - '{keyword}' 처리 중...")
            papers = self.collect_papers_for_keyword(keyword, time_folder)
            total_collected += len(papers)
            
            # 키워드 간 지연 시간 (서버 부하 방지)
            if i < len(self.keywords):  # 마지막 키워드가 아니면 지연
                time.sleep(3)
        
        logging.info("=" * 60)
        logging.info(f"일일 수집 완료: 총 {total_collected}개 논문 수집")
        logging.info(f"키워드 수: {len(self.keywords)}개")
        logging.info(f"📁 저장 위치: {time_papers_dir}")
        logging.info("=" * 60)
    
    def weekly_summary(self):
        """주간 요약 생성"""
        try:
            logging.info("=" * 60)
            logging.info(f"주간 요약 생성 시작 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logging.info("=" * 60)
            
            response = self.session.get(f"{self.server_url}/papers?limit=200")
            
            if response.status_code == 200:
                papers = response.json()
                
                # 최근 7일간 수집된 논문 필터링
                week_ago = datetime.now() - timedelta(days=7)
                
                recent_papers = []
                for paper in papers:
                    try:
                        # 날짜 파싱 개선
                        created_at = paper['created_at']
                        logging.info(f"파싱 중인 날짜: {created_at}")
                        
                        # 다양한 날짜 형식 처리
                        if 'T' in created_at:
                            # ISO 형식: 2025-07-23T08:15:12
                            paper_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        elif ' ' in created_at:
                            # SQL 형식: 2025-07-23 08:15:12
                            paper_date = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
                        else:
                            # 날짜만: 2025-07-23
                            paper_date = datetime.strptime(created_at, '%Y-%m-%d')
                        
                        logging.info(f"파싱된 날짜: {paper_date}, 기준일: {week_ago}")
                        
                        if paper_date > week_ago:
                            recent_papers.append(paper)
                            logging.info(f"최근 논문 추가: {paper['title'][:50]}...")
                    except Exception as e:
                        logging.error(f"날짜 파싱 오류: {paper.get('created_at', 'N/A')} - {e}")
                        continue
                
                # 1. 기본 통계
                logging.info(f"📊 주간 요약: 최근 7일간 {len(recent_papers)}개 논문 수집")
                
                # 2. 소스별 통계
                source_stats = {}
                for paper in recent_papers:
                    source = paper['source']
                    source_stats[source] = source_stats.get(source, 0) + 1
                
                logging.info("📈 소스별 통계:")
                for source, count in source_stats.items():
                    logging.info(f"  📚 {source}: {count}개")
                
                # 3. 키워드별 통계 (제목에서 키워드 매칭)
                keyword_stats = {}
                for paper in recent_papers:
                    title_lower = paper['title'].lower()
                    for keyword in self.keywords:
                        if keyword.lower() in title_lower:
                            keyword_stats[keyword] = keyword_stats.get(keyword, 0) + 1
                
                logging.info("🔍 키워드별 통계:")
                for keyword, count in keyword_stats.items():
                    logging.info(f"  🏷️ {keyword}: {count}개")
                
                # 4. PDF 다운로드 통계
                pdf_downloaded = sum(1 for paper in recent_papers if paper.get('file_path'))
                pdf_total = len(recent_papers)
                pdf_rate = (pdf_downloaded / pdf_total * 100) if pdf_total > 0 else 0
                
                logging.info(f"📥 PDF 다운로드: {pdf_downloaded}/{pdf_total}개 ({pdf_rate:.1f}%)")
                
                # 5. 최근 논문 목록 (상위 10개)
                logging.info("📋 최근 수집된 논문 (상위 10개):")
                for i, paper in enumerate(recent_papers[:10], 1):
                    pdf_status = "✅" if paper.get('file_path') else "❌"
                    logging.info(f"  {i}. {pdf_status} {paper['title']}")
                    logging.info(f"     👥 저자: {', '.join(paper['authors'][:3])}{'...' if len(paper['authors']) > 3 else ''}")
                    logging.info(f"     📅 수집일: {paper['created_at'][:10]}")
                    logging.info(f"     🔗 소스: {paper['source']}")
                    logging.info("")
                
                # 6. 일별 수집 통계
                daily_stats = {}
                for paper in recent_papers:
                    date = paper['created_at'][:10]  # YYYY-MM-DD
                    daily_stats[date] = daily_stats.get(date, 0) + 1
                
                logging.info("📅 일별 수집 통계:")
                for date in sorted(daily_stats.keys()):
                    count = daily_stats[date]
                    logging.info(f"  📆 {date}: {count}개")
                
                # 7. 추천 키워드 (수집이 적은 키워드)
                logging.info("💡 추천 사항:")
                for keyword in self.keywords:
                    if keyword not in keyword_stats or keyword_stats[keyword] < 2:
                        logging.info(f"  🔍 '{keyword}' 키워드로 더 많은 논문 수집 권장")
                
                logging.info("=" * 60)
                logging.info("주간 요약 완료")
                logging.info("=" * 60)
                
            else:
                logging.error(f"주간 요약 생성 실패: {response.status_code}")
                
        except Exception as e:
            logging.error(f"주간 요약 생성 중 오류: {e}")
    
    def run_scheduler(self):
        """스케줄러 실행"""
        logging.info("자동 논문 수집 스케줄러 시작")
        
        # 매일 오전 9시에 수집
        schedule.every().day.at("09:00").do(self.daily_collection)
        
        # 매주 일요일 오전 10시에 주간 요약
        schedule.every().sunday.at("10:00").do(self.weekly_summary)
        
        # 즉시 한 번 실행 (테스트용)
        logging.info("즉시 첫 번째 수집 실행...")
        self.daily_collection()
        
        logging.info("스케줄러 실행 중... (Ctrl+C로 종료)")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # 1분마다 체크
        except KeyboardInterrupt:
            logging.info("스케줄러 종료")

def main():
    """메인 함수"""
    collector = AutoPaperCollector()
    
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "collect":
            # 즉시 수집만 실행
            collector.daily_collection()
        elif sys.argv[1] == "summary":
            # 주간 요약만 실행
            collector.weekly_summary()
        else:
            print("사용법: python auto_collector.py [collect|summary]")
    else:
        # 스케줄러 실행
        collector.run_scheduler()

if __name__ == "__main__":
    main() 
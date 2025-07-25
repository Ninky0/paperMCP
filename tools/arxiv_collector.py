import arxiv
import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class ArxivCollector:
    def __init__(self):
        self.client = arxiv.Client(
            page_size=100,
            delay_seconds=3,
            num_retries=3
        )
    
    async def search(self, query: str, max_results: int = 10, existing_urls: List[str] = None) -> List[Dict[str, Any]]:
        """arXiv에서 논문 검색 (중복 제거 포함)"""
        try:
            # 기존 URL 목록이 없으면 빈 리스트로 초기화
            if existing_urls is None:
                existing_urls = []
            
            # 더 많은 결과를 검색해서 중복을 제거한 후 원하는 개수만큼 반환
            search_size = max_results * 3  # 충분한 새로운 논문을 찾기 위해 3배로 검색
            
            search = arxiv.Search(
                query=query,
                max_results=search_size,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )
            
            papers = []
            new_papers = []
            
            for result in self.client.results(search):
                paper = {
                    'title': result.title,
                    'authors': [author.name for author in result.authors],
                    'abstract': result.summary,
                    'url': result.entry_id,
                    'pdf_url': result.pdf_url,
                    'published_date': result.published.strftime('%Y-%m-%d') if result.published else None,
                    'keywords': [],  # arXiv는 키워드를 제공하지 않음
                    'source': 'arxiv'
                }
                papers.append(paper)
                
                # 중복이 아닌 새로운 논문만 추가
                if result.entry_id not in existing_urls:
                    new_papers.append(paper)
                    logger.info(f"New paper found: {paper['title']}")
                    
                    # 원하는 개수만큼 새로운 논문을 찾으면 중단
                    if len(new_papers) >= max_results:
                        break
                else:
                    logger.info(f"Skipping existing paper: {paper['title']}")
            
            logger.info(f"Found {len(papers)} total papers, {len(new_papers)} new papers from arXiv for query: {query}")
            return new_papers
            
        except Exception as e:
            logger.error(f"Error searching arXiv: {e}")
            return []
    
    async def search_by_category(self, category: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """특정 카테고리에서 논문 검색"""
        try:
            # arXiv 카테고리 검색
            search = arxiv.Search(
                query=f"cat:{category}",
                max_results=max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )
            
            papers = []
            for result in self.client.results(search):
                paper = {
                    'title': result.title,
                    'authors': [author.name for author in result.authors],
                    'abstract': result.summary,
                    'url': result.entry_id,
                    'pdf_url': result.pdf_url,
                    'published_date': result.published.strftime('%Y-%m-%d') if result.published else None,
                    'keywords': [],
                    'source': 'arxiv'
                }
                papers.append(paper)
                
                if len(papers) >= max_results:
                    break
            
            logger.info(f"Found {len(papers)} papers from arXiv category: {category}")
            return papers
            
        except Exception as e:
            logger.error(f"Error searching arXiv category {category}: {e}")
            return []
    
    async def get_recent_papers(self, max_results: int = 20) -> List[Dict[str, Any]]:
        """최근 논문들 가져오기"""
        try:
            # 최근 논문 검색
            search = arxiv.Search(
                query="",
                max_results=max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )
            
            papers = []
            for result in self.client.results(search):
                paper = {
                    'title': result.title,
                    'authors': [author.name for author in result.authors],
                    'abstract': result.summary,
                    'url': result.entry_id,
                    'pdf_url': result.pdf_url,
                    'published_date': result.published.strftime('%Y-%m-%d') if result.published else None,
                    'keywords': [],
                    'source': 'arxiv'
                }
                papers.append(paper)
                
                if len(papers) >= max_results:
                    break
            
            logger.info(f"Found {len(papers)} recent papers from arXiv")
            return papers
            
        except Exception as e:
            logger.error(f"Error getting recent papers from arXiv: {e}")
            return []
    
    async def search_by_author(self, author_name: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """특정 저자의 논문 검색"""
        try:
            search = arxiv.Search(
                query=f"au:\"{author_name}\"",
                max_results=max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )
            
            papers = []
            for result in self.client.results(search):
                paper = {
                    'title': result.title,
                    'authors': [author.name for author in result.authors],
                    'abstract': result.summary,
                    'url': result.entry_id,
                    'pdf_url': result.pdf_url,
                    'published_date': result.published.strftime('%Y-%m-%d') if result.published else None,
                    'keywords': [],
                    'source': 'arxiv'
                }
                papers.append(paper)
                
                if len(papers) >= max_results:
                    break
            
            logger.info(f"Found {len(papers)} papers by {author_name} from arXiv")
            return papers
            
        except Exception as e:
            logger.error(f"Error searching papers by author {author_name}: {e}")
            return [] 
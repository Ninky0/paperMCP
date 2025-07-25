import requests
import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

class PubMedCollector:
    def __init__(self):
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        self.search_url = f"{self.base_url}esearch.fcgi"
        self.fetch_url = f"{self.base_url}efetch.fcgi"
        self.summary_url = f"{self.base_url}esummary.fcgi"
    
    async def search(self, query: str, max_results: int = 10, existing_urls: List[str] = None) -> List[Dict[str, Any]]:
        """PubMed에서 논문 검색 (중복 제거 포함)"""
        try:
            # 기존 URL 목록이 없으면 빈 리스트로 초기화
            if existing_urls is None:
                existing_urls = []
            
            # 더 많은 결과를 검색해서 중복을 제거한 후 원하는 개수만큼 반환
            search_size = max_results * 3  # 충분한 새로운 논문을 찾기 위해 3배로 검색
            
            # 1단계: 검색하여 ID 목록 가져오기
            search_params = {
                'db': 'pubmed',
                'term': query,
                'retmax': search_size,
                'retmode': 'xml',
                'sort': 'date'
            }
            
            response = requests.get(self.search_url, params=search_params)
            response.raise_for_status()
            
            # XML 파싱
            root = ET.fromstring(response.content)
            id_list = root.find('.//IdList')
            
            if id_list is None:
                logger.warning("No results found in PubMed")
                return []
            
            pmids = [id_elem.text for id_elem in id_list.findall('Id')]
            
            if not pmids:
                logger.warning("No PMIDs found")
                return []
            
            # 2단계: 상세 정보 가져오기
            all_papers = await self._fetch_paper_details(pmids)
            
            # 중복 제거: 새로운 논문들만 필터링
            new_papers = []
            for paper in all_papers:
                if paper['url'] not in existing_urls:
                    new_papers.append(paper)
                    logger.info(f"New PubMed paper found: {paper['title']}")
                    
                    # 원하는 개수만큼 새로운 논문을 찾으면 중단
                    if len(new_papers) >= max_results:
                        break
                else:
                    logger.info(f"Skipping existing PubMed paper: {paper['title']}")
            
            logger.info(f"Found {len(all_papers)} total papers, {len(new_papers)} new papers from PubMed for query: {query}")
            return new_papers
            
        except Exception as e:
            logger.error(f"Error searching PubMed: {e}")
            return []
    
    async def _fetch_paper_details(self, pmids: List[str]) -> List[Dict[str, Any]]:
        """PMID 목록으로 상세 정보 가져오기"""
        try:
            # 여러 PMID를 쉼표로 구분
            pmid_string = ','.join(pmids)
            
            # 상세 정보 요청
            fetch_params = {
                'db': 'pubmed',
                'id': pmid_string,
                'retmode': 'xml',
                'rettype': 'abstract'
            }
            
            response = requests.get(self.fetch_url, params=fetch_params)
            response.raise_for_status()
            
            # XML 파싱
            root = ET.fromstring(response.content)
            papers = []
            
            for article in root.findall('.//PubmedArticle'):
                try:
                    paper = self._parse_article(article)
                    if paper:
                        papers.append(paper)
                except Exception as e:
                    logger.error(f"Error parsing article: {e}")
                    continue
            
            return papers
            
        except Exception as e:
            logger.error(f"Error fetching paper details: {e}")
            return []
    
    def _parse_article(self, article_elem) -> Dict[str, Any]:
        """개별 논문 파싱"""
        try:
            # 기본 정보 추출
            medline_citation = article_elem.find('.//MedlineCitation')
            if medline_citation is None:
                return None
            
            # 제목
            title_elem = medline_citation.find('.//ArticleTitle')
            title = title_elem.text if title_elem is not None else "No title"
            
            # 저자들
            authors = []
            author_list = medline_citation.find('.//AuthorList')
            if author_list is not None:
                for author in author_list.findall('Author'):
                    last_name = author.find('LastName')
                    first_name = author.find('ForeName')
                    if last_name is not None and first_name is not None:
                        authors.append(f"{first_name.text} {last_name.text}")
                    elif last_name is not None:
                        authors.append(last_name.text)
            
            # 초록
            abstract_elem = medline_citation.find('.//Abstract/AbstractText')
            abstract = abstract_elem.text if abstract_elem is not None else "No abstract available"
            
            # PMID
            pmid_elem = medline_citation.find('PMID')
            pmid = pmid_elem.text if pmid_elem is not None else ""
            
            # DOI 추출 (ArticleIdList에서)
            doi = None
            article_id_list = medline_citation.find('.//ArticleIdList')
            if article_id_list is not None:
                for article_id in article_id_list.findall('ArticleId'):
                    id_type = article_id.get('IdType')
                    if id_type == 'doi':
                        doi = article_id.text
                        break
            
            # 발행일
            pub_date_elem = medline_citation.find('.//PubDate')
            published_date = None
            if pub_date_elem is not None:
                year_elem = pub_date_elem.find('Year')
                month_elem = pub_date_elem.find('Month')
                if year_elem is not None:
                    year = year_elem.text
                    month = month_elem.text if month_elem is not None else "01"
                    published_date = f"{year}-{month.zfill(2)}-01"
            
            # 키워드
            keywords = []
            keyword_list = medline_citation.find('.//KeywordList')
            if keyword_list is not None:
                for keyword in keyword_list.findall('Keyword'):
                    if keyword.text:
                        keywords.append(keyword.text)
            
            # URL 생성
            url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            
            # DOI URL 생성 (DOI가 있는 경우)
            doi_url = None
            if doi:
                doi_url = f"https://doi.org/{doi}"
            
            return {
                'title': title,
                'authors': authors,
                'abstract': abstract,
                'url': url,
                'pdf_url': doi_url,  # DOI URL을 PDF URL로 사용
                'doi': doi,  # DOI 정보 추가
                'published_date': published_date,
                'keywords': keywords,
                'source': 'pubmed'
            }
            
        except Exception as e:
            logger.error(f"Error parsing article element: {e}")
            return None
    
    async def search_by_author(self, author_name: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """특정 저자의 논문 검색"""
        try:
            query = f"{author_name}[Author]"
            return await self.search(query, max_results)
        except Exception as e:
            logger.error(f"Error searching by author {author_name}: {e}")
            return []
    
    async def search_by_journal(self, journal_name: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """특정 저널의 논문 검색"""
        try:
            query = f"{journal_name}[Journal]"
            return await self.search(query, max_results)
        except Exception as e:
            logger.error(f"Error searching by journal {journal_name}: {e}")
            return []
    
    async def search_recent_papers(self, days: int = 30, max_results: int = 20) -> List[Dict[str, Any]]:
        """최근 논문들 검색"""
        try:
            # 최근 N일 내 논문 검색
            query = f"{days}[Days]"
            return await self.search(query, max_results)
        except Exception as e:
            logger.error(f"Error searching recent papers: {e}")
            return [] 
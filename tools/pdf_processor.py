import requests
import os
import asyncio
import logging
from typing import Dict, Any, Optional
from urllib.parse import urlparse
import PyPDF2
from datetime import datetime

logger = logging.getLogger(__name__)

class PDFProcessor:
    def __init__(self, download_dir: str = "papers", time_folder: Optional[str] = None):
        self.download_dir = download_dir
        self.time_folder = time_folder
        self._ensure_download_dir()
    
    def _ensure_download_dir(self):
        """다운로드 디렉토리 생성"""
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
            logger.info(f"Created download directory: {self.download_dir}")
        
        # 시간별 폴더가 지정된 경우 생성
        if self.time_folder:
            time_dir = os.path.join(self.download_dir, self.time_folder)
            if not os.path.exists(time_dir):
                os.makedirs(time_dir)
                logger.info(f"Created time folder: {time_dir}")
    
    async def download_and_process(self, paper_url: str, paper_id: Optional[int] = None, max_pages: int = 30) -> Dict[str, Any]:
        """논문 다운로드 및 처리"""
        try:
            # URL에서 PDF URL 추출
            pdf_url = await self._get_pdf_url(paper_url)
            if not pdf_url:
                return {
                    'success': False,
                    'error': 'PDF URL not found',
                    'paper_url': paper_url
                }
            
            # 파일명 생성
            filename = await self._generate_filename(paper_url, pdf_url)
            
            # 시간별 폴더가 있으면 해당 폴더에 저장
            if self.time_folder:
                file_path = os.path.join(self.download_dir, self.time_folder, filename)
            else:
                file_path = os.path.join(self.download_dir, filename)
            
            # 이미 존재하는지 확인
            if os.path.exists(file_path):
                logger.info(f"File already exists: {file_path}")
                return {
                    'success': True,
                    'file_path': file_path,
                    'filename': filename,
                    'message': 'File already exists'
                }
            
            # PDF 다운로드
            success = await self._download_pdf(pdf_url, file_path)
            if not success:
                return {
                    'success': False,
                    'error': 'Failed to download PDF',
                    'pdf_url': pdf_url
                }
            
            # PDF 메타데이터 추출
            metadata = await self._extract_metadata(file_path)
            
            # 페이지 수 확인 및 제한
            if metadata.get('pages', 0) > max_pages:
                # 파일 삭제
                os.remove(file_path)
                logger.warning(f"PDF too long ({metadata.get('pages', 0)} pages), deleted: {filename}")
                return {
                    'success': False,
                    'error': f'PDF too long ({metadata.get("pages", 0)} pages, max: {max_pages})',
                    'pdf_url': pdf_url,
                    'pages': metadata.get('pages', 0)
                }
            
            return {
                'success': True,
                'file_path': file_path,
                'filename': filename,
                'metadata': metadata,
                'pdf_url': pdf_url
            }
            
        except Exception as e:
            logger.error(f"Error downloading and processing paper: {e}")
            return {
                'success': False,
                'error': str(e),
                'paper_url': paper_url
            }
    
    async def _get_pdf_url(self, paper_url: str) -> Optional[str]:
        """논문 URL에서 PDF URL 추출"""
        try:
            # arXiv URL 처리
            if 'arxiv.org' in paper_url:
                # arXiv URL을 PDF URL로 변환
                if '/abs/' in paper_url:
                    pdf_url = paper_url.replace('/abs/', '/pdf/') + '.pdf'
                    return pdf_url
                elif '/pdf/' in paper_url:
                    return paper_url
            
            # DOI URL 처리 (PubMed 논문)
            elif 'doi.org' in paper_url:
                return await self._extract_pdf_from_doi(paper_url)
            
            # PubMed URL 처리
            elif 'pubmed.ncbi.nlm.nih.gov' in paper_url:
                # PubMed URL에서 DOI를 추출하여 처리
                doi = await self._extract_doi_from_pubmed(paper_url)
                if doi:
                    doi_url = f"https://doi.org/{doi}"
                    return await self._extract_pdf_from_doi(doi_url)
                else:
                    logger.warning("PubMed URL에서 DOI를 찾을 수 없음")
                    return None
            
            # 기타 URL은 직접 요청하여 PDF 링크 찾기
            else:
                response = requests.get(paper_url, timeout=10)
                response.raise_for_status()
                
                # HTML에서 PDF 링크 찾기
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # PDF 링크 찾기
                pdf_links = soup.find_all('a', href=True)
                for link in pdf_links:
                    href = link['href']
                    if 'pdf' in href.lower() or 'download' in href.lower():
                        if href.startswith('http'):
                            return href
                        else:
                            # 상대 URL을 절대 URL로 변환
                            from urllib.parse import urljoin
                            return urljoin(paper_url, href)
                
                return None
                
        except Exception as e:
            logger.error(f"Error extracting PDF URL from {paper_url}: {e}")
            return None
    
    async def _extract_pdf_from_doi(self, doi_url: str) -> Optional[str]:
        """DOI 링크에서 PDF URL 추출"""
        try:
            logger.info(f"DOI 링크에서 PDF 추출 시도: {doi_url}")
            
            # DOI 링크로 접속
            response = requests.get(doi_url, timeout=15)
            response.raise_for_status()
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 다양한 PDF 다운로드 링크 패턴 찾기
            pdf_selectors = [
                'a[href*="pdf"][href*="download"]',
                'a[href*="pdf"][href*=".pdf"]',
                'a[class*="download"][href*="pdf"]',
                'a[class*="pdf"][href*="download"]',
                'a[title*="PDF"]',
                'a[aria-label*="PDF"]',
                'a[aria-label*="Download PDF"]',
                'a.btn[href*="pdf"]',
                'a[data-download-files-key="pdf"]'
            ]
            
            for selector in pdf_selectors:
                pdf_links = soup.select(selector)
                for link in pdf_links:
                    href = link.get('href')
                    if href:
                        # 절대 URL로 변환
                        if href.startswith('http'):
                            pdf_url = href
                        else:
                            from urllib.parse import urljoin
                            pdf_url = urljoin(doi_url, href)
                        
                        logger.info(f"PDF 링크 발견: {pdf_url}")
                        return pdf_url
            
            # 일반적인 PDF 링크도 찾기
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link.get('href', '').lower()
                if 'pdf' in href and ('download' in href or '.pdf' in href):
                    if href.startswith('http'):
                        pdf_url = link['href']
                    else:
                        from urllib.parse import urljoin
                        pdf_url = urljoin(doi_url, link['href'])
                    
                    logger.info(f"일반 PDF 링크 발견: {pdf_url}")
                    return pdf_url
            
            logger.warning(f"DOI 페이지에서 PDF 링크를 찾을 수 없음: {doi_url}")
            return None
            
        except Exception as e:
            logger.error(f"DOI에서 PDF 추출 중 오류: {e}")
            return None
    
    async def _extract_doi_from_pubmed(self, pubmed_url: str) -> Optional[str]:
        """PubMed URL에서 DOI 추출"""
        try:
            response = requests.get(pubmed_url, timeout=10)
            response.raise_for_status()
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # DOI 링크 찾기
            doi_links = soup.find_all('a', href=True)
            for link in doi_links:
                href = link.get('href', '')
                if 'doi.org' in href:
                    # DOI URL에서 DOI 추출
                    doi = href.split('doi.org/')[-1]
                    logger.info(f"PubMed에서 DOI 추출: {doi}")
                    return doi
            
            return None
            
        except Exception as e:
            logger.error(f"PubMed에서 DOI 추출 중 오류: {e}")
            return None
    
    async def _generate_filename(self, paper_url: str, pdf_url: str) -> str:
        """파일명 생성"""
        try:
            # URL에서 파일명 추출
            parsed_url = urlparse(pdf_url)
            original_filename = os.path.basename(parsed_url.path)
            
            if original_filename and original_filename.endswith('.pdf'):
                # 특수문자 제거 및 안전한 파일명으로 변환
                safe_filename = "".join(c for c in original_filename if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
                return safe_filename
            
            # 기본 파일명 생성
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            return f"paper_{timestamp}.pdf"
            
        except Exception as e:
            logger.error(f"Error generating filename: {e}")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            return f"paper_{timestamp}.pdf"
    
    async def _download_pdf(self, pdf_url: str, file_path: str) -> bool:
        """PDF 파일 다운로드"""
        try:
            logger.info(f"Downloading PDF from: {pdf_url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(pdf_url, headers=headers, timeout=30, stream=True)
            response.raise_for_status()
            
            # 파일 크기 확인
            content_length = response.headers.get('content-length')
            if content_length:
                file_size = int(content_length)
                if file_size > 100 * 1024 * 1024:  # 100MB 제한
                    logger.warning(f"File too large: {file_size} bytes")
                    return False
            
            # 파일 저장
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"Successfully downloaded: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading PDF: {e}")
            return False
    
    async def _extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """PDF 메타데이터 추출"""
        try:
            metadata = {
                'title': None,
                'author': None,
                'subject': None,
                'creator': None,
                'producer': None,
                'pages': 0,
                'file_size': os.path.getsize(file_path)
            }
            
            # PyPDF2로 메타데이터 추출
            try:
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    
                    # 기본 메타데이터
                    if pdf_reader.metadata:
                        info = pdf_reader.metadata
                        metadata['title'] = info.get('/Title')
                        metadata['author'] = info.get('/Author')
                        metadata['subject'] = info.get('/Subject')
                        metadata['creator'] = info.get('/Creator')
                        metadata['producer'] = info.get('/Producer')
                    
                    # 페이지 수
                    metadata['pages'] = len(pdf_reader.pages)
                    
            except Exception as e:
                logger.warning(f"PyPDF2 metadata extraction failed: {e}")
            
            # PyPDF2로 텍스트 추출 시도
            try:
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    if len(pdf_reader.pages) > 0 and not metadata['title']:
                        first_page = pdf_reader.pages[0]
                        text = first_page.extract_text()
                        if text:
                            # 첫 번째 줄을 제목으로 추측
                            lines = text.split('\n')
                            if lines:
                                metadata['title'] = lines[0][:100]  # 첫 100자
            except Exception as e:
                logger.warning(f"PyPDF2 text extraction failed: {e}")
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            return {'error': str(e)}
    
    async def cleanup_old_files(self, days: int = 30):
        """오래된 파일 정리"""
        try:
            cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
            
            for filename in os.listdir(self.download_dir):
                file_path = os.path.join(self.download_dir, filename)
                if os.path.isfile(file_path):
                    file_time = os.path.getmtime(file_path)
                    if file_time < cutoff_time:
                        os.remove(file_path)
                        logger.info(f"Deleted old file: {filename}")
            
        except Exception as e:
            logger.error(f"Error cleaning up old files: {e}")
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """파일 정보 조회"""
        try:
            if not os.path.exists(file_path):
                return {'error': 'File not found'}
            
            stat = os.stat(file_path)
            return {
                'file_path': file_path,
                'file_size': stat.st_size,
                'created_time': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'exists': True
            }
            
        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            return {'error': str(e)} 
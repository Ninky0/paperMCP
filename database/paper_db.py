import sqlite3
import asyncio
import json
import os
from typing import List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# SQLite 데이터베이스로 논문 정보 관리
class PaperDatabase:
    def __init__(self, db_path: str = "papers.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """데이터베이스 초기화 및 테이블 생성"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS papers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                authors TEXT NOT NULL,
                abstract TEXT,
                url TEXT UNIQUE NOT NULL,
                pdf_url TEXT,
                published_date TEXT,
                keywords TEXT,
                source TEXT NOT NULL,
                file_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    
    async def add_papers(self, papers: List[dict]) -> List[dict]:
        """
        논문들을 데이터베이스에 추가
        - 새 논문들을 데이터베이스에 저장
        - 중복 제거: URL 기준으로 이미 있는 논문은 제외
        - JSON 형태로 저자, 키워드 저장
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        added_papers = []
        
        for paper in papers:
            try:
                # 중복 체크
                cursor.execute("SELECT id FROM papers WHERE url = ?", (paper['url'],))
                existing = cursor.fetchone()
                
                if existing:
                    logger.info(f"Paper already exists: {paper['title']}")
                    continue
                
                # 새 논문 추가
                cursor.execute('''
                    INSERT INTO papers (title, authors, abstract, url, pdf_url, published_date, keywords, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    paper['title'],
                    json.dumps(paper['authors']),
                    paper['abstract'],
                    paper['url'],
                    paper.get('pdf_url'),
                    paper.get('published_date'),
                    json.dumps(paper.get('keywords', [])),
                    paper['source']
                ))
                
                paper_id = cursor.lastrowid
                paper['id'] = paper_id
                added_papers.append(paper)
                
            except Exception as e:
                logger.error(f"Error adding paper {paper['title']}: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        logger.info(f"Added {len(added_papers)} new papers")
        return added_papers
    
    async def get_papers(self, limit: int = 50, offset: int = 0) -> List[dict]:
        """저장된 논문 목록 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, title, authors, abstract, url, pdf_url, published_date, keywords, source, file_path, created_at
            FROM papers
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        
        rows = cursor.fetchall()
        papers = []
        
        for row in rows:
            paper = {
                'id': row[0],
                'title': row[1],
                'authors': json.loads(row[2]),
                'abstract': row[3],
                'url': row[4],
                'pdf_url': row[5],
                'published_date': row[6],
                'keywords': json.loads(row[7]) if row[7] else [],
                'source': row[8],
                'file_path': row[9],
                'created_at': row[10]
            }
            papers.append(paper)
        
        conn.close()
        return papers
    
    async def get_paper_by_id(self, paper_id: int) -> Optional[dict]:
        """ID로 특정 논문 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, title, authors, abstract, url, pdf_url, published_date, keywords, source, file_path, created_at
            FROM papers
            WHERE id = ?
        ''', (paper_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'title': row[1],
                'authors': json.loads(row[2]),
                'abstract': row[3],
                'url': row[4],
                'pdf_url': row[5],
                'published_date': row[6],
                'keywords': json.loads(row[7]) if row[7] else [],
                'source': row[8],
                'file_path': row[9],
                'created_at': row[10]
            }
        return None
    
    async def update_paper_file_path(self, paper_id: int, file_path: str):
        """
        논문의 파일 경로 업데이트
        - PDF 다운로드 후 로컬 파일 경로 저장
        - 나중에 파일 접근 시 사용
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE papers
            SET file_path = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (file_path, paper_id))
        
        conn.commit()
        conn.close()
    
    async def delete_paper(self, paper_id: int):
        """
        논문 삭제
        - 데이터베이스에서 논문 정보 삭제
        - 파일도 함께 삭제: 로컬 PDF 파일도 자동 삭제
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 파일 경로 확인
        cursor.execute("SELECT file_path FROM papers WHERE id = ?", (paper_id,))
        row = cursor.fetchone()
        
        if row and row[0]:
            # 파일 삭제
            try:
                os.remove(row[0])
                logger.info(f"Deleted file: {row[0]}")
            except FileNotFoundError:
                logger.warning(f"File not found: {row[0]}")
        
        # 데이터베이스에서 삭제
        cursor.execute("DELETE FROM papers WHERE id = ?", (paper_id,))
        conn.commit()
        conn.close()
        
        logger.info(f"Deleted paper with ID: {paper_id}")
    
    async def search_papers(self, query: str) -> List[dict]:
        """
        논문 검색
        - 제목, 초록, 저자에서 키워드 검색
        - 부분 일치 검색 지원
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, title, authors, abstract, url, pdf_url, published_date, keywords, source, file_path, created_at
            FROM papers
            WHERE title LIKE ? OR abstract LIKE ? OR authors LIKE ?
            ORDER BY created_at DESC
        ''', (f'%{query}%', f'%{query}%', f'%{query}%'))
        
        rows = cursor.fetchall()
        papers = []
        
        for row in rows:
            paper = {
                'id': row[0],
                'title': row[1],
                'authors': json.loads(row[2]),
                'abstract': row[3],
                'url': row[4],
                'pdf_url': row[5],
                'published_date': row[6],
                'keywords': json.loads(row[7]) if row[7] else [],
                'source': row[8],
                'file_path': row[9],
                'created_at': row[10]
            }
            papers.append(paper)
        
        conn.close()
        return papers 
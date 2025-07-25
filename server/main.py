#!/usr/bin/env python3
"""
논문 수집 MCP 서버 메인 파일
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import asyncio
import logging

# 프로젝트 루트를 Python 경로에 추가
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tools.arxiv_collector import ArxivCollector
from tools.pubmed_collector import PubMedCollector
from tools.pdf_processor import PDFProcessor
from database.paper_db import PaperDatabase

# FastAPI 앱 생성
app = FastAPI(title="논문 수집 MCP 서버", version="1.0.0")

# 수집기 및 데이터베이스 초기화
arxiv_collector = ArxivCollector()
pubmed_collector = PubMedCollector()
pdf_processor = PDFProcessor()  # 기본 PDF 프로세서 (시간별 폴더 없음)
paper_db = PaperDatabase()

# 요청 모델
class SearchRequest(BaseModel):
    query: str
    max_results: int = 10
    source: str = "arxiv"  # "arxiv", "pubmed", "all"

class DownloadRequest(BaseModel):
    paper_url: str

# 기본 엔드포인트
@app.get("/")
async def root():
    return {"message": "논문 수집 MCP 서버가 실행 중입니다"}

# 논문 검색 엔드포인트
@app.post("/search_papers")
async def search_papers(request: SearchRequest):
    try:
        papers = []
        
        # 기존 논문 URL들을 가져와서 중복 제거에 사용
        existing_papers = await paper_db.get_papers(limit=10000)  # 충분히 많은 기존 논문들
        existing_urls = [paper['url'] for paper in existing_papers]
        
        logging.info(f"Found {len(existing_urls)} existing papers for duplicate checking")
        
        # arXiv에서 검색 (중복 제거 포함)
        if request.source in ["arxiv", "all"]:
            arxiv_papers = await arxiv_collector.search(request.query, request.max_results, existing_urls)
            papers.extend(arxiv_papers)
        
        # PubMed에서 검색 (중복 제거 포함)
        if request.source in ["pubmed", "all"]:
            pubmed_papers = await pubmed_collector.search(request.query, request.max_results, existing_urls)
            papers.extend(pubmed_papers)
        
        # 데이터베이스에 저장
        if papers:
            saved_papers = await paper_db.add_papers(papers)
            return saved_papers
        
        return []
        
    except Exception as e:
        logging.error(f"논문 검색 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 저장된 논문 목록 조회
@app.get("/papers")
async def get_papers(limit: int = 50, offset: int = 0):
    try:
        papers = await paper_db.get_papers(limit, offset)
        return papers
    except Exception as e:
        logging.error(f"논문 목록 조회 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 특정 논문 조회
@app.get("/papers/{paper_id}")
async def get_paper(paper_id: int):
    try:
        paper = await paper_db.get_paper_by_id(paper_id)
        if paper:
            return paper
        else:
            raise HTTPException(status_code=404, detail="논문을 찾을 수 없습니다")
    except Exception as e:
        logging.error(f"논문 조회 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 논문 다운로드
@app.post("/download_paper")
async def download_paper(paper_url: str, time_folder: str = None):
    try:
        # 시간별 폴더가 지정된 경우 해당 폴더에 저장
        if time_folder:
            time_pdf_processor = PDFProcessor(time_folder=time_folder)
            result = await time_pdf_processor.download_and_process(paper_url)
        else:
            # 기본 PDF 프로세서 사용
            result = await pdf_processor.download_and_process(paper_url)
        
        if result['success']:
            # 데이터베이스에서 해당 논문 찾기
            papers = await paper_db.get_papers(limit=1000)
            for paper in papers:
                if paper['url'] == paper_url:
                    # 파일 경로 업데이트
                    await paper_db.update_paper_file_path(paper['id'], result['file_path'])
                    break
            
            return {
                "success": True,
                "filename": result['filename'],
                "file_path": result['file_path'],
                "message": "PDF 다운로드 완료"
            }
        else:
            return {
                "success": False,
                "error": result['error']
            }
            
    except Exception as e:
        logging.error(f"PDF 다운로드 중 오류: {e}")
        return {
            "success": False,
            "error": str(e)
        }

# 논문 삭제
@app.delete("/papers/{paper_id}")
async def delete_paper(paper_id: int):
    try:
        await paper_db.delete_paper(paper_id)
        return {"message": "논문이 삭제되었습니다"}
    except Exception as e:
        logging.error(f"논문 삭제 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 논문 검색 (저장된 논문에서)
@app.get("/search")
async def search_papers(query: str):
    try:
        papers = await paper_db.search_papers(query)
        return papers
    except Exception as e:
        logging.error(f"논문 검색 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 서버 상태 확인
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "서버가 정상적으로 실행 중입니다"} 
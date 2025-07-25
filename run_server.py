#!/usr/bin/env python3
"""
논문 수집 MCP 서버 실행 스크립트
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from server.main import app
import uvicorn

def load_config():
    """설정 파일 로드"""
    config_path = project_root / "config" / "settings.json"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        print(f"Warning: Config file not found at {config_path}")
        return {}

def setup_logging(config):
    """로깅 설정"""
    log_config = config.get('logging', {})
    log_level = getattr(logging, log_config.get('level', 'INFO'))
    
    # 로그 포맷 설정
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # 파일 핸들러 설정
    if log_config.get('file'):
        log_file = project_root / log_config['file']
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(log_format))
        
        # 루트 로거에 핸들러 추가
        logging.getLogger().addHandler(file_handler)
    
    # 콘솔 핸들러 설정
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))
    logging.getLogger().addHandler(console_handler)
    
    # 로그 레벨 설정
    logging.getLogger().setLevel(log_level)

def main():
    """메인 함수"""
    print("=" * 50)
    print("논문 수집 MCP 서버 시작")
    print("=" * 50)
    
    # 설정 로드
    config = load_config()
    
    # 로깅 설정
    setup_logging(config)
    
    # 서버 설정
    server_config = config.get('server', {})
    host = server_config.get('host', '0.0.0.0')
    port = server_config.get('port', 8000)
    debug = server_config.get('debug', False)
    
    print(f"서버 설정:")
    print(f"  - 호스트: {host}")
    print(f"  - 포트: {port}")
    print(f"  - 디버그 모드: {debug}")
    print()
    
    # 필요한 디렉토리 생성
    papers_dir = project_root / "papers"
    papers_dir.mkdir(exist_ok=True)
    print(f"논문 저장 디렉토리: {papers_dir}")
    print()
    
    try:
        # 서버 시작
        print("서버를 시작합니다...")
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n서버를 종료합니다...")
    except Exception as e:
        print(f"서버 실행 중 오류 발생: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
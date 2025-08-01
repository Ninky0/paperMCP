# 📚 PaperMCP - 논문 수집 MCP 서버

논문 수집을 자동화하는 Model Context Protocol (MCP) 서버입니다. arXiv, PubMed 등 다양한 소스에서 논문을 검색하고, PDF 파일을 자동으로 다운로드하여 체계적으로 관리할 수 있습니다.

## 🚀 빠른 시작

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 서버 실행
```bash
python run_server.py
```
✅ 서버가 `http://localhost:8001`에서 실행됩니다.

### 3. 논문 수집 + PDF 다운로드
```bash
# 방법 1: 즉시 수집 (추천)
python simple_collect.py

# 방법 2: 자동 스케줄러 (매일 오전 9시 자동 실행)
python auto_collector.py

# 방법 3: 기존 논문 PDF 다운로드
python test_download.py
```

## 📁 프로젝트 구조

```
paperMCP/
├── tools/                     # 논문 수집 도구들
│   ├── arxiv_collector.py     # arXiv 논문 수집기
│   ├── pubmed_collector.py    # PubMed 논문 수집기
│   └── pdf_processor.py       # PDF 다운로드/처리기
├── database/                  # 데이터베이스 관리
│   └── paper_db.py           # 논문 정보 저장/관리 (SQLite)
├── config/                    # 설정 파일
│   └── settings.json         # 서버 설정
├── papers/                    # 다운로드된 PDF 저장소
│   ├── 20241201_090000/      # 시간별 폴더 (YYYYMMDD_HHMMSS)
│   ├── 20241201_150000/      # 각 실행마다 별도 폴더 생성
│   └── ...
├── run_server.py             # MCP 서버 실행
├── simple_collect.py         # 간단한 논문 수집
├── auto_collector.py         # 자동 스케줄러
├── test_download.py          # PDF 다운로드 테스트
├── papers.db                 # SQLite 데이터베이스
├── requirements.txt          # Python 의존성
└── README.md                 # 프로젝트 문서
```

## 🎯 주요 기능

### 📖 논문 수집
- **arXiv**: 컴퓨터 과학, 수학, 물리학 등 다양한 분야
- **PubMed**: 생명과학, 의학 분야 논문
- **키워드 검색**: 원하는 키워드로 논문 검색
- **저자별 검색**: 특정 저자의 논문 검색

### 📥 자동 PDF 다운로드
- **자동 다운로드**: 논문 PDF 파일 자동 다운로드
- **메타데이터 추출**: 제목, 저자, 초록 등 자동 추출
- **시간별 폴더**: 실행 시간별로 폴더를 생성하여 논문 구분 저장
- **파일 관리**: 체계적인 폴더 구조로 저장

### 🔄 자동화
- **일일 자동 수집**: 매일 오전 9시에 자동으로 논문 수집
- **키워드 설정**: 관심 있는 키워드별로 자동 수집
- **중복 제거**: 이미 수집된 논문은 자동으로 제외
- **시간별 구분**: 각 실행마다 `YYYYMMDD_HHMMSS` 형식의 폴더를 생성하여 논문을 구분 저장

## 🔧 API 사용법

### 기본 엔드포인트
- `GET /` - 서버 상태 확인
- `POST /search_papers` - 논문 검색
- `GET /papers` - 저장된 논문 목록
- `POST /download_paper` - 논문 다운로드
- `DELETE /papers/{id}` - 논문 삭제

### 논문 검색 예시
```bash
curl -X POST "http://localhost:8001/search_papers" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning",
    "max_results": 10,
    "source": "arxiv"
  }'
```

### Python 클라이언트 예시
```python
import requests

# 논문 검색
response = requests.post("http://localhost:8001/search_papers", json={
    "query": "deep learning",
    "max_results": 5,
    "source": "arxiv"
})

papers = response.json()
print(f"Found {len(papers)} papers")

# 논문 다운로드
for paper in papers:
    if paper.get('pdf_url'):
        download_response = requests.post("http://localhost:8001/download_paper", 
                                        params={"paper_url": paper['url']})
        print(f"Downloaded: {paper['title']}")
```

## ⚙️ 설정

### config/settings.json
```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8001
  },
  "download": {
    "directory": "papers",
    "max_file_size_mb": 100
  },
  "search": {
    "default_max_results": 10
  }
}
```

### 자동 수집 설정
`auto_collector.py`에서 키워드와 설정을 수정할 수 있습니다:

```python
self.keywords = [
    "machine learning",
    "deep learning", 
    "artificial intelligence"
]

self.keyword_configs = {
    "machine learning": {"max_results": 5, "source": "arxiv"},
    "deep learning": {"max_results": 5, "source": "arxiv"}
}
```

## 🔄 자동화

### 1. 일일 자동 수집
```bash
# 스케줄러 실행 (매일 오전 9시 자동 수집)
python auto_collector.py

# 즉시 수집만 실행
python auto_collector.py collect

# 주간 요약만 실행
python auto_collector.py summary
```

### 2. Windows 작업 스케줄러
1. 작업 스케줄러 열기
2. "기본 작업 만들기" 클릭
3. 프로그램/스크립트: `python`
4. 인수 추가: `auto_collector.py collect`
5. 매일 실행으로 설정

### 3. Linux cron
```bash
# crontab 편집
crontab -e

# 매일 오전 9시에 실행
0 9 * * * cd /path/to/paperMCP && python auto_collector.py collect
```

## 🎯 사용 시나리오

### 회사에서 매일 사용
1. `python run_server.py` (서버 실행)
2. `python auto_collector.py` (자동 스케줄러 시작)
3. 매일 오전 9시에 자동으로 논문 수집 + PDF 다운로드

### 즉시 수집이 필요한 경우
1. `python run_server.py` (서버 실행)
2. `python simple_collect.py` (즉시 수집)

### 기존 논문 PDF만 다운로드
1. `python run_server.py` (서버 실행)
2. `python test_download.py` (PDF 다운로드)

## 📊 결과 확인

- **수집된 논문**: `papers.db` (SQLite 데이터베이스)
- **다운로드된 PDF**: `papers/` 폴더
- **로그 파일**: `paper_mcp.log`, `auto_collector.log`

### 통계 확인
```python
import requests

# 저장된 논문 수 확인
response = requests.get("http://localhost:8001/papers")
papers = response.json()
print(f"총 {len(papers)}개 논문 저장됨")

# 소스별 통계
sources = {}
for paper in papers:
    source = paper['source']
    sources[source] = sources.get(source, 0) + 1

for source, count in sources.items():
    print(f"{source}: {count}개")
```

## 🛠️ 문제 해결

### 서버가 시작되지 않는 경우
1. 포트 8001이 사용 중인지 확인
2. 의존성 패키지 설치 확인: `pip install -r requirements.txt`
3. Python 버전 확인 (3.7 이상 필요)

### 논문 검색이 안 되는 경우
1. 인터넷 연결 확인
2. arXiv/PubMed 서버 상태 확인
3. 방화벽 설정 확인

### PDF 다운로드가 안 되는 경우
1. 디스크 공간 확인
2. 파일 권한 확인
3. 네트워크 연결 확인

## 🔒 보안 고려사항

1. **로컬 사용**: 현재 서버는 로컬에서만 실행되도록 설계됨
2. **방화벽**: 외부 접근을 차단하려면 방화벽 설정
3. **백업**: 정기적으로 데이터베이스 백업 권장

## 💊 지원

문제가 발생하면 다음을 확인하세요:
1. 로그 파일 확인
2. 서버 상태 확인
3. 네트워크 연결 확인
4. 의존성 패키지 버전 확인

## 📄 라이선스

MIT License

## 🤝 기여

이슈 리포트나 풀 리퀘스트를 통해 기여해주세요.

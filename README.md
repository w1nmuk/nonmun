# 📚 논문 검색기

arXiv 논문을 검색하고 제목·저자·원문 초록을 확인한 뒤 Markdown으로 저장하는 Streamlit MVP입니다.

## 실행

Python 3.12 기준입니다.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

검색어와 논문 개수(1~10개)를 입력하고 **논문 검색**을 누르세요. 관련도순 결과를 읽고 **Markdown 다운로드**로 저장할 수 있습니다. 다운로드나 화면 재실행 시에도 마지막 검색 결과를 유지합니다.

## MVP 범위

- 검색 한 번당 arXiv HTTPS 요청 한 번, 연결·응답 대기 시간 제한 15초
- 같은 검색어·개수는 5분간 캐시(최대 100개 검색), 폼 제출 때만 검색
- 검색 결과 없음과 연결 실패·요청 제한·잘못된 응답을 구분해 안내
- Markdown 생성·다운로드에는 추가 API 호출 없음
- 인용수 필터와 자동 번역은 MVP에서 제외: 논문별 외부 요청과 강제 대기로 생기던 지연을 없애고 검색·읽기·저장에 집중

외부 연결은 `export.arxiv.org`의 HTTPS API가 필요합니다. API 키는 필요 없습니다. 클라우드에서는 해당 도메인을 네트워크 허용 목록에 추가하세요. 실제 논문 링크는 `arxiv.org`로 열립니다. arXiv 장애나 요청 제한이 있으면 오류를 표시하며, 오류를 결과 없음으로 숨기지 않습니다.

## 테스트

프로젝트 루트에서 실행합니다. 외부 API를 대체해 재현 가능한 응답으로 검색·오류 처리와 화면 동작을 검사합니다.

```bash
python -m unittest discover -s tests -v
```

테스트 통과는 실제 arXiv 연결 성공을 뜻하지 않습니다. 실제 연결 확인:

```bash
python -c "from arxiv_engine import fetch_arxiv_base; print(fetch_arxiv_base('transformer', max_results=1))"
```

## 구성

- `app.py`: 검색 폼, 캐시, 결과 유지, 화면·다운로드
- `arxiv_engine.py`: arXiv 검색·응답 검사, 네트워크 없는 Markdown 생성
- `tests/`: API 클라이언트와 Streamlit 화면 회귀 테스트

# arxiv_engine.py
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
from deep_translator import GoogleTranslator

def fetch_arxiv_base(query, start_index=0, max_results=30):
    """arXiv API에서 논문을 가져옵니다."""
    safe_query = urllib.parse.quote(query)
    url = f'http://export.arxiv.org/api/query?search_query=all:{safe_query}&start={start_index}&max_results={max_results}'
    try:
        response = urllib.request.urlopen(url)
        root = ET.fromstring(response.read())
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        papers = []
        for entry in root.findall('atom:entry', ns):
            title = entry.find('atom:title', ns).text.strip().replace('\n', ' ')
            link = entry.find('atom:id', ns).text
            summary = entry.find('atom:summary', ns).text.strip().replace('\n', ' ')
            authors = [author.find('atom:name', ns).text for author in entry.findall('atom:author', ns)]
            papers.append({
                'title': title,
                'summary': summary,
                'authors': ", ".join(authors),
                'link': link,
                'citationCount': 0
            })
        return papers
    except Exception:
        return []

def get_citation_by_title(title):
    """Semantic Scholar에서 인용수를 가져옵니다."""
    safe_title = urllib.parse.quote(title)
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={safe_title}&limit=1&fields=citationCount"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req)
        json_data = json.loads(response.read().decode('utf-8'))
        papers = json_data.get('data', [])
        if papers:
            return papers[0].get('citationCount') or 0
        return 0
    except Exception:
        return 0

def create_markdown_content(papers, keyword):
    """결과물을 마크다운 텍스트로 변환하고 번역합니다."""
    translator = GoogleTranslator(source='en', target='ko')
    content = f"# 🔍 '{keyword}' 관련 우수 논문 리스트\n\n"

    for i, paper in enumerate(papers, 1):
        try:
            kr_title = translator.translate(paper['title'])
            kr_summary = translator.translate(paper['summary'])
        except:
            kr_title = "번역 실패"
            kr_summary = "번역 실패"

        content += f"## {i}. {paper['title']}\n"
        content += f"### 🇰🇷 {kr_title}\n\n"
        content += f"* **⭐ 인용수:** {paper['citationCount']}회\n"
        content += f"* **저자:** {paper['authors']}\n"
        content += f"* **링크:** [arXiv에서 보기]({paper['link']})\n\n"
        content += f"**📑 초록 요약 (번역):**\n> {kr_summary}\n\n"
        content += f"**📄 원문 (Original):**\n> {paper['summary']}\n\n---\n\n"
    return content
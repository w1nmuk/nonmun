"""Small arXiv client and offline Markdown export."""

import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET


class SearchError(Exception):
    """A search could not complete; this is different from an empty result."""


def fetch_arxiv_base(query, max_results=5):
    """Fetch at most ten papers in one bounded HTTPS request."""
    query = query.strip()
    if not query:
        raise ValueError("검색어를 입력해 주세요.")
    if not 1 <= max_results <= 10:
        raise ValueError("논문 개수는 1~10개로 설정해 주세요.")

    params = urllib.parse.urlencode({
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
    })
    request = urllib.request.Request(
        f"https://export.arxiv.org/api/query?{params}",
        headers={"User-Agent": "nonmun-paper-reader/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            root = ET.fromstring(response.read())
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            message = "arXiv 요청이 많습니다. 잠시 후 다시 검색해 주세요."
        else:
            message = f"arXiv 검색 요청에 실패했습니다 (HTTP {exc.code}). 잠시 후 다시 시도해 주세요."
        raise SearchError(message) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise SearchError("arXiv에 연결할 수 없습니다. 네트워크를 확인하고 다시 시도해 주세요.") from exc
    except ET.ParseError as exc:
        raise SearchError("arXiv 응답을 읽을 수 없습니다. 잠시 후 다시 시도해 주세요.") from exc

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    if root.tag != "{http://www.w3.org/2005/Atom}feed":
        raise SearchError("arXiv 응답 형식이 올바르지 않습니다.")
    papers = []
    for entry in root.findall("atom:entry", ns):
        link = entry.findtext("atom:id", default="", namespaces=ns)
        if link.startswith(("http://arxiv.org/api/errors", "https://arxiv.org/api/errors")):
            raise SearchError("arXiv가 검색어를 처리하지 못했습니다. 검색어를 확인해 주세요.")
        title = entry.findtext("atom:title", default="", namespaces=ns)
        summary = entry.findtext("atom:summary", default="", namespaces=ns)
        if not title.strip() or not summary.strip() or not link:
            raise SearchError("arXiv 응답에 논문 정보가 누락되었습니다.")
        # Only expose canonical paper links supplied by arXiv.
        parsed = urllib.parse.urlsplit(link)
        if parsed.hostname != "arxiv.org" or not parsed.path.startswith("/abs/"):
            raise SearchError("arXiv 응답에 올바르지 않은 논문 링크가 있습니다.")
        authors = [
            " ".join(author.findtext("atom:name", default="", namespaces=ns).split())
            for author in entry.findall("atom:author", ns)
        ]
        papers.append({
            "title": " ".join(title.split()),
            "summary": " ".join(summary.split()),
            "authors": ", ".join(authors),
            "link": f"https://arxiv.org{parsed.path}",
        })
    return papers[:max_results]


def create_markdown_content(papers, keyword):
    """Export the displayed papers without further network requests."""
    content = [f"# '{keyword}' 관련 논문\n"]
    for index, paper in enumerate(papers, 1):
        content.extend([
            f"## {index}. {paper['title']}\n",
            f"- **저자:** {paper['authors']}",
            f"- **링크:** {paper['link']}\n",
            f"{paper['summary']}\n",
        ])
    return "\n".join(content)

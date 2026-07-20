import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
import time

def fetch_arxiv_base(query, start_index=0, max_results=30):
    """
    arXiv에서 논문을 가져옵니다.
    start_index를 조절하여 다음 페이지의 논문을 이어서 가져올 수 있습니다.
    """
    safe_query = urllib.parse.quote(query)
    # start 매개변수를 동적으로 변경하여 페이지네이션 구현
    url = f'http://export.arxiv.org/api/query?search_query=all:{safe_query}&start={start_index}&max_results={max_results}'

    try:
        response = urllib.request.urlopen(url)
        root = ET.fromstring(response.read())
        ns = {'atom': 'http://www.w3.org/2005/Atom'}

        papers = []
        for entry in root.findall('atom:entry', ns):
            title = entry.find('atom:title', ns).text.strip().replace('\n', ' ')
            link = entry.find('atom:id', ns).text
            authors = [author.find('atom:name', ns).text for author in entry.findall('atom:author', ns)]

            papers.append({
                'title': title,
                'authors': ", ".join(authors),
                'link': link,
                'citationCount': 0
            })
        return papers
    except Exception as e:
        print(f"arXiv 검색 중 에러가 발생했습니다: {e}")
        return []

def get_citation_by_title(title):
    """
    Semantic Scholar에서 제목으로 인용수를 가져옵니다.
    """
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

def main():
    print("=" * 75)
    print("   딥 서치 논문 검색기 (페이지네이션 지원 및 메모리 최적화)")
    print("=" * 75)

    # 튜닝 가능한 변수들
    TARGET_PAPER_COUNT = 5     # 최종적으로 찾고 싶은 논문 개수
    MIN_CITATIONS = 5          # 최소 인용수 커트라인
    MAX_SEARCH_LIMIT = 120     # 최대 검사할 논문 개수 (무한 대기 방지용 안전장치)
    BATCH_SIZE = 30            # 한 번에 arXiv에서 가져올 논문 개수

    while True:
        user_input = input("\n검색할 키워드를 입력하세요 (종료: 'q'): ").strip()

        if user_input.lower() == 'q':
            print("\n프로그램을 종료합니다. 수고하셨습니다!")
            break

        if not user_input:
            continue

        qualified_papers = []  # 조건을 통과한 논문만 저장할 리스트 (메모리 절약)
        current_start = 0      # arXiv 탐색 시작 위치
        total_checked = 0      # 지금까지 검사한 총 논문 개수

        print(f"\n[{user_input}] 관련 논문을 목표치({TARGET_PAPER_COUNT}개)만큼 찾을 때까지 딥 서치를 시작합니다...\n")

        # 목표 개수를 채우거나, 검사 한계선에 도달할 때까지 계속 반복(While)합니다.
        while len(qualified_papers) < TARGET_PAPER_COUNT and total_checked < MAX_SEARCH_LIMIT:
            print(f"🔄 arXiv에서 {current_start+1}번째부터 {current_start+BATCH_SIZE}번째 후보군을 가져옵니다...")

            candidate_papers = fetch_arxiv_base(user_input, start_index=current_start, max_results=BATCH_SIZE)

            # 더 이상 arXiv에 검색되는 논문이 없으면 루프를 완전히 탈출합니다.
            if not candidate_papers:
                print("⚠️ arXiv에 더 이상 관련 논문이 없습니다. 탐색을 종료합니다.")
                break

            for paper in candidate_papers:
                # 안전장치: 최대 한계선에 도달하면 즉시 중단
                if total_checked >= MAX_SEARCH_LIMIT:
                    break

                time.sleep(1) # API 차단 방지
                total_checked += 1

                citation = get_citation_by_title(paper['title'])
                print(f"  > [누적 검사: {total_checked}/{MAX_SEARCH_LIMIT}] 인용수: {citation}회")

                # 인용수 미달 시 버림 (메모리 최적화 핵심)
                if citation < MIN_CITATIONS:
                    continue

                paper['citationCount'] = citation
                qualified_papers.append(paper)
                print(f"    ✅ 합격! (현재 {len(qualified_papers)}/{TARGET_PAPER_COUNT}개 수집됨)")

                # 목표치 달성 시 루프 조기 종료
                if len(qualified_papers) >= TARGET_PAPER_COUNT:
                    break

            # 다음 페이지를 위해 시작 위치를 증가시킵니다.
            current_start += BATCH_SIZE

        # --- 검사 결과 처리 ---
        if not qualified_papers:
            print(f"\n❌ 총 {total_checked}개의 논문을 검사했지만, 조건(인용수 {MIN_CITATIONS}회)을 만족하는 논문을 찾지 못했습니다.")
            continue

        if len(qualified_papers) < TARGET_PAPER_COUNT:
            print(f"\n⚠️ 목표치에 도달하지 못하고 한계선({MAX_SEARCH_LIMIT}개)에 도달하여, 지금까지 찾은 논문만 출력합니다.")
        else:
            print(f"\n🎯 성공적으로 우수 논문 {TARGET_PAPER_COUNT}개를 모두 찾았습니다!")

        qualified_papers.sort(key=lambda x: x['citationCount'], reverse=True)

        print("\n" + "=" * 60)
        for i, paper in enumerate(qualified_papers, 1):
            print(f"[{i}] 제목: {paper['title']}")
            print(f"    ⭐ 인용수: {paper['citationCount']}회")
            print(f"    저자: {paper['authors']}")
            print(f"    링크: {paper['link']}\n")
            print("-" * 60)

if __name__ == "__main__":
    main()
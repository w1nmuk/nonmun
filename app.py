# app.py
import time
import streamlit as st

# 우리가 분리한 핵심 엔진에서 필요한 함수들만 쏙쏙 불러옵니다!
from arxiv_engine import fetch_arxiv_base, get_citation_by_title, create_markdown_content

def main():
    st.set_page_config(page_title="논문 검색 봇", page_icon="📚", layout="wide")
    st.title("📚 나만의 딥 서치 논문 리더기")
    st.markdown("arXiv와 Semantic Scholar를 교차 검증하여 영향력 있는 논문만 찾아 번역해 줍니다.")

    st.sidebar.header("⚙️ 검색 설정")
    target_count = st.sidebar.slider("찾을 논문 개수", 1, 10, 5)
    min_citations = st.sidebar.slider("최소 인용수 기준", 0, 100, 5)
    max_search_limit = st.sidebar.slider("최대 탐색 한계선", 30, 300, 120)

    query = st.text_input("🔍 검색할 키워드를 입력하세요 (예: neuromorphic computing, FPGA)")

    if st.button("논문 검색 시작"):
        if not query:
            st.warning("키워드를 입력해 주세요.")
            return

        st.info(f"'{query}' 관련 논문을 찾고 있습니다. (인용수 필터링 중...)")

        progress_bar = st.progress(0)
        status_text = st.empty()

        batch_size = 30
        qualified_papers = []
        current_start = 0
        total_checked = 0

        # 외부에서 불러온 함수(fetch_arxiv_base)를 마치 내 파일에 있는 것처럼 사용합니다.
        while len(qualified_papers) < target_count and total_checked < max_search_limit:
            candidate_papers = fetch_arxiv_base(query, start_index=current_start, max_results=batch_size)
            if not candidate_papers:
                break

            for paper in candidate_papers:
                if total_checked >= max_search_limit or len(qualified_papers) >= target_count:
                    break

                time.sleep(1)
                total_checked += 1

                progress = min(total_checked / max_search_limit, 1.0)
                progress_bar.progress(progress)
                status_text.text(f"검사 진행 중: {total_checked}개 완료 / 합격: {len(qualified_papers)}개")

                # 외부에서 불러온 함수(get_citation_by_title) 사용
                citation = get_citation_by_title(paper['title'])
                if citation < min_citations:
                    continue

                paper['citationCount'] = citation
                qualified_papers.append(paper)

            current_start += batch_size

        progress_bar.empty()
        status_text.empty()

        if not qualified_papers:
            st.error("조건에 맞는 논문을 찾지 못했습니다. 검색어나 기준을 변경해 보세요.")
        else:
            qualified_papers.sort(key=lambda x: x['citationCount'], reverse=True)
            st.success(f"🎉 총 {len(qualified_papers)}개의 훌륭한 논문을 찾았습니다!")

            # 외부에서 불러온 함수(create_markdown_content) 사용
            md_content = create_markdown_content(qualified_papers, query)
            st.download_button(
                label="📝 결과 마크다운(.md) 파일 다운로드",
                data=md_content,
                file_name=f"{query.replace(' ', '_')}_papers.md",
                mime="text/markdown"
            )

            for i, paper in enumerate(qualified_papers, 1):
                with st.expander(f"[{i}] {paper['title']} (⭐ {paper['citationCount']}회)"):
                    st.write(f"**저자:** {paper['authors']}")
                    st.write(f"**링크:** [보러가기]({paper['link']})")
                    st.markdown("---")
                    st.write("**원문 초록:**")
                    st.info(paper['summary'])

if __name__ == "__main__":
    main()
"""Search, read and export papers with a single arXiv request."""

import streamlit as st

from arxiv_engine import SearchError, create_markdown_content, fetch_arxiv_base


@st.cache_data(ttl=300, max_entries=100, show_spinner=False)
def search_papers(query, count):
    return fetch_arxiv_base(query, max_results=count)


def main():
    st.set_page_config(page_title="논문 검색기", page_icon="📚", layout="wide")
    st.title("📚 논문 검색기")
    st.write("arXiv 논문을 검색하고 원문 초록을 읽거나 Markdown으로 저장하세요.")

    with st.form("search"):
        query = st.text_input("검색어", placeholder="예: neuromorphic computing, FPGA")
        count = st.slider("찾을 논문 개수", 1, 10, 5)
        submitted = st.form_submit_button("논문 검색")

    if submitted:
        query = query.strip()
        # Never show results from an older query as the current search result.
        st.session_state.pop("search_result", None)
        if not query:
            st.warning("검색어를 입력해 주세요.")
        else:
            try:
                with st.spinner("논문을 검색하고 있습니다…"):
                    papers = search_papers(query, count)
                st.session_state.search_result = {"query": query, "papers": papers}
            except SearchError as exc:
                st.error(str(exc))

    result = st.session_state.get("search_result")
    if result is None:
        return
    papers = result["papers"]
    st.subheader(f"검색 결과: {result['query']}")
    if not papers:
        st.info("검색 결과가 없습니다. 다른 검색어를 입력해 주세요.")
        return

    st.caption(f"관련도순 {len(papers)}개 · 원문 초록")
    st.download_button(
        "Markdown 다운로드",
        data=create_markdown_content(papers, result["query"]),
        file_name="papers.md",
        mime="text/markdown",
        on_click="ignore",
    )
    for paper in papers:
        with st.expander(paper["title"], expanded=True):
            st.text(f"저자: {paper['authors']}")
            st.link_button("arXiv에서 보기", paper["link"])
            st.text(paper["summary"])


if __name__ == "__main__":
    main()

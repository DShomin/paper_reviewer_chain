import arxiv
import streamlit as st
import pandas as pd

# Construct the default API client.
client = arxiv.Client()


def search_arxiv(query):
    search = arxiv.Search(
        query=query,
        max_results=10,
        sort_by=arxiv.SortCriterion.Relevance,
    )

    results = client.results(search)

    return list(results)


def split_id_from_url(url):
    try:
        # PDF URL에서 ID 추출
        # 예: 'https://arxiv.org/pdf/1706.03762.pdf' -> '1706.03762'
        parts = url.split("/")
        raw_id = parts[-1]

        # .pdf 확장자가 있으면 제거
        if raw_id.endswith(".pdf"):
            raw_id = raw_id[:-4]

        # 버전 정보 (예: v1, v2) 제거
        if "v" in raw_id and raw_id.split("v")[-1].isdigit():
            raw_id = raw_id.split("v")[0]

        return raw_id
    except Exception:
        # URL 파싱 중 오류 발생 시 원본 URL 반환
        st.warning(f"ArXiv ID 추출 중 오류가 발생했습니다: {url}")
        return url.split("/")[-1]


def regist_arxive_id(arxiv_id):

    st.session_state.axiv_id.append(arxiv_id)


def on_change_interest_paper_list(arxiv_id):
    if arxiv_id in st.session_state.interest_paper_list:
        st.session_state.interest_paper_list.remove(arxiv_id)
        df = pd.read_csv(f"./data/paper_csv/paper.csv")
        df = df[df["arxiv_id"] != arxiv_id]
        df.to_csv(f"./data/paper_csv/paper.csv", index=False)
    else:
        regist_arxive_id(arxiv_id)


# Streamlit app
def display_arxiv_results(results, summary=False):
    st.subheader("Arxiv 논문 검색 결과")

    # Display results in cards
    for i, paper in enumerate(results):
        with st.container(border=True):
            if summary:
                st.markdown(
                    f"""
### {paper.title}
Authors: {', '.join(author.name for author in paper.authors)}
**Published**: {paper.published.strftime('%Y-%m-%d')}

**Summary**: {paper.summary}
"""
                )
            else:
                st.markdown(
                    f"""
### {paper.title}
Authors: {', '.join(author.name for author in paper.authors)}
**Published**: {paper.published.strftime('%Y-%m-%d')}

**Summary**: {paper.summary[:200]}...
"""
                )
            col1, col2 = st.columns([0.4, 2])
            with col1:
                st.link_button("Go pdf", paper.pdf_url)

            with col2:
                arxive_id = split_id_from_url(paper.pdf_url)
                st.toggle(
                    "Interest",
                    value=(
                        True
                        if arxive_id in st.session_state.interest_paper_list
                        else False
                    ),
                    key=arxive_id,
                    on_change=on_change_interest_paper_list,
                    args=(arxive_id,),
                )

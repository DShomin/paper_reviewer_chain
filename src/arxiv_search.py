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

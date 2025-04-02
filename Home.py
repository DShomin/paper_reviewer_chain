import streamlit as st
import pandas as pd
import os
import json
from src.arxiv_search import search_arxiv, display_arxiv_results
from src.translator import translate
from src.utils import load_csv
from langchain_community.document_loaders import ArxivLoader


def load_arxiv(arxiv_id, with_meta=True):
    loader = ArxivLoader(arxiv_id, load_all_available_meta=with_meta)
    return loader.load()


def dataframe_with_selections(df):
    df_with_selections = df.copy()
    df_with_selections.insert(0, "Select", False)

    edited_df = st.data_editor(
        df_with_selections,
        hide_index=True,
        column_config={"Select": st.column_config.CheckboxColumn(required=True)},
        disabled=df.columns,
    )

    selected_rows = edited_df[edited_df.Select]

    return selected_rows.drop(columns=["Select"])


def save_paper_to_csv(arxiv_id, arxiv_data):
    if os.path.exists(f"./data/paper_csv/paper.csv"):
        df = pd.read_csv(f"./data/paper_csv/paper.csv")

        if arxiv_id in df["arxiv_id"].values:
            st.write("이미 저장된 논문입니다.")
            return
        else:
            new_df = pd.json_normalize(arxiv_data[0].dict()["metadata"])
            new_df["arxiv_id"] = arxiv_id
            df = pd.concat([df, new_df])
            df.to_csv(f"./data/paper_csv/paper.csv", index=False)
    else:
        df = pd.json_normalize(arxiv_data[0].dict()["metadata"])
        df["arxiv_id"] = arxiv_id
        df.to_csv(f"./data/paper_csv/paper.csv", index=False)


def handle_arxiv_search(query):
    results = search_arxiv(query)
    summary_button = st.checkbox("Full Summary", False)

    if st.button("검색"):
        if results:
            display_arxiv_results(results, summary_button)
        else:
            st.write("검색 결과가 없습니다. 다른 검색어를 입력해주세요.")

    if st.session_state.axiv_id is not None:
        for arxiv_id in st.session_state.axiv_id:
            arxiv_data = load_arxiv(arxiv_id)
            save_paper_to_csv(arxiv_id, arxiv_data)


def handle_interesting_papers(df):
    selected_df = dataframe_with_selections(df)

    for i, (title, abstract, arxiv_id) in enumerate(
        selected_df[["Title", "Summary", "arxiv_id"]].values
    ):
        with st.container(border=True):
            st.markdown(f"### {i+1}. {title} abstract")
            st.markdown(abstract)
            col = st.columns([1, 2])
            with col[0]:
                trans_button = st.button("Translate abstract", key=f"trans_{i}")
            with col[1]:
                target_lang = st.selectbox(
                    "Target Language", ["ko", "en"], key=f"t_lang_{i}"
                )
            file_name = f"./data/paper_csv/{arxiv_id}_{target_lang}.json"
            translated_abstract = None
            if os.path.exists(file_name):
                with open(file_name, "r", encoding="utf-8-sig") as f:
                    translated_abstract = json.loads(f.read())["translated"]  # type: ignore
                st.expander("Translated Abstract").markdown(translated_abstract)

            else:
                if trans_button:
                    # load translated abstract
                    translated_abstract = translate(abstract, target_lang)  # type: ignore
                    st.expander("Translated Abstract", expanded=True).markdown(
                        translated_abstract
                    )

                    # save translated abstract as json
                    translated_abstract = {
                        "source": abstract,
                        "translated": translated_abstract,
                    }
                    with open(file_name, "w", encoding="UTF-8-sig") as f:
                        f.write(json.dumps(translated_abstract, ensure_ascii=False))

            if st.button("Search on Youtube", key=f"you_{i}", use_container_width=True):
                data = {
                    "title": title,
                    "arxiv_id": arxiv_id,
                }
                st.session_state.paper_data = data
                st.switch_page("./pages/🎥 YouTube Search.py")

            if st.button("Go to Review Page", key=f"re_{i}", use_container_width=True):
                # pass data
                data = {
                    "df": selected_df,
                    "translated_abstract": translated_abstract,
                }
                st.session_state.paper_data = data
                st.switch_page("./pages/📄 Review page.py")


if "axiv_id" not in st.session_state:
    st.session_state.axiv_id = []

st.set_page_config(
    page_title="Review Paper Home",
    page_icon="🏠",
)

st.markdown(
    """
# 논문 리뷰 페이지

> 이 페이지는 유튜브 리뷰 영상과 Arxiv 논문을 통합하여 최신 연구 내용을 쉽게 이해할 수 있도록 도와드립니다. 주요 기능은 다음과 같습니다:

- **유튜브 리뷰 음성 변환**: 유튜브 리뷰 영상을 텍스트로 변환하여 제공합니다.
- **논문 요약 제공**: Arxiv 논문의 핵심 내용을 요약해 제공합니다.
- **AI 기반 Q&A**: 논문과 리뷰에 대한 질문에 AI가 상세한 답변을 제공합니다.

논문 내용을 빠르게 이해하고, 궁금한 점을 해결하세요.
"""
)

df = load_csv()
interest_paper_list = df["arxiv_id"].values.tolist()
st.session_state.interest_paper_list = interest_paper_list

with st.container(border=True):
    st.markdown("## Arxiv Search")

    # get user query for arxiv search
    query = st.text_input("Arxiv에서 검색할 검색어를 입력하세요:")
    handle_arxiv_search(query)

with st.container(border=True):
    st.markdown("## Interesting Papers")
    handle_interesting_papers(df)

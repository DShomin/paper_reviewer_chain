from langchain.schema import Document
import json
import os
import pandas as pd
import streamlit as st
from typing import Iterable


def save_docs_to_jsonl(array: Iterable[Document], file_path: str) -> None:
    # 파일의 디렉토리 경로를 추출하고 필요한 경우 생성
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

    with open(file_path, "w") as jsonl_file:
        for doc in array:
            jsonl_file.write(doc.json() + "\n")


def load_docs_from_jsonl(file_path) -> Iterable[Document]:
    array = []
    with open(file_path, "r") as jsonl_file:
        for line in jsonl_file:
            data = json.loads(line)
            obj = Document(**data)
            array.append(obj)
    return array


def load_csv():
    if os.path.exists(f"./data/paper_csv/paper.csv"):
        df = pd.read_csv(f"./data/paper_csv/paper.csv")
    else:
        # 디렉토리가 없으면 생성
        os.makedirs("./data/paper_csv", exist_ok=True)
        st.warning("관심 논문이 없습니다. 논문을 검색하여 관심 논문에 추가해주세요.")
        # 기본 컬럼을 가진 빈 DataFrame 생성
        df = pd.DataFrame(columns=["Title", "Summary", "arxiv_id"])
    return df

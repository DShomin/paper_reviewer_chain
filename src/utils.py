from langchain.schema import Document
import json
import os
import pandas as pd
import streamlit as st
from typing import Iterable


def save_docs_to_jsonl(array: Iterable[Document], file_path: str) -> None:
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
        st.write("관심 논문이 없습니다.")
    return df

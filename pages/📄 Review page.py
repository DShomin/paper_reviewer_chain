import os
import json
import streamlit as st
from glob import glob
from langchain.document_loaders import ArxivLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.retrievers import EnsembleRetriever
from langchain_core.runnables import RunnablePassthrough
from src.utils import load_docs_from_jsonl
from langchain.chat_models.openai import ChatOpenAI
from langchain.prompts import PromptTemplate


class ReviewPage:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=250,
            chunk_overlap=50,
            length_function=len,
            is_separator_regex=False,
        )
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

        st.session_state.retriever = None

    def load_markdown(self, title):
        if os.path.exists(f"./data/review_markdown/{title}.md"):
            with open(f"./data/review_markdown/{title}.md", "r") as f:
                return f.read()
        else:
            return f"## {title} Review\n\n"

    def save_markdown(self, md, title):
        with open(f"./data/review_markdown/{title}.md", "w") as f:
            f.write(md)

    def create_vector_db(self, db_file_name, docs):
        if os.path.exists(db_file_name):
            db = FAISS.load_local(
                db_file_name,
                self.embeddings,
                allow_dangerous_deserialization=True,
            )
        else:
            docs = self.text_splitter.split_documents(docs)
            db = FAISS.from_documents(docs, self.embeddings)
            db.save_local(db_file_name)

        return db.as_retriever()

    def create_arxiv_vector_db(self, arxiv_id):
        arxiv_loader = ArxivLoader(arxiv_id)
        docs = arxiv_loader.load()
        db_file_name = f"./data/vector_db/{arxiv_id}_paper_pdf"
        return self.create_vector_db(db_file_name, docs)

    def create_youtube_vector_db(self, db_file_name_youtube, docs):
        st.session_state.youtube_retriever = self.create_vector_db(
            db_file_name_youtube, docs
        )
        return st.session_state.youtube_retriever

    def answer_question(self, question):
        result = self.rag_chain.invoke(question)
        st.markdown(
            f"""
                    ## Answer
                    {result.content}
                    """
        )

    def format_docs(self, docs):
        return "\n\n".join(doc.page_content for doc in docs)

    def setup(self):
        st.set_page_config(
            page_title="Review Paper",
            page_icon="📄",
        )

        df = st.session_state.paper_data["df"]
        col_1, col_2 = st.columns([1, 1], gap="large")

        paper_title = df["Title"].values[0]
        abstract = df["Summary"].values[0]
        arxiv_id = df["arxiv_id"].values[0]

        with col_1:
            md = self.load_markdown(paper_title)
            md = st.text_area("Review를 위한 Markdown을 입력하세요: ", md, height=500)

            if st.button("Markdown 저장"):
                self.save_markdown(md, paper_title)

        if st.button("Paper RAG 생성"):
            st.session_state.paper_retriever = self.create_arxiv_vector_db(arxiv_id)

        with col_2:
            st.write(md)

        with st.container(border=True):
            st.expander("Abstract").markdown(abstract)

        trans_abstract_list = [
            file_ for file_ in glob("./data/paper_csv/*json") if arxiv_id in file_
        ]

        with st.container(border=True):
            for trans_abstract_path in trans_abstract_list:
                with open(trans_abstract_path, "r", encoding="utf-8-sig") as f:
                    translated_abstract = json.loads(f.read())["translated"]  # type: ignore
                st.expander("Translated Abstract").markdown(translated_abstract)

        youtube_trans_list = glob(
            f"./data/youtube_audio/{arxiv_id}/{paper_title}/*json"
        )
        with st.container(border=True):
            for i, trans_path in enumerate(youtube_trans_list):
                docs = load_docs_from_jsonl(trans_path)
                trans = "".join([doc.page_content for doc in docs])
                video_name = trans_path.split("/")[-2]
                st.markdown(f"## Youtube")
                st.expander(video_name, expanded=False).markdown(trans)

                docs = self.text_splitter.split_documents(docs)

                db_file_name_youtube = f"./data/vector_db/{video_name}_youtube_trans"

                st.button(
                    "Youtube RAG 생성",
                    on_click=self.create_youtube_vector_db,  # type: ignore
                    args=(db_file_name_youtube, docs),
                )

        if (
            "paper_retriever" in st.session_state
            and "youtube_retriever" in st.session_state
        ):
            retriever = EnsembleRetriever(
                retrievers=[
                    st.session_state.paper_retriever,
                    st.session_state.youtube_retriever,
                ],
                weights=[0.6, 0.4],
            )
            st.session_state.retriever = retriever
            st.success("Paper retriever와 Youtube retriever를 앙상블하여 사용합니다.")
        elif "paper_retriever" in st.session_state:
            st.warning("Only paper retriever is available.")
            st.session_state.retriever = st.session_state.paper_retriever
        elif "youtube_retriever" in st.session_state:
            st.warning("Only youtube retriever is available.")
            st.session_state.retriever = st.session_state.youtube_retriever
        else:
            st.warning("No retriever is available.")

        llm = ChatOpenAI(model="gpt-4o")
        qa_prompt_template = """
        You are an expert in summarizing and explaining complex information. Use the provided information from both academic papers and video reviews to answer the user's question comprehensively. Ensure that your answer is clear, concise, and based on the retrieved documents.

        Provided Information:
        {context}

        Question:
        {question}

        Answer:
        """
        qa_prompt = PromptTemplate(
            template=qa_prompt_template, input_variables=["context", "question"]
        )
        if st.session_state.retriever is not None:
            self.rag_chain = (
                {
                    "context": st.session_state.retriever | self.format_docs,
                    "question": RunnablePassthrough(),
                }
                | qa_prompt
                | llm
            )

        q_ = st.chat_input("질문을 입력하세요: ")
        if q_:
            self.answer_question(q_)


if __name__ == "__main__":
    page = ReviewPage()
    page.setup()

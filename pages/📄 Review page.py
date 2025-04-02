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
import time


class ReviewPage:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=250,
            chunk_overlap=50,
            length_function=len,
            is_separator_regex=False,
        )
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

        # 세션 상태 변수 초기화
        if "retriever" not in st.session_state:
            st.session_state.retriever = None
        if "paper_retriever" not in st.session_state:
            st.session_state.paper_retriever = None
        if "youtube_retriever" not in st.session_state:
            st.session_state.youtube_retriever = None

    def load_markdown(self, title):
        if os.path.exists(f"./data/review_markdown/{title}.md"):
            with open(f"./data/review_markdown/{title}.md", "r") as f:
                return f.read()
        else:
            return f"## {title} Review\n\n"

    def save_markdown(self, md, title):
        # 디렉토리가 없으면 생성
        os.makedirs("./data/review_markdown", exist_ok=True)
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
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            status_text.text("논문을 불러오는 중...")
            progress_bar.progress(10)

            arxiv_loader = ArxivLoader(arxiv_id)
            docs = arxiv_loader.load()

            status_text.text("논문을 분석하는 중...")
            progress_bar.progress(30)

            # 디렉토리가 없으면 생성
            os.makedirs("./data/vector_db", exist_ok=True)
            db_file_name = f"./data/vector_db/{arxiv_id}_paper_pdf"

            status_text.text("벡터 데이터베이스를 생성하는 중...")
            progress_bar.progress(60)

            retriever = self.create_vector_db(db_file_name, docs)

            status_text.text("완료되었습니다!")
            progress_bar.progress(100)
            time.sleep(0.5)  # 잠시 완료 메시지 표시

            progress_bar.empty()
            status_text.empty()

            return retriever
        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"RAG 생성 중 오류가 발생했습니다: {str(e)}")
            return None

    def create_youtube_vector_db(self, db_file_name_youtube, docs, video_name):
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            status_text.text("YouTube 스크립트를 분석하는 중...")
            progress_bar.progress(30)

            # 디렉토리가 없으면 생성
            os.makedirs(os.path.dirname(db_file_name_youtube), exist_ok=True)

            status_text.text("벡터 데이터베이스를 생성하는 중...")
            progress_bar.progress(60)

            youtube_retriever = self.create_vector_db(db_file_name_youtube, docs)

            status_text.text("완료되었습니다!")
            progress_bar.progress(100)
            time.sleep(0.5)  # 잠시 완료 메시지 표시

            progress_bar.empty()
            status_text.empty()

            st.session_state.youtube_retriever = youtube_retriever
            st.success(f"{video_name} 스크립트의 RAG가 생성되었습니다.")
            st.experimental_rerun()  # 페이지를 새로고침하여 버튼 상태 업데이트

            return youtube_retriever
        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"YouTube RAG 생성 중 오류가 발생했습니다: {str(e)}")
            return None

    def answer_question(self, question):
        language = st.session_state.language
        result = self.rag_chain.invoke(question)
        with st.container(border=True):
            st.markdown(f"**질문**: {question}")
            st.markdown(f"**답변 ({language})**: {result.content}")

    def format_docs(self, docs):
        return "\n\n".join(doc.page_content for doc in docs)

    def setup(self):
        st.set_page_config(
            page_title="Review Paper",
            page_icon="📄",
        )

        if "paper_data" not in st.session_state or st.session_state.paper_data is None:
            st.error("논문 데이터가 없습니다. 홈페이지에서 논문을 선택해주세요.")
            st.stop()

        df = st.session_state.paper_data["df"]
        paper_title = df["Title"].values[0]
        abstract = df["Summary"].values[0]
        arxiv_id = df["arxiv_id"].values[0]

        # 언어 선택 (기본값은 한국어)
        if "language" not in st.session_state:
            st.session_state.language = "한국어"

        st.markdown(f"# {paper_title}")

        # 상단 설정 섹션
        with st.container(border=True):
            col_settings = st.columns([1, 1])
            with col_settings[0]:
                selected_language = st.selectbox(
                    "응답 언어",
                    ["한국어", "English", "日本語", "中文"],
                    index=["한국어", "English", "日本語", "中文"].index(
                        st.session_state.language
                    ),
                )
                st.session_state.language = selected_language

            with col_settings[1]:
                # 언어 코드 매핑
                language_code_map = {
                    "한국어": "ko",
                    "English": "en",
                    "日本語": "ja",
                    "中文": "zh",
                }
                language_code = language_code_map[selected_language]

        # 1. 질문 기능을 상단에 배치
        llm = ChatOpenAI(model="gpt-4o")
        qa_prompt_template = """
        You are an expert in summarizing and explaining complex information. Use the provided information from both academic papers and video reviews to answer the user's question comprehensively. Ensure that your answer is clear, concise, and based on the retrieved documents.
        
        IMPORTANT: You must respond in {language}.

        Provided Information:
        {context}

        Question:
        {question}

        Answer (in {language}):
        """
        qa_prompt = PromptTemplate(
            template=qa_prompt_template,
            input_variables=["context", "question", "language"],
        )

        # RAG 버튼을 상단에 배치
        col_rag1, col_rag2 = st.columns([1, 1])

        # Paper RAG 버튼은 이미 생성된 경우 표시하지 않음
        paper_rag_exists = (
            "paper_retriever" in st.session_state
            and st.session_state.paper_retriever is not None
        )

        if not paper_rag_exists:
            with col_rag1:
                if st.button("Paper RAG 생성", use_container_width=True):
                    with st.spinner("RAG를 생성하는 중..."):
                        retriever = self.create_arxiv_vector_db(arxiv_id)
                        if retriever:
                            st.session_state.paper_retriever = retriever
                            st.success("Paper RAG가 생성되었습니다.")
                            st.experimental_rerun()  # 페이지를 새로고침하여 버튼 상태 업데이트
        else:
            with col_rag1:
                st.success("Paper RAG가 이미 생성되었습니다.")

        # RAG 상태 표시
        if (
            "paper_retriever" in st.session_state
            and "youtube_retriever" in st.session_state
            and st.session_state.paper_retriever is not None
            and st.session_state.youtube_retriever is not None
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
        elif (
            "paper_retriever" in st.session_state
            and st.session_state.paper_retriever is not None
        ):
            st.info("Paper retriever가 활성화되었습니다.")
            st.session_state.retriever = st.session_state.paper_retriever
        elif (
            "youtube_retriever" in st.session_state
            and st.session_state.youtube_retriever is not None
        ):
            st.info("Youtube retriever가 활성화되었습니다.")
            st.session_state.retriever = st.session_state.youtube_retriever
        else:
            st.session_state.retriever = None
            st.warning("아직 활성화된 retriever가 없습니다. RAG를 생성해주세요.")

        if st.session_state.retriever is not None:
            try:
                self.rag_chain = (
                    {
                        "context": st.session_state.retriever | self.format_docs,
                        "question": RunnablePassthrough(),
                        "language": lambda _: language_code,
                    }
                    | qa_prompt
                    | llm
                )

                st.markdown("## 질문하기")
                q_ = st.chat_input("논문에 대해 질문해보세요:")
                if q_:
                    with st.spinner(f"{selected_language}로 답변을 생성하는 중..."):
                        self.answer_question(q_)
            except Exception as e:
                st.error(f"RAG 체인 생성 중 오류가 발생했습니다: {str(e)}")
                st.session_state.retriever = None

        # 2. 리뷰 작성 부분
        st.markdown("## 리뷰 작성")
        col_1, col_2 = st.columns([1, 1], gap="large")

        with col_1:
            md = self.load_markdown(paper_title)
            md = st.text_area("Review를 위한 Markdown을 입력하세요: ", md, height=500)

            if st.button("Markdown 저장"):
                self.save_markdown(md, paper_title)
                st.success("Markdown이 저장되었습니다.")

        with col_2:
            st.write(md)

        # 3. YouTube 스크립트 섹션
        youtube_trans_list = glob(
            f"./data/youtube_audio/{arxiv_id}/{paper_title}/*json"
        )

        if youtube_trans_list:
            st.markdown("## YouTube 스크립트")
            with st.container(border=True):
                for i, trans_path in enumerate(youtube_trans_list):
                    try:
                        docs = load_docs_from_jsonl(trans_path)
                        trans = "".join([doc.page_content for doc in docs])
                        video_name = trans_path.split("/")[-2]
                        st.expander(video_name, expanded=False).markdown(trans)

                        # 이미 YouTube RAG가 생성되었는지 확인
                        db_file_name_youtube = (
                            f"./data/vector_db/{video_name}_youtube_trans"
                        )
                        youtube_rag_exists = (
                            "youtube_retriever" in st.session_state
                            and st.session_state.youtube_retriever is not None
                            and os.path.exists(db_file_name_youtube)
                        )

                        docs = self.text_splitter.split_documents(docs)

                        if not youtube_rag_exists:
                            st.button(
                                "YouTube RAG 생성",
                                on_click=self.create_youtube_vector_db,
                                args=(db_file_name_youtube, docs, video_name),
                                key=f"youtube_rag_{i}",
                            )
                        else:
                            st.success(f"{video_name} RAG가 이미 생성되었습니다.")
                    except Exception as e:
                        st.error(f"스크립트 로딩 중 오류가 발생했습니다: {str(e)}")


if __name__ == "__main__":
    page = ReviewPage()
    page.setup()

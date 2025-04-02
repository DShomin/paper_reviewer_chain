import streamlit as st
import os
from src.youtube_search import search_youtube
from src.utils import save_docs_to_jsonl, load_docs_from_jsonl
from dotenv import load_dotenv


from langchain.document_loaders.generic import GenericLoader
from langchain.document_loaders.parsers.audio import OpenAIWhisperParser
from langchain.document_loaders import YoutubeLoader
from langchain_community.document_loaders import YoutubeAudioLoader
from datetime import datetime, timezone


def time_since(published_at):
    # Parse the published_at string into a datetime object
    published_at = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")
    published_at = published_at.replace(tzinfo=timezone.utc)

    # Get the current time in UTC
    now = datetime.now(timezone.utc)

    # Calculate the difference
    diff = now - published_at

    # Determine the time unit
    seconds = diff.total_seconds()
    if seconds < 60:
        return f"{int(seconds)} seconds ago"
    elif seconds < 3600:
        return f"{int(seconds // 60)} minutes ago"
    elif seconds < 86400:
        return f"{int(seconds // 3600)} hours ago"
    elif seconds < 604800:
        return f"{int(seconds // 86400)} days ago"
    elif seconds < 2419200:
        return f"{int(seconds // 604800)} weeks ago"
    elif seconds < 29030400:
        return f"{int(seconds // 2419200)} months ago"
    else:
        return f"{int(seconds // 29030400)} years ago"


def view_count(view_count):
    view_count = int(view_count)
    if view_count < 1000:
        return view_count
    elif view_count < 1000000:
        return f"{view_count // 1000}K views"
    else:
        return f"{view_count // 1000000}M views"


load_dotenv()


st.set_page_config(
    page_title="YouTube Search",
    page_icon="🔍",
)

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")


st.markdown("# YouTube Search")

# get queyy from user
query = st.text_input(
    "유튜브를 통해 검색할 검색어를 입력하세요:",
    value=(
        st.session_state.paper_data["title"]
        if st.session_state.paper_data is not None
        else ""
    ),
)

if query:
    results = search_youtube(query, YOUTUBE_API_KEY)
    with st.container(border=True):
        for i, video in enumerate(results):
            with st.container(border=True):
                YOUTUBE_AUDIO_SAVE_DIR = f"./data/youtube_audio/{st.session_state.paper_data['arxiv_id']}/{video['title']}"

                st.image(video["thumbnail_url"], use_column_width=True)
                st.markdown(f"## {video['title']}")
                st.markdown(
                    f"Views: {view_count(video['view_count'])} | Likes: {video['like_count']} | Comments: {video['comment_count']}"
                )
                st.markdown(f"Published at: {time_since(video['published_at'])}")
                st.link_button("Watch on YouTube", video["url"])
                WHISPER_SCRIPT_DIR = YOUTUBE_AUDIO_SAVE_DIR + "/whisper_script.json"
                YOUTUBE_SCRIPT_DIR = YOUTUBE_AUDIO_SAVE_DIR + "/script.json"

                if os.path.exists(WHISPER_SCRIPT_DIR):
                    docs = load_docs_from_jsonl(WHISPER_SCRIPT_DIR)
                    transript = "".join([doc.page_content for doc in docs])
                    st.expander("Whisper transcipt", expanded=True).markdown(transript)
                elif os.path.exists(YOUTUBE_SCRIPT_DIR):
                    docs = load_docs_from_jsonl(YOUTUBE_SCRIPT_DIR)
                    transript = "".join([doc.page_content for doc in docs])
                    st.expander("Youtube transript", expanded=True).markdown(transript)
                else:
                    col = st.columns([1, 2])

                    target_lang = col[0].selectbox(
                        "Select Language",
                        [None, "en", "ko", "ja", "zh"],
                        key=f"t_lang_{i}",
                    )
                    whisper_trans_button = col[1].button(
                        "Get Whisper Transcript", key=f"whisper_{i}"
                    )

                    if whisper_trans_button:
                        SCRIPT_PATH = WHISPER_SCRIPT_DIR
                        loader = GenericLoader(
                            YoutubeAudioLoader(
                                urls=[video["url"]], save_dir=YOUTUBE_AUDIO_SAVE_DIR
                            ),
                            OpenAIWhisperParser(
                                response_format="json", language=target_lang
                            ),
                        )
                        docs = loader.load()
                        transript = "".join([doc.page_content for doc in docs])
                        st.expander("Whisper transript", expanded=False).markdown(
                            transript
                        )
                        save_docs_to_jsonl(docs, SCRIPT_PATH)

                    youtube_trans_button = st.button(
                        "Get Youtube Transcript", key=f"youtube_{i}"
                    )
                    if youtube_trans_button:
                        SCRIPT_PATH = YOUTUBE_SCRIPT_DIR
                        loader = YoutubeLoader.from_youtube_url(video["url"])
                        docs = loader.load()
                        transript = "".join([doc.page_content for doc in docs])
                        st.expander("Youtube transript", expanded=False).markdown(
                            transript
                        )
                        save_docs_to_jsonl(docs, SCRIPT_PATH)

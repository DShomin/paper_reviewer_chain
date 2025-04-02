from langchain_community.document_transformers import DoctranTextTranslator  # type: ignore
from langchain.schema.document import Document
import dotenv

dotenv.load_dotenv()


def translate(text, target_language="ko"):
    translator = DoctranTextTranslator(
        language=target_language, openai_api_model="gpt-3.5-turbo"
    )
    text = Document(page_content=text)
    translated_document = translator.transform_documents([text])

    return translated_document[0].page_content

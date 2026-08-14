import logging 

from langchain_core.documents import Document as LCDocument
from langchain_text_splitters import Language, RecursiveCharacterTextSplitter

from src.chunking.config import get_chunking_config

logger = logging.getLogger(__name__)

EXTENSION_TO_LANGUAGE = {
    ".py": Language.PYTHON,
    ".js": Language.JS,
    ".ts": Language.TS,
    ".java": Language.JAVA,
    ".go": Language.GO,
}

_encoding = None
_tiktoken_unavailable = False

def count_tokens(text: str) -> int:
    global _encoding, _tiktoken_unavailable

    if _tiktoken_unavailable:
        return max(1, len(text) // 4)
    if _encoding is None:
        try:
            import tiktoken

            _encoding = tiktoken.get_encoding("cl100k_base")
        except Exception as exc:
            logger.warning("tiktoken unavailable (%s); using character-based fallback.", exc)
            _tiktoken_unavailable = True
            return max(1, len(text) // 4)

    return len(_encoding.encode(text))

def _build_splitter(
        chunk_size: int, chunk_overlap: int, language: Language | None
) -> RecursiveCharacterTextSplitter:
    if language is not None:
        return RecursiveCharacterTextSplitter.from_language(
            language=language,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=count_tokens,
        )
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=count_tokens,
    )

def chunk_document(
        langchain_docs: list[LCDocument],
        file_extensions: str | None = None
) -> list[dict]:
    config = get_chunking_config()
    language = EXTENSION_TO_LANGUAGE.get(file_extensions) if file_extensions else None

    parent_splitter = _build_splitter(
        config.parent_chunk_size, config.parent_chunk_overlap, language
    )
    child_splitter = _build_splitter(
        config.child_chunk_size, config.child_chunk_overlap, language
    )

    full_text = "\n\n".join(doc.page_content for doc in langchain_docs)
    base_metadata = dict(langchain_docs[0].metadata) if langchain_docs else {}

    parent_texts = parent_splitter.split_text(full_text)

    result: list[dict] = []
    for parent_index, parent_text in enumerate(parent_texts):
        result.append(
            {
                "content": parent_text,
                "chunk_level": "parent",
                "token_count": count_tokens(parent_text),
                "chunk_index": parent_index,
                "parent_index": None,
                "extra_metadata": base_metadata,
            }
        )

        child_texts = child_splitter.split_text(parent_text)
        for child_index, child_text in enumerate(child_texts):
            result.append(
                {
                    "content": child_text,
                    "chunk_level": "child",
                    "token_count": count_tokens(child_text),
                    "chunk_index": child_index,
                    "parent_index": parent_index,
                    "extra_metadata": base_metadata,
                }
            )
    return result

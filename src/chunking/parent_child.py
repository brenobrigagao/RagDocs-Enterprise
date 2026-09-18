import logging 
from functools import lru_cache
from pathlib import Path
import uuid

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

@lru_cache(maxsize=1)
def _get_tiktoken_encoding():
    try:
        import tiktoken
        return tiktoken.get_encoding("cl100k_base")
    except Exception as exc:
        logger.warning("tiktoken unavailable (%s); using character-based fallback.", exc)
        return None

def count_tokens(text: str) -> int:
    encoding = _get_tiktoken_encoding()
    if encoding is None:
        return max(1, len(text) // 4)
    return len(encoding.encode(text))

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

def _extract_extension(file_extension: str | None, doc_metadata: dict) -> str | None:
    if file_extension:
        ext = file_extension.lower()
        return ext if ext.endswith(".") else f".{ext}"

    file_name = doc_metadata.get("file_name") or doc_metadata.get("source_path")
    if file_name:
        return Path(file_name).suffix.lower()
    return None

def chunk_document(
        langchain_docs: list[LCDocument],
        file_extension: str | None = None
) -> list[dict]:
    config = get_chunking_config()
    result: list[dict] = []

    for doc in langchain_docs:
        doc_metadata = dict(doc.metadata)

        effective_ext = _extract_extension(file_extension, doc_metadata)
        language = EXTENSION_TO_LANGUAGE.get(effective_ext) if effective_ext else None

        parent_splitter = _build_splitter(
            config.parent_chunk_size, config.parent_chunk_overlap, language
        )
        child_splitter = _build_splitter(
            config.child_chunk_size, config.child_chunk_overlap, language
        )
        parent_texts = parent_splitter.split_text(doc.page_content)

        for parent_text in parent_texts:
            parent_id = str(uuid.uuid4())
            parent_tokens = count_tokens(parent_text)

            result.append(
                {
                    "chunk_id": parent_id,
                    "content": parent_text,
                    "chunk_level": "parent",
                    "token_count": parent_tokens,
                    "parent_id": None,
                    "extra_metadata": doc_metadata,
                }
            )

            child_texts = child_splitter.split_text(parent_text)
            for child_index, child_text in enumerate(child_texts):
                result.append(
                    {
                        "chunk_id": str(uuid.uuid4()),
                        "content": child_text,
                        "chunk_level": "child",
                        "token_count": count_tokens(child_text),
                        "chunk_index": child_index,
                        "parent_id": parent_id,
                        "extra_metadata": doc_metadata,
                    }
                )
                            
    return result

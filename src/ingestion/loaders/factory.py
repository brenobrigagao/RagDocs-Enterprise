from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.documents import Document as LCDocument

CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".java", ".go", ".rb", ".rs",
    ".c", ".cpp", ".cs", ".php", ".jsx", ".tsx",
}

class UnsupportedFileTypeError(ValueError):
    pass

def detect_source_type(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".pdf":
        return "pdf"
    if ext == ".md":
        return "markdown"
    if ext == ".txt":
        return "text"
    if ext in CODE_EXTENSIONS:
        return "code"
    raise UnsupportedFileTypeError(f"Unsupported extension: {ext}")

def load_file(file_path: str | Path) -> list[LCDocument]:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    source_type = detect_source_type(path)

    if source_type == "pdf":
        loader = PyPDFLoader(str(path))
    else:
        loader = TextLoader(str(path), encoding="utf-8")

    documents = loader.load()

    for doc in documents:
        doc.metadata["source_type"] = source_type
        doc.metadata["file_name"] = path.name
        doc.metadata["source_path"] = str(path.resolve())

    return documents
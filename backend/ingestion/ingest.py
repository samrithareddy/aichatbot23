"""Build a local FAISS index from product documentation.

Usage:
    python -m backend.ingestion.ingest --data-dir data --output-dir faiss_index
"""

from __future__ import annotations

import argparse
from pathlib import Path


def build_index(data_dir: Path, output_dir: Path) -> None:
    try:
        from langchain_community.document_loaders import DirectoryLoader
        from langchain_community.vectorstores import FAISS
        from langchain_openai import OpenAIEmbeddings
        from langchain_text_splitters import RecursiveCharacterTextSplitter
    except ImportError as exc:
        raise RuntimeError(
            "Install ingestion dependencies from requirements.txt before building the FAISS index."
        ) from exc

    loaders = [
        DirectoryLoader(str(data_dir), glob="**/*.md", show_progress=True),
        DirectoryLoader(str(data_dir), glob="**/*.html", show_progress=True),
        DirectoryLoader(str(data_dir), glob="**/*.pdf", show_progress=True),
    ]
    documents = []
    for loader in loaders:
        documents.extend(loader.load())

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(documents)
    embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local(str(output_dir))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build FAISS product documentation index.")
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--output-dir", type=Path, default=Path("faiss_index"))
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    build_index(args.data_dir, args.output_dir)

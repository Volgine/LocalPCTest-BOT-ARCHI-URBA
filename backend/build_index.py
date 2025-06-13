import os
import sys
from pathlib import Path
from typing import List

from langchain.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS


def load_documents(folder: Path) -> List[str]:
    """Load all .txt files from the folder."""
    docs = []
    for file in folder.rglob('*.txt'):
        loader = TextLoader(str(file), encoding='utf-8')
        docs.extend(loader.load())
    return docs


def main():
    if len(sys.argv) < 3:
        print('Usage: python build_index.py <docs_folder> <index_path>')
        sys.exit(1)

    docs_folder = Path(sys.argv[1])
    index_path = Path(sys.argv[2])

    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print('OPENAI_API_KEY not set in environment')
        sys.exit(1)

    raw_docs = load_documents(docs_folder)
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    docs = splitter.split_documents(raw_docs)

    embeddings = OpenAIEmbeddings(openai_api_key=api_key)
    vector_store = FAISS.from_documents(docs, embeddings)

    index_path.parent.mkdir(parents=True, exist_ok=True)
    vector_store.save_local(str(index_path))
    print(f'Index saved to {index_path}')


if __name__ == '__main__':
    main()
